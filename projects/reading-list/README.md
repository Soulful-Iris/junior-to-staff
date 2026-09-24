# Build and evolve a shared reading-list application

Alice and Bob belong to a study group. They save documentation links, browse shared notes and keep separate reading progress. Over five stages, you turn that small application into a deployed, recoverable service, add background work and an optional AI feature, then migrate its data while users keep working.

## Start with a real application

The repository includes a [runnable HTTP API and step-by-step setup](../../examples/reading-list-starter/README.md). It already saves data to SQLite and supports list, note edit and per-member reading state. Run it and send the supplied requests before starting Stage 1. You will add the browser UI and production identity; later stages add operations, queues, AI suggestions and migration.

Each stage also links a small Python mechanism demonstration. Those demonstrations isolate one concept; they are not completed stage implementations. Continue your own application between stages. The AWS diagrams show the target deployment and each stage explains the adapters you still need to write.

## Follow the stages in order

| Stage | Assignment | Added responsibility |
|---|---|---|
| 1 | [Stage 1: Build the shared reading-list application](stages/01-it-works/README.md) | A persisted, authorized full-stack feature |
| 2 | [Stage 2: Deploy, back up and recover the reading list](stages/02-it-survives/README.md) | Delivery, recovery and operational evidence |
| 3 | [Stage 3: Add durable jobs and bounded caching](stages/03-under-load/README.md) | Queues, caches, load and duplicate handling |
| 4 | [Stage 4: Add optional AI tag suggestions](stages/04-it-reasons/README.md) | An AI feature with evaluation and budgets |
| 5 | [Stage 5: Migrate the reading list to stable tag IDs](stages/05-it-changes/README.md) | Compatibility, migration, rollback and retirement |

The stages depend on their predecessors. Use the [curriculum](../../curriculum/README.md) for concepts and return here to apply them to the same system. Prefer a smaller independent exercise? Use the [subject project index](../../indexes/projects.md).
