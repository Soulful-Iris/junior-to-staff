#!/usr/bin/env python3
"""Insert the maintained interview expectation and edge-case blocks.

The problem implementations and tests remain authoritative. This script makes
their important behavioral distinctions visible before a learner opens the
worked answer. It is intentionally idempotent so future editing can regenerate
the marked blocks without disturbing authored explanations.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
START = '<!-- interview-rehearsal:start -->'
END = '<!-- interview-rehearsal:end -->'

# case, exact input/state, expected result, lesson exposed by the case
CASES = {
1: [
('Representative', '`[2, 7, 11, 15]`, target `9`', '`(0, 1)`', 'A prior complement should be found.'),
('Repeated value', '`[3, 3]`, target `6`', '`(0, 1)`', 'Two positions may hold the same value.'),
('No answer', '`[1, 2, 3]`, target `20`', '`None`', 'Absence is part of the return contract.'),
('Too little input', '`[]` and `[9]`', '`None` for both', 'One position cannot be reused.'),
('Tie rule', '`[1, 4, 2, 3]`, target `5`', '`(0, 1)`', 'Smallest right index wins before later pairs.'),
('Invalid/atomic', '`[True, 2]`, target `3`', '`ValueError`; input unchanged', 'Python booleans must not silently count as integers.'),
],
2: [
('Both empty', '`""`, `""`', '`True`', 'The empty multiplicity maps are equal.'),
('Same inventory', '`"aab"`, `"aba"`', '`True`', 'Order is irrelevant; counts are not.'),
('Missing copy', '`"aab"`, `"ab"`', '`False`', 'A set would lose multiplicity.'),
('Case', '`"A"`, `"a"`', '`False`', 'Comparison is exact and case-sensitive.'),
('Unicode form', 'precomposed `"é"` vs `"e\u0301"`', '`False`', 'Normalization is explicitly outside the baseline.'),
('Invalid', '`None`, `""`', '`ValueError`', 'Reject the contract violation before counting.'),
],
3: [
('Representative', '`["eat","tea","tan","ate"]`', '`[["eat","tea","ate"],["tan"]]`', 'Canonical keys form groups.'),
('Empty batch', '`[]`', '`[]`', 'No synthetic empty group is created.'),
('Empty words', '`["",""]`', '`[["",""]]`', 'Empty strings are real entries.'),
('Duplicates', '`["ab","ab","ba"]`', 'one group retaining all three entries', 'Do not deduplicate input.'),
('Stable order', '`["tan","eat","nat","tea"]`', 'groups and members follow first appearance', 'Sorting the final answer changes the contract.'),
('Invalid/atomic', '`["ok", 7]`', '`ValueError`; input unchanged', 'Validate the whole batch.'),
],
4: [
('Representative', '`"abba"`', '`(0, 2)` for `"ab"`', 'The left edge never moves backward.'),
('Empty', '`""`', '`(0, 0)`', 'Half-open indices still form a valid empty slice.'),
('All repeated', '`"aaaa"`', '`(0, 1)`', 'A repeated character closes the longer window.'),
('Tie', '`"abcaef"`', 'earliest maximum window', 'Equal lengths do not replace the earlier answer.'),
('Exact code points', '`"aA"`', '`(0, 2)`', 'Case-sensitive symbols are distinct.'),
('Invalid', 'non-string input', '`ValueError`', 'The API does not coerce collections to text.'),
],
5: [
('Representative', '`"ABAAC"`, required `"AAC"`', '`(2, 5)` for `"AAC"`', 'Required multiplicities drive validity.'),
('Empty requirement', 'any text, required `""`', '`(0, 0)`', 'The empty need is already satisfied.'),
('Impossible multiplicity', '`"ab"`, required `"aa"`', '`None`', 'Presence without enough copies is insufficient.'),
('Surplus', '`"AAABC"`, required `"AC"`', 'shortest window containing one A and one C', 'Extra required characters must not inflate unmet demand.'),
('Tie', 'two equal-length valid windows', 'the one with the smallest start', 'State the deterministic result before coding.'),
('Invalid', 'either argument is not a string', '`ValueError`', 'Validation precedes scanning.'),
],
6: [
('Representative', '`[1,-1,0]`, target `0`', '`3`', 'Overlapping ranges count separately.'),
('All zeros', '`[0,0]`, target `0`', '`3`', 'Repeated prefix sums contribute multiplicity.'),
('Empty', '`[]`, target `0`', '`0`', 'The empty subarray is excluded.'),
('Negative values', '`[3,-2,-1]`, target `0`', '`1`', 'Sliding-window monotonicity is unavailable.'),
('No match', '`[1,2]`, target `9`', '`0`', 'The result is a count, never `None`.'),
('Invalid/atomic', 'boolean element or target', '`ValueError`; input unchanged', 'Exact integer validation matters.'),
],
7: [
('Representative', '`[2,3,4]`', '`[12,8,6]`', 'Each answer combines strict prefix and suffix.'),
('Singleton', '`[7]`', '`[1]`', 'The product of no other values is the multiplicative identity.'),
('One zero', '`[0,3,4]`', '`[12,0,0]`', 'Only the zero position sees the nonzero product.'),
('Two zeros', '`[0,0,4]`', '`[0,0,0]`', 'Every exclusion still contains a zero.'),
('Negative values', '`[-1,2,-3]`', '`[-6,3,-2]`', 'Signs follow ordinary integer multiplication.'),
('Invalid/atomic', '`[1,False]`', '`ValueError`; input unchanged', 'No division or silent boolean coercion.'),
],
8: [
('Representative', '`[100,4,200,1,3,2,2]`', '`4`', 'Duplicates do not lengthen the run 1..4.'),
('Empty', '`[]`', '`0`', 'No run exists.'),
('Negative bridge', '`[-1,1,0]`', '`3`', 'The ordering crosses zero normally.'),
('Duplicates only', '`[5,5,5]`', '`1`', 'Distinct values define run length.'),
('Separated values', '`[1,3,5]`', '`1`', 'Input adjacency is irrelevant.'),
('Invalid/atomic', 'noninteger or boolean element', '`ValueError`; input unchanged', 'Validate before building the set.'),
],
9: [
('Representative', '`[(5,7),(1,3),(3,6)]`', '`[(1,7)]`', 'Sorting exposes one unresolved covered range.'),
('Empty', '`[]`', '`[]`', 'No placeholder interval is returned.'),
('Disjoint', '`[(1,2),(3,4)]`', 'both intervals in sorted order', 'A real gap stays visible.'),
('Touching', '`[(1,3),(3,5)]`', '`[(1,5)]`', 'This contract merges half-open boundaries that touch.'),
('Nested/duplicate', '`[(1,10),(2,3),(1,10)]`', '`[(1,10)]`', 'Contained coverage adds no new range.'),
('Invalid/atomic', '`[(3,3)]` or malformed pair', '`ValueError`; input unchanged', 'Reject zero duration and bad structure.'),
],
10: [
('Representative', '`[(0,10),(5,7),(7,12)]`', '`2`', 'End-before-start tie handling lets a room turn over at 7.'),
('Empty', '`[]`', '`0`', 'No rooms are required.'),
('Touching', '`[(1,2),(2,3)]`', '`1`', 'Half-open meetings share a room.'),
('Duplicates', '`[(1,4),(1,4)]`', '`2`', 'Multiplicity matters even for identical intervals.'),
('Nested', '`[(0,10),(2,3),(4,5)]`', '`2`', 'Peak concurrency is not number of meetings.'),
('Invalid/atomic', '`[(4,4)]`', '`ValueError`; input unchanged', 'Zero-duration entries are outside the contract.'),
],
11: [
('Present duplicate', '`[1,3,3,8]`, target `3`', '`1`', 'Return the first equal position.'),
('Absent middle', 'same list, target `4`', '`3`', 'Return the insertion boundary.'),
('Beyond right', 'same list, target `9`', '`4`', 'The sentinel is `len(nums)`.'),
('Empty', '`[]`, target `2`', '`0`', 'The only insertion point is zero.'),
('Before left', '`[2,4]`, target `1`', '`0`', 'Nothing is proven smaller.'),
('Invalid/atomic', '`[3,1]`, target `2`', '`ValueError`; input unchanged', 'Checked input must actually be sorted.'),
],
12: [
('Representative', '`[4,5,7,0,1,2]`, target `1`', '`4`', 'One half remains ordered at every step.'),
('Absent', 'same array, target `6`', '`-1`', 'Absence uses an index sentinel.'),
('Empty', '`[]`, any target', '`-1`', 'No midpoint exists.'),
('Unrotated', '`[1,2,3]`, target `2`', '`1`', 'A rotation by zero is valid.'),
('Singleton', '`[1]`, target `1` / `2`', '`0` / `-1`', 'Both smallest success and failure paths matter.'),
('Invalid/atomic', 'duplicates or invalid rotation', '`ValueError`; input unchanged', 'The ordered-half proof relies on the contract.'),
],
13: [
('Representative', '`[3,2,2,4,1,4]`, days `3`', '`6`', 'Capacity 5 fails and 6 is feasible.'),
('Empty shipment', '`[]`, days `2`', '`0`', 'No capacity is required.'),
('One day', '`[2,3,4]`, days `1`', '`9`', 'Every package must fit in one ordered day.'),
('Many days', '`[2,3,4]`, days `10`', '`4`', 'Unused days are allowed; largest package is the floor.'),
('No splitting', '`[8,1,1]`, days `2`', '`8`', 'A package is indivisible.'),
('Invalid/atomic', 'zero weight or nonpositive days', '`ValueError`; input unchanged', 'Validate before feasibility search.'),
],
14: [
('Representative', '`a → b → c → None`', 'same objects as `c → b → a → None`', 'Identity, not copied values, defines success.'),
('Empty', '`None`', '`None`', 'No links are written.'),
('Singleton', '`a → None`', 'the exact object `a`', 'Head identity stays the same.'),
('Repeated values', 'three distinct nodes all storing `1`', 'all three identities reversed', 'Values cannot identify nodes.'),
('Cycle', '`a → b → a`', '`ValueError` before mutation', 'Validation must not partially destroy the structure.'),
('Malformed link', 'reachable `next` is not Node/None', '`ValueError` before mutation', 'Atomic rejection is observable behavior.'),
],
15: [
('Acyclic', '`a → b → None`', '`None`', 'Equal values would not create a cycle.'),
('Self-cycle', '`a.next = a`', 'the exact object `a`', 'The smallest cycle must terminate.'),
('Tail into cycle', '`a → b → c → b`', 'the exact object `b`', 'Meeting point and entry are different concepts.'),
('Repeated values', 'acyclic nodes sharing a value', '`None`', 'Use object identity.'),
('No mutation', 'any valid chain', 'every original link unchanged', 'Detection is observational.'),
('Malformed link', 'reachable non-node `next`', '`ValueError`', 'Reject invalid topology explicitly.'),
],
16: [
('Representative', '`1→3` and `1→2`', '`1(first)→1(second)→2→3`', 'The first chain wins equal-value ties.'),
('One empty', '`None` and `2→4`', 'the original second head', 'No replacement nodes are needed.'),
('Both empty', '`None`, `None`', '`None`', 'The frontier can be empty on both sides.'),
('Duplicates', '`1→1` and `1`', 'all identities retained stably', 'Multiplicity and stable ties matter.'),
('Shared node', 'two inputs converge on one object', '`ValueError` before mutation', 'Splicing shared ownership can create corruption.'),
('Unsorted/malformed', 'a descending link or cycle', '`ValueError` before mutation', 'Validate the whole reachable inputs.'),
],
17: [
('Representative', 'root a; children b,c; b has d', '`[[a],[b,c],[d]]` by value', 'Queue boundaries preserve levels.'),
('Empty', '`None`', '`[]`', 'No empty level is emitted.'),
('Singleton', 'one node', 'one one-element level', 'Depth zero is represented.'),
('Duplicate values', 'distinct nodes with equal values', 'both values appear', 'Topology, not a value set, controls visitation.'),
('Shared child', 'left and right reference same node', '`ValueError`', 'The input must be a tree, not a DAG.'),
('Cycle/malformed', 'child returns to ancestor or invalid object', '`ValueError`; no mutation', 'Traversal must terminate safely.'),
],
18: [
('Valid', '2 with children 1 and 3', '`True`', 'Both global bounds hold.'),
('Ancestor violation', '10 → left 5 → right 12', '`False`', 'Checking only each parent misses the violation.'),
('Duplicate', '2 with child 2', '`False`', 'The baseline ordering is strict.'),
('Empty/singleton', '`None` / one integer node', '`True` / `True`', 'Small valid structures establish boundaries.'),
('Invalid value', 'a node contains `True`', '`ValueError`', 'Boolean is excluded despite integer inheritance.'),
('Invalid topology', 'cycle or shared child', '`ValueError`', 'Ordering failure does not hide structural corruption.'),
],
19: [
('Split branches', 'p in left subtree, q in right', 'root object', 'The first subtree joining both presences wins.'),
('Ancestor', 'p is an ancestor of q', 'the exact object p', 'A node is its own ancestor.'),
('Same query', '`p is q` and reachable', 'the exact p object', 'Presence is counted correctly once.'),
('One absent', 'p reachable, q detached', '`None`', 'A partial candidate is not an answer.'),
('Equal values', 'different nodes share values', 'identity-based ancestor', 'Values cannot substitute for node identity.'),
('Invalid topology', 'cycle/shared child/malformed query', '`ValueError`', 'Validate even when an answer seems discoverable early.'),
],
20: [
('Representative', 'a with b,c; b with d,e', '`3` edges', 'The best path can combine two child heights.'),
('Empty', '`None`', '`0`', 'No path has zero edges.'),
('Singleton', 'one node', '`0`', 'Diameter counts edges, not nodes.'),
('Chain', 'four nodes in one line', '`3`', 'The deepest subtree can contain the answer.'),
('Off-root maximum', 'long path entirely within one subtree', 'that subtree distance', 'Do not require the global root to be crossed.'),
('Invalid topology', 'cycle or shared child', '`ValueError`', 'Tree assumptions are enforced.'),
],
21: [
('Representative', 'tasks fetch,parse,save,metrics; fetch→parse→save', '`[fetch,metrics,parse,save]`', 'Independent tasks must not disappear.'),
('Empty', 'no tasks or edges', '`[]`', 'An empty plan is valid.'),
('Duplicate edge', 'submit fetch→parse twice', 'count the prerequisite once', 'Indegree represents unique requirements.'),
('Partial cycle', 'fetch→parse→save→fetch plus metrics', '`ValueError`', 'A runnable vertex does not make the whole plan valid.'),
('Unknown task', 'edge mentions undeclared task', '`ValueError`', 'The graph is closed over declared IDs.'),
('Long chain', 'thousands of serial tasks', 'every task once without recursion failure', 'Work should be O(V+E).'),
],
22: [
('Representative', '`hit` to `cog` through standard dictionary', 'a shortest endpoint-inclusive path', 'BFS returns minimum transformations.'),
('Same endpoint', '`same` to `same`', '`["same"]`', 'Zero transformations still includes the endpoint.'),
('Missing end', 'end absent from dictionary', '`[]`', 'A different end must be admitted.'),
('Unreachable', 'valid words split into components', '`[]`', 'Valid input need not have a solution.'),
('Duplicates', 'dictionary repeats a word', 'same path semantics', 'Repeated entries do not create states.'),
('Invalid', 'mixed lengths or non-lowercase ASCII', '`ValueError`', 'Neighbor generation depends on the alphabet contract.'),
],
23: [
('Initial', 'fresh set of n vertices', '`connected(a,b)` false when a≠b', 'Every vertex starts as its own component.'),
('Merge', '`union(0,3)`', '`True`; now connected', 'A successful union reduces component count once.'),
('Repeat', 'same union again', '`False`', 'Idempotence avoids double accounting.'),
('Self link', '`union(2,2)`', '`False`', 'A vertex already shares its own component.'),
('Empty universe', '`n=0`', 'construction succeeds; any lookup is out of range', 'Empty is valid, phantom vertices are not.'),
('Bounds', 'negative or `n` index', '`IndexError`; state unchanged', 'Python negative indexing is not allowed here.'),
],
24: [
('Representative', 'open grid with a wall forcing a detour', 'an endpoint-inclusive shortest coordinate path', 'BFS discovers by distance layers.'),
('Same endpoint', 'open start equals goal', 'one-coordinate path', 'Distance zero still includes the point.'),
('Blocked endpoint', 'start or goal cell is 1', '`[]`', 'Blocked is valid input but unsolvable.'),
('Unreachable', 'walls separate the endpoints', '`[]`', 'Failure is not an exception.'),
('Tie', 'two equal shortest routes', 'either valid shortest route', 'Do not overfit an unspecified tie.'),
('Invalid/atomic', 'empty/ragged grid or bad coordinate', '`ValueError`; grid unchanged', 'Validate shape and bounds.'),
],
25: [
('Relaxation', 'A→B 8, A→C 1, C→B 2', '`(3,[A,C,B])`', 'First discovery is not final.'),
('Same vertex', 'source equals target', '`(0,[source])`', 'The empty edge path is valid.'),
('Unreachable', 'target in a disconnected component', '`(inf,[])`', 'Absence has an explicit pair result.'),
('Zero-cost cycle', 'cycle edges cost zero', 'terminates with an optimal simple witness', 'Stale heap work must not loop.'),
('Huge integers', 'weights beyond float precision', 'exact integer total', 'Do not coerce costs to float.'),
('Invalid anywhere', 'negative/nonfinite edge in disconnected component', '`ValueError`', 'Whole-graph validation is not traversal-dependent.'),
],
26: [
('No arrivals', 'fresh `TopK(3)`', '`[]`', 'A query does not invent values.'),
('Fewer than k', 'add 4,1 to k=3', '`[4,1]`', 'Return only observed values.'),
('More than k', 'add 4,1,7,3 to k=2', '`[7,4]`', 'Only the retained frontier matters.'),
('Duplicates', 'add 5,5,4 to k=2', '`[5,5]`', 'Observations are not distinct keys.'),
('Zero k', 'add any values to k=0', '`[]`', 'Nothing is retained.'),
('Invalid/atomic', 'boolean sample or negative k', '`ValueError`; prior snapshot unchanged', 'Failed input must not corrupt retained state.'),
],
27: [
('Representative', '`[1,4]`, `[1,3]`, `[2]`', '`1,1,2,3,4` lazily', 'Heap entries identify their source.'),
('No sources', '`[]`', 'empty iterator', 'The collection itself may be empty.'),
('Empty sources', '`[[],[1],[]]`', '`1`', 'Do not assume every source has a head.'),
('Duplicates', 'equal values within/across streams', 'every occurrence retained', 'Merging is not deduplication.'),
('Laziness', 'a source raises if read past requested prefix', 'only necessary values consumed', 'Do not materialize all streams.'),
('Late invalid order', 'source yields 3 then 2', '`ValueError` when 2 is consumed', 'Iterator validation occurs at the observable boundary.'),
],
28: [
('Eviction', 'capacity 2; put a,b; get a; put c', 'evict b', 'A successful read refreshes recency.'),
('Overwrite', 'put existing a with new value', 'no size growth; a becomes most recent', 'Update and insert differ.'),
('Stored None', 'put key with value `None`', '`get` returns `None`', 'None cannot stand in for a miss.'),
('Miss', 'get absent key', '`KeyError`', 'Miss behavior is explicit.'),
('Zero capacity', 'put a into capacity 0', 'returns a as immediately evicted', 'The structure retains nothing.'),
('Invalid construction', 'negative/noninteger capacity', '`ValueError`', 'Capacity is validated once.'),
],
29: [
('Before boundary', 'deadline 105; get at 104.999', 'stored value', 'Liveness is strict `now < deadline`.'),
('Exact boundary', 'get at 105', '`KeyError`', 'Expiration does not wait for cleanup.'),
('Stored None', 'live key maps to `None`', '`get` returns `None`', 'A miss needs an exception, not a sentinel.'),
('Zero TTL', 'put with TTL 0', 'key is immediately absent', 'No transient live interval exists.'),
('Overwrite invalid', 'live key then put invalid TTL', '`ValueError`; old value/deadline remain', 'Validation is atomic.'),
('Purge sample', 'several deadlines around one injected time', 'remove exactly all expired keys', 'Read the clock once for a coherent purge.'),
],
30: [
('Representative', 'add car,card,cat; suggest `car`, 5', '`["car","card"]`', 'A terminal prefix word remains a suggestion.'),
('Limit', 'same data; suggest `car`, 1', '`["car"]`', 'Stop after enough lexicographic results.'),
('Empty prefix', 'suggest `""`, 5', 'first five words globally', 'The root represents all words.'),
('Duplicate add', 'add car twice', 'car appears once', 'Dictionary membership is unique.'),
('No match/zero limit', 'prefix z or limit 0', '`[]`', 'Both are normal results.'),
('Invalid', 'uppercase/empty added word or negative limit', '`ValueError`', 'The fixed alphabet contract is enforced.'),
],
31: [
('Representative', '`[2,3,6,7,2]`, target 7', '`[[2,2,3],[7]]`', 'Duplicate candidates collapse; reuse remains legal.'),
('Zero target', 'any valid candidates, target 0', '`[[]]`', 'One empty combination reaches zero.'),
('Impossible', '`[4,6]`, target 5', '`[]`', 'No witness is not an exception.'),
('Lexical order', 'several valid combinations', 'sorted nondecreasing combinations', 'Determinism is part of output.'),
('No mutation', 'unsorted candidate input', 'same input after return', 'Search works on owned normalized state.'),
('Invalid', 'zero/negative/bool candidate or negative target', '`ValueError`', 'Nonpositive choices could break termination.'),
],
32: [
('Representative', 'board contains an orthogonal spelling', '`True`', 'A path may turn.'),
('No cell reuse', 'word needs the same cell twice', '`False`', 'Visited state belongs to the current path.'),
('Backtrack', 'first matching prefix dead-ends; later start succeeds', '`True`', 'Restore state before exploring alternatives.'),
('Empty word', 'any board, including empty', '`True`', 'No cells are required.'),
('Empty board', 'nonempty word', '`False`', 'Valid but unsatisfiable.'),
('Invalid/atomic', 'ragged board or multi-character cell', '`ValueError`; board unchanged', 'Validation and restoration are observable.'),
],
33: [
('Greedy trap', '`[1,3,4]`, amount 6', '`(2,[3,3])`', 'Largest-first is not generally optimal.'),
('Zero amount', 'any valid coins, amount 0', '`(0,[])`', 'The empty witness is optimal.'),
('Impossible', '`[2]`, amount 3', '`(-1,[])`', 'No witness has a distinct result.'),
('Duplicate coins', '`[1,1,3]`', 'same answer as unique denominations', 'Input duplicates add no choice.'),
('Tied optimum', 'multiple minimum witnesses', 'any stated optimal witness', 'Do not promise an unspecified tie.'),
('Invalid/atomic', 'nonpositive coin or negative amount', '`ValueError`; input unchanged', 'DP states require positive progress.'),
],
34: [
('Representative', '`[10,9,2,5,3,7,101,18]`', 'a length-4 witness such as `[2,3,7,18]`', 'Return values, not only length.'),
('Empty', '`[]`', '`[]`', 'No witness exists.'),
('All equal', '`[2,2,2]`', 'one `2`', 'Increasing is strict.'),
('Decreasing', '`[5,4,3]`', 'any one value allowed by tie contract', 'Best length can be one.'),
('Tails warning', 'sequence where tails array mixes predecessors', 'a reconstructed valid subsequence', 'Optimization state is not automatically the witness.'),
('Invalid/atomic', 'noninteger/bool element', '`ValueError`; input unchanged', 'Validate before reconstruction state.'),
],
35: [
('Representative', '`"kitten"` to `"sitting"`', '`3`', 'Replace, replace, insert is optimal.'),
('Equal', 'same string twice', '`0`', 'No operation is required.'),
('Empty side', '`""` to length-n text', '`n`', 'Every target symbol must be inserted.'),
('Order', '`"ab"` to `"ba"`', '`2`', 'Transposition is not a baseline operation.'),
('Unicode', 'strings compared by Python code point', 'distance over exact code points', 'No implicit normalization/grapheme logic.'),
('Invalid', 'either input non-string', '`ValueError`', 'The API does not stringify values.'),
],
36: [
('Representative', '`"226"`', '`3`', 'It partitions as 2-2-6, 22-6, and 2-26.'),
('Leading zero', '`"06"`', '`0`', 'Zero cannot begin a code.'),
('Valid zero', '`"10"` / `"20"`', '`1` / `1`', 'Zero participates only in those pairs.'),
('Invalid zero', '`"30"` / `"100"`', '`0` / `0`', 'A preceding digit does not always rescue zero.'),
('Empty public input', '`""`', '`0`', 'Public semantics differ from the DP empty suffix base.'),
('Invalid/large', 'nondigit raises; long valid digits return exact integer', 'no truncation or modulus', 'Separate validation from arbitrary-size counting.'),
],
37: [
('Representative', '`[73,74,75,71,69,72,76,73]`', '`[1,1,4,2,1,1,0,0]`', 'Unresolved days remain on a decreasing stack.'),
('Empty', '`[]`', '`[]`', 'Output shape matches input.'),
('Equals', '`[5,5,5]`', '`[0,0,0]`', 'Warmer means strictly greater.'),
('Decreasing', '`[3,2,1]`', '`[0,0,0]`', 'No future resolution exists.'),
('Negative', '`[-2,-1]`', '`[1,0]`', 'Temperature sign is irrelevant.'),
('Invalid/atomic', 'noninteger/bool element', '`ValueError`; input unchanged', 'Validation precedes stack mutation.'),
],
38: [
('Representative', '`[2,1,5,6,2,3]`', '`10`', 'Height 5 across width 2 is best.'),
('Empty/all zero', '`[]` / `[0,0]`', '`0` / `0`', 'No positive rectangle exists.'),
('Plateau', '`[2,2,2]`', '`6`', 'Equal heights must combine across width.'),
('Zero split', '`[2,0,2]`', '`2`', 'A zero ends positive rectangles.'),
('Final flush', '`[1,2,3]`', '`4`', 'Remaining bars need a virtual right boundary.'),
('Invalid/atomic', 'negative or noninteger height', '`ValueError`; input unchanged', 'Histogram geometry assumes nonnegative integers.'),
],
39: [
('Precedence', '`a==TRUE OR b==TRUE AND c==TRUE` with T,F,F', '`True`', 'AND binds before OR.'),
('Parentheses', '`(a==TRUE OR b==TRUE) AND c==TRUE`', '`False`', 'Grouping changes authority.'),
('Missing', '`missing != "admin"`', '`False`', 'Absence cannot accidentally grant access.'),
('Malformed right branch', '`a==TRUE OR ???`', '`ValueError`', 'Short-circuit evaluation must not skip parsing.'),
('Quoted content', 'string literal containing spaces/escaped quote/OR text', 'one decoded literal token', 'Splitting on whitespace or keywords is wrong.'),
('Resource/type boundary', 'too many tokens/depth or mismatched scalar type', '`ValueError` for limits; comparison false for type mismatch', 'Syntax admission and evaluation semantics differ.'),
],
40: [
('Window boundary', 'width 10; events at 9 and 10', 'counts in `[0,10)` and `[10,20)`', 'Intervals are half-open.'),
('Allowed late', 'event arrives behind watermark but window not closed', '`add` returns true and count includes it', 'Arrival order differs from event time.'),
('Too late', '`end + lateness <= watermark`', '`add` returns false', 'Closed windows never reopen.'),
('Exact close', 'watermark equals end plus lateness', 'emit that nonempty window once', 'Equality belongs to closed.'),
('Duplicates/empty', 'same timestamp twice; untouched windows', 'duplicates count; empty windows omitted', 'Events are observations, not unique IDs.'),
('Invalid/atomic', 'decreasing watermark or bad number', '`ValueError`; watermark/state unchanged', 'Failed control input cannot move time backward.'),
],
41: [
('Odd count', 'add 5,1,9', '`Fraction(5,1)`', 'Median is the ordered middle.'),
('Even count', 'add 1,2', '`Fraction(3,2)`', 'Return an exact average.'),
('Duplicates', 'add 4,4,4,4', '`Fraction(4,1)`', 'Multiplicity is preserved.'),
('Empty', 'median before any add', '`ValueError`', 'No sentinel number represents absence.'),
('Huge integers', 'two values beyond float precision', 'exact `Fraction`', 'Do not overflow or round through float.'),
('Invalid/atomic', 'boolean/noninteger observation', '`ValueError`; prior median unchanged', 'Heap balance survives rejected input.'),
],
42: [
('FIFO', 'put A, put B, then two gets', 'A then B', 'Acceptance order is preserved.'),
('Full producer', 'capacity 1 contains A; producer puts B', 'producer waits until A is removed, then succeeds once', 'Use a condition loop, not one wakeup assumption.'),
('Empty consumer', 'consumer gets from empty queue', 'waits until item, close, cancel, or deadline', 'Every wake path rechecks state.'),
('Timeout zero', 'full put or empty get with timeout 0', 'immediate `TimeoutError`', 'Zero is a nonblocking attempt.'),
('Drain/cancel', 'close with items present', 'drain serves them; cancel returns/removes them', 'Shutdown policy is explicit and first call wins.'),
('Race safety', 'competing producers/consumers plus spurious wakeups', 'no loss/duplication; deadline budget not reset', 'Concurrency tests target schedules, not only values.'),
],
}

OUTPUT_FALLBACKS = {
    39: 'Return the exact Boolean value defined by the fully parsed policy, or raise `ValueError` for malformed or over-budget input.',
    40: 'Accept or reject each event against the watermark and emit every newly closed, nonempty window exactly once in start order.',
    42: 'Preserve FIFO and bounded capacity while giving every put, get, timeout, drain, and cancellation race the documented outcome.',
}

def render(number, output):
    rows = '\n'.join(f'| {case} | {given} | {expected} | {reason} |'
                     for case, given, expected, reason in CASES[number])
    return f'''{START}

## What the interviewer expects

The opening scenario is the product context; the table above is the callable
contract. Your job is to connect them. Before coding, say what the output means,
walk one normal case and one case that could disprove a tempting shortcut, then
name the invariant your implementation will preserve. Start with a correct
baseline, improve it deliberately, and derive time and space from actual work.

**Done means:** {output.rstrip('.')}.

Passing the happy path alone is not done; your answer
must make a deliberate decision for every scenario below without mutating input
unless the contract explicitly permits it.

### Test-case scenarios to settle before coding

| Case | Exact input or state | Expected result | What it is testing |
|---|---|---|---|
{rows}

Do not merely list these cases in an interview. For each one, point to the branch,
state transition, or invariant that makes the expected result inevitable. If your
design cannot explain a row, the design is not finished yet.

{END}'''

def main():
    bank = json.loads((ROOT/'indexes/problem-bank.json').read_text())
    assert {item['number'] for item in bank} == set(CASES)
    for item in bank:
        path = ROOT/item['path']
        text = path.read_text()
        output_match = re.search(r'^\| Output \| (.+?) \|$', text, re.M)
        if not output_match and item['number'] not in OUTPUT_FALLBACKS:
            raise RuntimeError(f'No output contract in {path}')
        output = output_match.group(1) if output_match else OUTPUT_FALLBACKS[item['number']]
        block = render(item['number'], output)
        if START in text:
            text = re.sub(re.escape(START)+r'.*?'+re.escape(END), block, text, flags=re.S)
        else:
            lines = text.splitlines()
            start = next(i for i,line in enumerate(lines) if line.startswith('| Contract |'))
            end = start
            while end+1 < len(lines) and lines[end+1].startswith('|'):
                end += 1
            lines[end+1:end+1] = ['', block]
            text = '\n'.join(lines) + ('\n' if text.endswith('\n') else '')
        path.write_text(text)
    print(f'Updated {len(bank)} coding problem briefs with explicit expectations and edge cases.')

if __name__ == '__main__':
    main()
