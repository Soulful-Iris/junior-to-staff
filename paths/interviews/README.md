# Path B · Software engineering interviews

[Practice drawing the architecture](architecture/whiteboard.md) · [Motion gallery](../../assets/learning/README.md)

Understand the concept. Implement the mechanism. Explain the tradeoff under time pressure. Architecture and AWS are the spine; coding and full-stack implementation are a separate, equally necessary area in this path.

## Start at your level

| Level | Start here | Architecture target | Coding target |
|---|---|---|---|
| Junior | [Junior route](junior/README.md) | A coherent single-service feature, schema, API, and request flow | Correct implementation, tests, and complexity |
| Senior | [Senior route](senior/README.md) | A complete system with quantified constraints, bottlenecks, failure handling, and operations | Adapt known patterns, implement an API or component, debug unfamiliar code |
| Staff | [Staff route](staff/README.md) | Several interacting systems, cross-team contracts, migration, economics, and explicit uncertainty | Maintain hands-on fluency; defend abstractions, concurrency, correctness, and evolvability |

These are this curriculum's practice standards, not universal company level mappings. Confirm your interview format with the recruiter. [Current evidence and limitations](research/README.md) distinguish candidate anecdotes, official guidance, and our own recommendations.

## Follow the material

1. [Architecture concepts](architecture/concepts.md): state, latency, storage, caching, queues, correctness, scaling, and AI systems.
2. [Worked system designs](architecture/designs.md): requirements through AWS mapping, implementation decisions, failure drills, and level-specific follow-ups.
3. [AWS implementation](aws/README.md): service choices, three labs, runnable infrastructure and code for the queue lab.
4. [Coding](coding/README.md): Python algorithms, TypeScript async/state examples, worked solutions, complexity, tests, and practical rounds.
5. [Full stack](full-stack/README.md): browser → API → data → background work, accessibility, security, and UI consistency.
6. [Practice](practice/README.md): timed mocks, scoring, behavioral stories, and improvement loops.

7. [Production architecture casebook](production/README.md): five recent incidents, AWS translations, before/after animations, and recovery exercises.

## How to study a module

Begin with the question before expanding the solution. Predict the visual, implement from memory, test an adversarial input, then answer one follow-up that changes the constraints. Copying a solution into your editor is the start of study, not its completion.

**AI use:** study with it freely; mock once with it and once without it. In a real interview follow the supplied rules. If AI is allowed, explain the generated code, catch failures, and retain your own architectural judgment.

## Run the examples

From the repository root:

```bash
python -m unittest discover -s paths/interviews/coding -p 'test_*.py' -v
node --experimental-strip-types --test paths/interviews/coding/typescript.test.ts
python -m unittest discover -s paths/interviews/aws/labs/job-pipeline -p 'test_*.py' -v
python scripts/check_learning.py
```

Python examples use the standard library. TypeScript examples use erasable type annotations and run with a Node version supporting type stripping (validated with Node 24). AWS deployment is a separate, explicit learner step; local examples do not require an AWS account.

[Choose a path](../README.md) · [AI engineering](../ai-engineering/README.md)
