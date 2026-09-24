# Design, ship, and operate the application

<section class="chapter-context" markdown="1">

## Operate the application when conditions change

The application must keep a clear contract during a release, a slow dependency, or a growing queue. You will design the boundary, connect it to infrastructure, record useful evidence, and recover from failures.

Begin with requirements and workload assumptions. Cloud labs are identified explicitly and include their resource setup and cleanup. A local protocol model is useful evidence, but it is not a deployed fleet or a production capacity measurement.

</section>

[Full learning sequence](../README.md)

| Order | Chapter | You will learn to… |
|---|---|---|
| CH 09 | [Design services from requirements to failure behavior](01-system-design/README.md) | Turn requirements and workload estimates into an explainable architecture. |
| CH 10 | [Deploy changes and control feature exposure](02-delivery/README.md) | Build once, verify compatibility, and release a change with stop conditions. |
| CH 11 | [Provision and operate application infrastructure on AWS](03-infrastructure/README.md) | Map a mechanism to explicit infrastructure, permissions, and operational limits. |
| CH 12 | [Trace requests and diagnose production symptoms](04-observability/README.md) | Use logs, metrics, and traces to answer a concrete system question. |
| CH 13 | [Set reliability objectives and recover from failures](05-reliability/README.md) | Budget failures, bound overload, and recover from evidence. |

Study the core material in order. Each lesson keeps its own deeper follow-ups, runnable references and project practice. Difficulty is a property of a question, not a separate directory or curriculum.

Next group: [Scale and evolve the system](../04-scale-and-evolution/README.md).
