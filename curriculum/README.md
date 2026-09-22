# The learning sequence

One curriculum organized by engineering subjects and prerequisites. Start with problem solving and core code, build an application, design and operate it, then study scale and evolution. Every lesson contains its existing deeper questions.

## Write correct code

| Chapter | What you learn |
|---|---|
| [Problem solving and AI-assisted engineering](01-code/01-problem-solving/README.md) | Clarify a requirement, make a bounded change, and verify the result. |
| [Data structures and algorithms](01-code/02-data-structures-algorithms/README.md) | Choose a representation, explain its invariant, and test time and space bounds. |

## Build a complete application

| Chapter | What you learn |
|---|---|
| [Backend and APIs](02-applications/01-backend/README.md) | Trace a request, define its contract, and coordinate bounded work. |
| [Databases and transactions](02-applications/02-databases/README.md) | Model authoritative data, explain a query plan, and protect concurrent writes. |
| [Frontend and full-stack integration](02-applications/03-frontend/README.md) | Preserve user intent across browser, API, and persisted state. |
| [Testing, debugging, and code review](02-applications/04-testing/README.md) | Reproduce a defect, build a check that catches it, and assess a proposed repair. |
| [Security](02-applications/05-security/README.md) | Enforce identity, ownership, and trust boundaries beyond the interface. |

## Design, ship, and operate the application

| Chapter | What you learn |
|---|---|
| [System design](03-production/01-system-design/README.md) | Turn requirements and workload estimates into an explainable architecture. |
| [CI/CD and progressive delivery](03-production/02-delivery/README.md) | Build once, verify compatibility, and release a change with stop conditions. |
| [Infrastructure as code and AWS](03-production/03-infrastructure/README.md) | Map a mechanism to explicit infrastructure, permissions, and operational limits. |
| [Observability](03-production/04-observability/README.md) | Use logs, metrics, and traces to answer a concrete system question. |
| [Reliability and incident response](03-production/05-reliability/README.md) | Budget failures, bound overload, and recover from evidence. |

## Scale and evolve the system

| Chapter | What you learn |
|---|---|
| [Data at scale](04-scale-and-evolution/01-data-at-scale/README.md) | Reason about caches, replication, partitioning, streams, and coordination scope. |
| [Performance and cost](04-scale-and-evolution/02-performance-cost/README.md) | Measure the bottleneck and defend an improvement with resource and cost evidence. |
| [AI systems](04-scale-and-evolution/03-ai-systems/README.md) | Evaluate an AI feature, protect permissions, and enforce quality and task budgets. |
| [Migrations and recovery](04-scale-and-evolution/04-migrations/README.md) | Move live data and clients through compatibility, reconciliation, rollback, and retirement. |
| [Technical decisions and engineering effectiveness](04-scale-and-evolution/05-technical-decisions/README.md) | Make options, ownership, adoption, and cross-team decisions explicit. |

## How to move through a lesson

1. Restate the brief, expected values and invariant.
2. Predict the initial diagram, then try the baseline.
3. Implement or draw independently; use the reference to check your attempt.
4. Change the requirement using the existing follow-ups; explain the new failure and updated diagram.
5. Use the tests or acceptance checks, then take an unfamiliar assessment.
6. Return to later-topic follow-ups after their prerequisites. Record the gap rather than treating a job title as a reading route.

AI-assisted exercises practice specification and review. Independent exercises practice implementation and explanation. Both use the same concepts and pages. Follow the stated tool rules for each assessment.

[Study method](../docs/HOW-TO-USE.md) · [Coding index](../indexes/coding.md) · [Projects](../indexes/projects.md) · [Assessments](../practice/README.md) · [Research](../docs/research/interview-evidence.md)
