# Build a complete application

<section class="chapter-context" markdown="1">

## Connect a visible user action to stored state

A shared reading list ties these chapters together. Someone saves a URL, reads the list, or edits a title while other requests are in flight. The browser, API, database, and permission boundary must agree about what that action means.

The local HTTP/SQLite starter and the separate seeded browser editor give you real code to inspect. They are deliberately small and have different route contracts. Each lesson says which one it uses and what you still need to build.

</section>

[Full learning sequence](../README.md)

| Order | Chapter | You will learn to… |
|---|---|---|
| CH 04 | [Build HTTP APIs and reliable background work](01-backend/README.md) | Trace a request, define its contract, and coordinate bounded work. |
| CH 05 | [Model data and enforce transactional rules](02-databases/README.md) | Model authoritative data, explain a query plan, and protect concurrent writes. |
| CH 06 | [Connect a usable interface to an API](03-frontend/README.md) | Preserve user intent across browser, API, and persisted state. |
| CH 07 | [Find defects and evaluate engineering evidence](04-testing/README.md) | Reproduce a defect, build a check that catches it, and assess a proposed repair. |
| CH 08 | [Enforce identity, ownership and tenant boundaries](05-security/README.md) | Enforce identity, ownership, and trust boundaries beyond the interface. |

Study the core material in order. Each lesson keeps its own deeper follow-ups, runnable references and project practice. Difficulty is a property of a question, not a separate directory or curriculum.

Next group: [Design, ship, and operate the application](../03-production/README.md).
