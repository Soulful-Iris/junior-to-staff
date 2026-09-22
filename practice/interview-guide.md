# Interview practice within the curriculum

[Practice drawing the architecture](../curriculum/03-production/01-system-design/whiteboard.md) · [Motion gallery](../assets/learning/README.md)

Understand the concept. Implement the mechanism. Explain the tradeoff under time pressure. Coding, full-stack implementation, architecture and AWS exercises assess the same curriculum from different angles.

## What the interviewer is asking you to demonstrate

> “A user retries a save after a timeout. Show me the input, the promised state
> change, and what the retry may safely repeat. Now suppose the first save
> committed but its response was lost.”

The opening problem is the teaching anchor. Clarify success and failure,
trace a tiny example, draw or implement a baseline, then change the design only
when an invariant or measured cost requires it. A useful answer makes its
assumptions testable. The individual coding problems and project pages supply
those examples and progressive follow-ups; the assessment packs hold back new
constraints until after your attempt.

## Choose the concept, then the depth

Follow the [curriculum](../curriculum/README.md) for prerequisites. Use [assessment depth](depth.md) to judge the same problem under harder constraints, and [the assessment packs](README.md) for independent sessions. Coding, full-stack, architecture and operational exercises all refer to the same subject pages.

## How to study a module

Begin with the question before expanding the solution. Predict the visual, implement from memory, test an adversarial input, then answer one follow-up that changes the constraints. Copying a solution into your editor is the start of study, not its completion.

**AI use:** study with it freely; mock once with it and once without it. In a real interview follow the supplied rules. If AI is allowed, explain the generated code, catch failures, and retain your own architectural judgment.

## Run the examples

From the repository root:

```bash
python -m unittest discover -s curriculum/01-code/02-data-structures-algorithms -p 'test_*.py' -v
node --experimental-strip-types --test curriculum/01-code/02-data-structures-algorithms/typescript.test.ts
python -m unittest discover -s curriculum/03-production/03-infrastructure/aws/labs/job-pipeline -p 'test_*.py' -v
python scripts/check_learning.py
```

Python examples use the standard library. TypeScript examples use erasable type annotations and run with a Node version supporting type stripping (validated with Node 24). AWS deployment is a separate, explicit learner step; local examples do not require an AWS account.
