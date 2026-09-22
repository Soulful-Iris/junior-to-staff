"""Execute real two-session PostgreSQL schedules. Requires psycopg and LAB_PG_DSN."""
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from retry import transaction_retry


def main():
    import psycopg
    dsn = os.environ["LAB_PG_DSN"]
    def connect():
        connection = psycopg.connect(dsn, autocommit=True)
        connection.execute("SET search_path=interview_lab")
        connection.execute("SET statement_timeout='8s'")
        connection.execute("SET lock_timeout='6s'")
        return connection

    with connect() as admin:
        admin.execute(Path(__file__).with_name("schema.sql").read_text())
        with connect() as a, connect() as b:
            # Lost update: both application reads see 1, then write the literal 0.
            a.execute("BEGIN")
            b.execute("BEGIN")
            assert a.execute("SELECT available FROM stock WHERE id=1").fetchone()[0] == 1
            assert b.execute("SELECT available FROM stock WHERE id=1").fetchone()[0] == 1
            for conn, buyer in ((a, "a"), (b, "b")):
                conn.execute("UPDATE stock SET available=0 WHERE id=1")
                conn.execute("INSERT INTO reservations VALUES (%s,1)", (buyer,))
                conn.execute("COMMIT")
            assert admin.execute("SELECT count(*) FROM reservations").fetchone()[0] == 2
            print("FAILURE reproduced: stock=0, reservations=2 for initial stock=1")
            admin.execute("TRUNCATE reservations")
            admin.execute("UPDATE stock SET available=1")
            a.execute("BEGIN")
            b.execute("BEGIN")
            assert a.execute("UPDATE stock SET available=available-1 WHERE id=1 AND available>0 RETURNING id").fetchone() == (1,)
            a.execute("INSERT INTO reservations VALUES ('a',1)")
            with ThreadPoolExecutor(max_workers=1) as pool:
                waiting = pool.submit(b.execute, "UPDATE stock SET available=available-1 WHERE id=1 AND available>0 RETURNING id")
                a.execute("COMMIT")
                assert waiting.result().fetchone() is None
            b.execute("COMMIT")
            assert admin.execute("SELECT count(*) FROM reservations").fetchone()[0] == 1
            assert admin.execute("SELECT available FROM stock WHERE id=1").fetchone()[0] == 0
            print("FIX passed: conditional decrement admits one reservation")

            # Write skew under snapshot isolation: disjoint writes evade row conflict.
            for conn in (a, b):
                conn.execute("BEGIN ISOLATION LEVEL REPEATABLE READ")
                assert conn.execute("SELECT count(*) FROM doctors WHERE on_call").fetchone()[0] == 2
            a.execute("UPDATE doctors SET on_call=false WHERE id=1")
            b.execute("UPDATE doctors SET on_call=false WHERE id=2")
            a.execute("COMMIT")
            b.execute("COMMIT")
            assert admin.execute("SELECT count(*) FROM doctors WHERE on_call").fetchone()[0] == 0
            print("FAILURE reproduced: repeatable-read write skew leaves zero doctors")
            admin.execute("UPDATE doctors SET on_call=true")
            for conn in (a, b):
                conn.execute("BEGIN ISOLATION LEVEL SERIALIZABLE")
                assert conn.execute("SELECT count(*) FROM doctors WHERE on_call").fetchone()[0] == 2
            a.execute("UPDATE doctors SET on_call=false WHERE id=1")
            b.execute("UPDATE doctors SET on_call=false WHERE id=2")
            failures = []
            for conn, doctor in ((a, 1), (b, 2)):
                try:
                    conn.execute("COMMIT")
                except psycopg.Error as error:
                    conn.execute("ROLLBACK")
                    assert error.sqlstate == "40001", error
                    failures.append(doctor)
            assert len(failures) == 1
            def retry_off_call():
                with connect() as conn:
                    try:
                        conn.execute("BEGIN ISOLATION LEVEL SERIALIZABLE")
                        count = conn.execute("SELECT count(*) FROM doctors WHERE on_call").fetchone()[0]
                        if count > 1:
                            conn.execute("UPDATE doctors SET on_call=false WHERE id=%s", (failures[0],))
                        conn.execute("COMMIT")
                        return count
                    except Exception:
                        conn.execute("ROLLBACK")
                        raise
            assert transaction_retry(retry_off_call) == 1
            assert admin.execute("SELECT count(*) FROM doctors WHERE on_call").fetchone()[0] == 1
            print("FIX passed: serialization abort plus complete transaction retry preserves one doctor")

            # Deadlock: opposite lock order. Victim rolls back before retry.
            a.execute("BEGIN")
            b.execute("BEGIN")
            a.execute("UPDATE counters SET hits=hits+1 WHERE id=1")
            b.execute("UPDATE counters SET hits=hits+1 WHERE id=2")
            def finish(conn, second_id):
                try:
                    conn.execute("UPDATE counters SET hits=hits+1 WHERE id=%s", (second_id,))
                    conn.execute("COMMIT")
                    return "ok"
                except psycopg.Error as error:
                    conn.execute("ROLLBACK")
                    return error.sqlstate
            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(finish, a, 2)
                second = pool.submit(finish, b, 1)
                outcomes = sorted((first.result(), second.result()))
            assert outcomes == ["40P01", "ok"], outcomes
            assert admin.execute("SELECT hits FROM counters ORDER BY id").fetchall() == [(1,), (1,)]
            print("FAILURE reproduced: deadlock 40P01; victim transaction rolled back")

            def ordered_transaction():
                with connect() as conn:
                    try:
                        conn.execute("BEGIN")
                        conn.execute("SELECT id FROM counters ORDER BY id FOR UPDATE").fetchall()
                        conn.execute("UPDATE counters SET hits=hits+1")
                        conn.execute("COMMIT")
                    except Exception:
                        conn.execute("ROLLBACK")
                        raise
            transaction_retry(ordered_transaction)
            assert admin.execute("SELECT hits FROM counters ORDER BY id").fetchall() == [(2,), (2,)]
            admin.execute("UPDATE counters SET hits=0")
            with ThreadPoolExecutor(max_workers=2) as pool:
                one = pool.submit(transaction_retry, ordered_transaction)
                two = pool.submit(transaction_retry, ordered_transaction)
                one.result()
                two.result()
            assert admin.execute("SELECT hits FROM counters ORDER BY id").fetchall() == [(2,), (2,)]
            print("FIX passed: ordered locks plus bounded whole-transaction retry")


if __name__ == "__main__":
    main()
