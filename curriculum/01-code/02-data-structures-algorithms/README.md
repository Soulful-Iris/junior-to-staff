# Data structures and algorithms

Learn the structures and algorithms before using them in a coding interview.

[Curriculum](../../README.md) · [About this part](../README.md)

## What this chapter gives you

A map, a queue, or a heap solves a particular kind of repeated work. Learn each tool's operations, trace its state, and see what it costs. Small code examples and diagrams make the mechanism visible. You do not need to solve a full interview problem at every step.

Start after **Problem solving and AI-assisted engineering**. Read the five sections in order; the next chapter puts these tools to work in complete coding problems.

## Learn in this order

| Section | Subsections, in learning order | What you will be able to do |
|---|---|---|
| Cost and basic collections | [Time and space](lessons/00-cost.md), [arrays and strings](lessons/10-sequences.md), [sets](lessons/11-sets.md), [maps](lessons/01-maps.md) | Count work, distinguish position from identity, and replace repeated scans with lookup. |
| Order and linked structures | [Stacks](lessons/07-stack.md), [queues](lessons/12-queues.md), [linked lists](lessons/13-linked-lists.md), [trees](lessons/14-trees.md), [heaps](lessons/06-heaps.md), [tries](lessons/15-tries.md) | Preserve the order, relationships, or priorities a problem needs. |
| Connections | [Graphs, BFS, DFS, and dependencies](lessons/05-graphs.md), [union-find](lessons/16-union-find.md), [weighted paths](lessons/21-weighted-paths.md) | Traverse safely, track components, and distinguish fewest hops from cheapest routes. |
| Narrowing the work | [Sorting](lessons/22-sorting.md), [binary search and intervals](lessons/04-order.md), [two pointers](lessons/17-two-pointers.md), [windows](lessons/02-windows.md), [prefix totals](lessons/03-prefix.md), [greedy choices](lessons/18-greedy.md) | Prove which candidates can be discarded and which work can be reused. |
| Search and reuse | [Backtracking](lessons/09-search.md), [dynamic programming](lessons/08-dp.md), [bits](lessons/19-bits.md), [choosing a tool](lessons/20-choose.md) | Define search state, reuse smaller answers, and choose from the tools deliberately. |

## Before moving into practice

Given a small example, draw the state after each operation. Name the assumption that makes the algorithm correct. Explain time and extra memory separately. Identify an input that would invalidate the assumption.

You can revisit a folded refresher inside each coding problem. The main reading flow will assume these foundations rather than introduce the same structure repeatedly.

Next chapter: [Coding practice: solve, explain, extend](../03-coding-practice/README.md).
