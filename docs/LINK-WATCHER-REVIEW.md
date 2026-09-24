# Link-watcher reference project: feedback and review scope

Status: **reference revision for Bruno's review; broader rollout is on hold**.

On 24 September 2026, Bruno asked to improve only the link-rot watcher first.
Revise this example with his feedback until he is satisfied, then apply the accepted
standard to the other project and design pages. Do not treat a passing build or
this checklist as his approval.

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
6. Which checks prove each requirement, and which guarantees remain unverified?

- Publication feedback: pushes to main must automatically appear on the website.
  Remove manual directory-migration requirements and optional verification gates
  from the publishing path; do not confuse GitHub checks with deployment status.
