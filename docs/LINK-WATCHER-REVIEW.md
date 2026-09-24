# Link-watcher reference project: feedback and review scope

Status: **approved by Bruno; apply this standard across design and architecture projects**.

Bruno first asked to improve only the link-rot watcher and review it before a wider rollout. He subsequently approved that page and explicitly requested the same approach across all design and architecture projects. The rollout follows that approval; publication remains automatic from main.

| Feedback | Requirement for this example |
|---|---|
| “Zero guidance on what to even do” | Lead with the assignment, user, input, output, and first command. |
| “No real project” / “no real scenario” | Describe a plausible organization and the specific failure its users face; supply runnable local code and controlled HTTP fixtures. |
| “No real stats” | Give explicit workload assumptions, peak conditions, retention and timing objectives; calculate capacity with units. Distinguish exercise inputs from measured results. |
| Diagrams and naming are below engineering expectations | Label the component, service, stored data and operation. Replace vague actors such as “tell somebody” with notification worker, email delivery and delivery status. |
| “No AWS diagrams” | Show an AWS architecture with the provider-neutral role under each AWS service, labelled arrows, trust boundaries, durable state, and failure paths. |
| “No code guidance” | Identify actual files and functions, contracts, table keys, transaction boundaries, examples and implementation tasks. |
| “No infra guidance” | Supply an infrastructure foundation, specific settings, IAM responsibilities, wiring steps, deploy/inspect/cleanup commands and validation limits. |
| “No explanation” | Explain why each component exists, what failure it addresses, and when a simpler alternative fits. |
| Unclear system/architecture language | Use direct engineering language and define unfamiliar terms at first use. Remove repeated review boilerplate and slogans. |
| Visual learner | Place focused architecture, state and failure visuals next to the explanation they support. Keep labels readable. |
| “Don’t write tests. Check if it works” | Do not add test suites for this revision; run the project, inspect its behavior and visually review the page. |
| Learn by implementing | Separate supplied behavior from work to build; give ordered checkpoints with exact expected outputs. |

## Review log

- Rollout completed: 41 design briefs, 33 other engineering project pages and five reading-list stages. Each has a concrete scenario/contract, workload assumptions, code starting point, AWS service/role diagram, ordered implementation guidance, infrastructure settings and observable outcomes. The approved link-watcher remains unchanged.
- Delivery: 75 small local starting programs, the four existing AI reference workflows, 79 authored AWS diagrams and a shared deployable AWS foundation. Direct execution and site rendering were inspected; no internal test suite, interval task or deployment gate was added. The exact page inventory is in `architecture-upgrade-progress.json`.

- Approval: Bruno confirmed the site is fixed, approved the link-watcher changes, and requested the same approach across all design/architecture projects. Push to main; add no internal or interval tests and no deployment gates.

- Initial request: improve engineering quality across all design and architecture problems.
- Scope correction: **only this linked project until Bruno approves it**.
- First revision: concrete documentation-monitor scenario; local Python/SQLite reference;
  live HTTP fixture; AWS service/role architecture; infrastructure foundation; ordered
  implementation tasks and failure checks. Pending user review.

## Questions the page must answer without another conversation

1. What am I building, for whom, and what will I see when it works?
2. What can I run today, and which parts am I expected to implement?
3. What do the numbers imply for concurrency, completion time and storage?
4. Where does each piece of state live, and what happens after a crash or retry?
5. How does local code map to AWS, and what must be configured explicitly?
6. Which observed outcomes support each requirement, and which guarantees remain unverified?

- Publication feedback: pushes to main must automatically appear on the website.
  Remove manual directory-migration requirements and optional verification gates
  from the publishing path; do not confuse GitHub checks with deployment status.
