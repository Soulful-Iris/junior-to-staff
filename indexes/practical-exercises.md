# Practical coding · choose one unfamiliar system

> “You inherit a feature with passing happy-path checks and failing customer behavior.
> Make the contract visible, reproduce one failure, and repair the responsible boundary.”

Each linked page is a separate constructed project/session with concrete inputs,
a reusable method, evolving diagrams and checks.

| Order | Project | Property demonstrated |
|---|---|---|
| 1 | [Bounded API fan-out](../curriculum/02-applications/01-backend/labs/fan-out/README.md) | Ordered partial results and at most K active asynchronous calls |
| 2 | [Search results race](../curriculum/02-applications/03-frontend/labs/search-race/README.md) | Latest request wins even when cancellation is ignored |
| 3 | [Quantity investigation](../curriculum/02-applications/04-testing/labs/quantity-debug/README.md) | Runtime validation and regression before repair |
| 4 | [Transaction importer](../curriculum/02-applications/04-testing/labs/importer/README.md) | Multi-module debugging, exact money, retries and durable restart |
| 5 | [Three-PR review](../curriculum/02-applications/04-testing/labs/importer/review/README.md) | Causal reproductions and release priorities |
| Backend/infra | [Bounded threaded executor](../curriculum/02-applications/01-backend/labs/bounded-executor/README.md) | Condition predicates, cancellation, deadlines and shutdown |
| Product | [Real bookmark editor](../curriculum/02-applications/03-frontend/labs/bookmark-editor/README.md) | Browser/API/SQLite behavior under races and conflicts |

Prerequisites: [coding route](../curriculum/01-code/02-data-structures-algorithms/practice-sequence.md), [runtime model](../curriculum/02-applications/01-backend/labs/bounded-executor/runtime.md).
Existing [TypeScript helpers](../curriculum/01-code/02-data-structures-algorithms/typescript.ts) and [tests](../curriculum/01-code/02-data-structures-algorithms/typescript.test.ts) remain
available. The importer starter deliberately fails before repair; its reference is
separate. The executor and bookmark slice are runnable references: use their
[candidate briefs](../practice/README.md) for independent attempts.

For AI-assisted review, first write the invariant and three adversarial cases; then
ask an assistant to implement fan-out, inspect every await, and record accepted and
rejected suggestions. Finish a changed version unaided. AI review and independent
implementation are distinct skills; recruiter instructions govern a real interview.

Do not call green reference tests a candidate pass. Complete the
[assessment route](../practice/README.md) on more than one unfamiliar occasion.
[Timed mock](../practice/coding-mock.md) · [Coding home](../curriculum/01-code/02-data-structures-algorithms/practice-sequence.md)
