# Merge k sorted streams

[Curriculum](../../../../README.md) · [Data structures and algorithms](../../README.md) · [All coding problems](../../../../../indexes/coding.md)

> “We export records from several partitions. Each partition produces ascending
> integer keys, and the export needs one ascending stream. The files are too large
> to concatenate in memory. Return a lazy iterator and pull only enough source
> data to determine the next output.”

Constructed practice question. Prerequisite: [heaps](../../lessons/06-heaps.md).
An iterator yields one value on demand. Keeping one **head** from each nonempty
source exposes the smallest value that source could contribute next.

| Contract | Required behavior |
|---|---|
| Input | Finite collection of finite, ascending integer iterables |
| Output | Lazy ascending iterator preserving every occurrence, including ties |
| Boundaries | Empty collection/sources allowed; source index breaks equal-key ties |
| Failure | Nonsorted or noninteger values raise `ValueError` when consumed |
| Scope | Synchronous iterators; no I/O deadlines or atomic all-or-nothing export |

<!-- interview-rehearsal:start -->

## What the interviewer expects

The opening scenario is the product context; the table above is the callable
contract. Your job is to connect them. Before coding, say what the output means,
walk one normal case and one case that could disprove a tempting shortcut, then
name the invariant your implementation will preserve. Start with a correct
baseline, improve it deliberately, and derive time and space from actual work.

**Done means:** Lazy ascending iterator preserving every occurrence, including ties.

Passing the happy path alone is not done; your answer
must make a deliberate decision for every scenario below without mutating input
unless the contract explicitly permits it.

### Test-case scenarios to settle before coding

| Case | Exact input or state | Expected result | What it is testing |
|---|---|---|---|
| Representative | `[1,4]`, `[1,3]`, `[2]` | `1,1,2,3,4` lazily | Heap entries identify their source. |
| No sources | `[]` | empty iterator | The collection itself may be empty. |
| Empty sources | `[[],[1],[]]` | `1` | Do not assume every source has a head. |
| Duplicates | equal values within/across streams | every occurrence retained | Merging is not deduplication. |
| Laziness | a source raises if read past requested prefix | only necessary values consumed | Do not materialize all streams. |
| Late invalid order | source yields 3 then 2 | `ValueError` when 2 is consumed | Iterator validation occurs at the observable boundary. |

Do not merely list these cases in an interview. For each one, point to the branch,
state transition, or invariant that makes the expected result inevitable. If your
design cannot explain a row, the design is not finished yet.

<!-- interview-rehearsal:end -->

`[[1,4],[],[1,3,8]]` produces `[1,1,3,4,8]`. For `[[1,0]]`, the iterator yields
1 and then raises when it reads 0. Previously yielded data cannot be retracted.
Ask whether partial output is acceptable: eager validation requires reading or
spooling complete sources and changes the lazy contract.

```mermaid
flowchart TD
  A["source 0: head 1, then 4"] -->|"head"| H["heap: 1@0, 1@2"]
  B["source 1: empty"]
  C["source 2: head 1, then 3,8"] -->|"head"| H
  H -->|"pop smallest head"| O["output 1 from source 0"]
```

Implement independently. Predict which source advances after the first output
and how many input items have been consumed when the consumer pauses.

<details>
<summary>Solution, frontier invariant, and follow-ups</summary>

Concatenate-and-sort costs O(N log N) time and O(N) retained values for N records.
A better baseline scans k current heads for every output, using O(k) memory and
O(Nk) comparisons. A heap replaces only this repeated minimum search; it does not
change the underlying merge reasoning.

Convert each source to an iterator, read at most one value from each, and heapify
the `(value,source_index)` pairs. Repeatedly pop and yield the smallest pair. When
the consumer resumes, advance that pair's source, check nondecreasing order, and
push its new head. Exhausted sources leave the heap permanently.

**Invariant:** at every selection point, the heap contains exactly one next
unemitted value from each active source. Every later value in that source is at
least its head. The global minimum unseen value is therefore a heap member, and
removing its minimum preserves sorted output and occurrence counts.

| Consumer request | Output | Pull triggered before next selection |
|---|---:|---|
| First | 1 from source 0 | Initial head from each source |
| Second | 1 from source 2 | Source 0 advances to 4 |
| Third | 3 from source 2 | Source 2 advances to 3 |

Initialization costs O(k). Consuming all N outputs costs O(k + N log(k + 1)) time
and O(k) auxiliary space. The caller may accumulate O(N) output, but the generator
does not. Sortedness checks are incremental and cannot discover unconsumed errors.
Closing the generator early does not consume the rest of its inputs.

**Follow-up 1 — a source is temporarily unavailable.** Predict whether the merger
may safely emit 4 while a source has no known head. It cannot: that source might
next yield 2. Distinguish permanent exhaustion from a delayed response. A watermark
(promise that future keys are at least some bound) can permit progress.

```mermaid
flowchart TD
  A["known head 4"] -->|"candidate"| M[merger]
  B["delayed source; future key unknown"] -->|"no ordering bound"| M
  M -->|"must wait"| W["cannot safely emit 4"]
  B -->|"optional watermark at least 5"| P["then 4 becomes safe"]
```

**Follow-up 2 — merge records with equal timestamps stably.** Use a tuple containing
timestamp, source priority, and per-source sequence, with the record outside the
comparison key. Define whether stability is source order or an external global
sequence; timestamp equality alone does not define a total order.

Senior depth includes pull-count tests and failure-after-partial-output semantics.
Lead depth adds cancellation/resource cleanup for real file or network iterators.

Reference: [solution.py](solution.py). Tests compare seeded streams with sorting,
verify laziness using counters, and check empty/tied/invalid inputs.

```bash
python -m unittest discover -s curriculum/01-code/02-data-structures-algorithms/problems/27-merge-k-streams -p 'test_*.py'
```

</details>
