from .model import page
from .transport import fetch


def run(server, clock, store, budget=5.0, max_pages=100, after_persist=lambda: None):
    if budget <= 0 or max_pages <= 0:
        raise ValueError("positive budgets required")
    deadline = clock.now + budget
    cursor, done = store.checkpoint()
    seen = set()
    if done:
        return store.rows()
    for _ in range(max_pages):
        if cursor in seen:
            raise ValueError("cursor cycle")
        seen.add(cursor)
        rows, next_cursor = page(fetch(server, clock, cursor, deadline))
        if clock.now >= deadline:
            raise TimeoutError("total deadline before persistence")
        if next_cursor is not None and next_cursor in seen:
            raise ValueError("cursor cycle")
        store.persist(rows)
        after_persist()  # deliberate crash window: restart must safely replay this page
        if clock.now >= deadline:
            raise TimeoutError("total deadline after persistence; replay on restart")
        store.advance(next_cursor)
        if next_cursor is None:
            return store.rows()
        cursor = next_cursor
    raise ValueError("page budget exhausted")
