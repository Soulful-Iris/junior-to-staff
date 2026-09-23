# Validate a BST: carry every ancestor constraint

[Curriculum](../../../../README.md) · [Data structures and algorithms](../../README.md) · [All coding problems](../../../../../indexes/coding.md)

Constructed practice problem; no company attribution. Prerequisites: [tree structure and identity](../17-tree-level-order/README.md) and [ordered boundaries](../11-binary-search-boundary/README.md).

## Candidate brief

> A storage index exports a binary tree and claims it is a strict binary search tree. Every value in a left subtree must be smaller than its ancestor, and every value in a right subtree larger. Validate that claim. Is checking each node against only its immediate children enough?

| Contract | Decision |
|---|---|
| Input | Binary `Node` tree with integer values, bool excluded; `None` is empty |
| Output | Boolean for strict BST ordering; equal values anywhere cannot satisfy strict ordering |
| Boundaries | Empty/singleton trees are valid; unbounded Python integers allowed; no mutation |
| Invalid input | Invalid values/links, cycles, or shared nodes raise `ValueError`; ordering violations return `False` |
| Excluded | Balancing guarantees and duplicate-placement policies |

## The tool before the challenge

For a binary search tree, a node must satisfy **every ancestor's** bounds, not merely its direct parent's comparison. Carry a permissible range down the recursion:
```python
def allowed(value, lower, upper):
    return lower < value < upper  # strict: duplicates are invalid here
```
A right child 6 under root 5 looks locally fine, but if it lies inside left subtree rooted at 3 it violates the root's upper bound of 5.

### A design choice worth saying aloud

`lower` and `upper` are exclusive bounds, so duplicate values fail the BST contract. A local child comparison is insufficient: a node 6 deep in the left subtree of root 5 must fail even if its immediate parent is 3. If duplicates become legal, state which side admits equality and adjust both checks.

<!-- interview-rehearsal:start -->

## What the interviewer expects

The interviewer gives you the scenario and the contract above. Explain what a
successful call returns, walk through one example below, and name what your
state means *before* choosing a data structure.

**Done means:** Boolean for strict BST ordering; equal values anywhere cannot satisfy strict ordering.

Now predict each output before looking at the reference; invalid input should
leave any existing state unchanged unless the contract says otherwise.

### Test-case scenarios to settle before coding

| Case | Exact input or state | Expected result | What it is testing |
|---|---|---|---|
| Valid | 2 with children 1 and 3 | `True` | Both global bounds hold. |
| Ancestor violation | 10 → left 5 → right 12 | `False` | Checking only each parent misses the violation. |
| Duplicate | 2 with child 2 | `False` | The baseline ordering is strict. |
| Empty/singleton | `None` / one integer node | `True` / `True` | Small valid structures establish boundaries. |
| Invalid value | a node contains `True` | `ValueError` | Boolean is excluded despite integer inheritance. |
| Invalid topology | cycle or shared child | `ValueError` | Ordering failure does not hide structural corruption. |

For each case, show which branch or state change produces that result.

<!-- interview-rehearsal:end -->

`Node(2, Node(1), Node(3))` is valid.
`Node(10, Node(5), Node(15, Node(6), Node(20)))` is invalid: 6 is in 10's right subtree.
`Node(2, Node(2))` returns `False`; `Node(True)` raises `ValueError`.

Before opening the explanation, restate the contract, trace the smallest useful
example, implement a baseline, and identify the repeated work. Then implement
your improvement independently and derive tests from the contract. Say what
your state means before saying which data structure stores it.

<details>
<summary>Worked lesson, changed requirements, and reference</summary>

### The failure is a forgotten ancestor

A local child comparison accepts the counterexample because 6 is less than 15,
while forgetting that the entire right subtree must exceed 10. A correct baseline
checks every node against all values in its left and right subtrees. Repeated
subtree scans cost O(n²) on a skewed tree. The reusable improvement is to carry
the ancestor requirements downward instead of rediscovering them below each node.

```mermaid
flowchart TD
    A[10: unrestricted bounds] --> B[5: value below 10]
    A --> C[15: value above 10]
    C --> D[6: must lie strictly between 10 and 15]
    C --> E[20: value above 15]
```

Represent a frame as `(node, lower, upper)` with exclusive bounds; None means an
absent bound, not a numeric sentinel. On entry, the bounds summarize every
ancestor constraint. Reject ordering when `value <= lower` or `value >= upper`.
The left child inherits lower and receives current value as upper; the right
child receives current value as lower and inherits upper. If all frames pass,
each node satisfies every relevant ancestor, which is exactly the strict BST
definition. Conversely, a violated ancestor relationship excludes a node from
its carried interval, so it is detected.

| Frame | Allowed interval | Value | Ordering result |
|---|---|---:|---|
| root | unbounded | 10 | valid locally |
| root.right | `(10, unbounded)` | 15 | valid locally |
| root.right.left | `(10, 15)` | 6 | false |

The logical recursive return is a boolean: this node is in bounds **and** both
child calls return true; an empty child returns true. The reference uses explicit
stack frames to avoid Python recursion limits. It records an ordering-failure
flag but continues validating shape and value types, so a malformed branch still
raises ValueError even when another branch already violates ordering. This
distinguishes a validly represented non-BST from an invalid object graph.

Each node is visited once: O(n) time. Trusted-tree DFS needs O(h) frame space,
but the reference's identity set detects shared nodes/cycles and raises total
auxiliary space to O(n). Integer bounds avoid false failures at extreme values.
The function does not prove balance or efficient lookup merely by returning true.

### Follow-up 1: allow duplicate keys only in right subtrees

Predict how bounds must carry inclusion as well as value. A left edge adds an
exclusive upper bound; a right edge adds an inclusive lower bound.

| Structure | Strict policy | Duplicates-right policy |
|---|---|---|
| root 2, right child 2 | false | true |
| root 2, left child 2 | false | false |
| root 2, right 3 with left 2 | false | true: still in root's right subtree |

Globally replacing both comparisons with inclusive ones is wrong: it permits
duplicates on the left. This policy also interacts with rotations; a balancing
operation may require counts stored within one node instead of duplicate nodes.

### Follow-up 2: validate an inorder stream

```mermaid
flowchart TD
    L[Visit left subtree] --> N[Compare current value with previous emitted value]
    N -->|must strictly increase| R[Visit right subtree]
    P[Previous value and presence flag] --> N
    N -->|replace previous| P
```

Inorder traversal emits left, node, right, so strict increase is equivalent to
strict BST ordering for a valid tree. A stream of values alone cannot validate
the original graph shape; that must be established elsewhere. A senior candidate
explains recursive return meaning, bounds, and malformed-versus-false behavior.
A lead candidate defines duplicate and structural-validation policy at the
serialization boundary rather than silently changing it in one consumer.

### Run and check

From the repository root:

```bash
cd curriculum/01-code/02-data-structures-algorithms/problems/18-validate-bst
python -m unittest -v test_solution.py
```

[Reference implementation](solution.py) · [Contract and oracle tests](test_solution.py).
Read the tests after your attempt. A green reference suite verifies the supplied
implementation; it does not demonstrate independent transfer. Reimplement one
follow-up with the reference closed and explain which old invariant no longer holds.

</details>

[Ordered foundation route](../foundations-index.md) · [Coding home](../../practice-sequence.md)
