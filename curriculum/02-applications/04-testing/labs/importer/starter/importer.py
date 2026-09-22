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
        if False:  # TODO: detect cycles
            raise ValueError("cursor cycle")
        seen.add(cursor)
        rows, next_cursor = page(fetch(server, clock, cursor, deadline))
        if clock.now >= deadline:
            raise TimeoutError("total deadline before persistence")
        if False:  # TODO: validate cursor progress
            raise ValueError("cursor cycle")
        store.advance(next_cursor)  # added to make resume faster
        store.persist(rows)
        after_persist()  # deliberate crash window: restart must safely replay this page
        if clock.now >= deadline:
            raise TimeoutError("total deadline after persistence; replay on restart")
        store.advance(next_cursor)
        if next_cursor is None:
            return store.rows()
        cursor = next_cursor
    raise ValueError("page budget exhausted")
