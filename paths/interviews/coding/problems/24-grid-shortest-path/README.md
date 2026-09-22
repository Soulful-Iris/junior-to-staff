# 24 · Shortest path through a grid

> “Our warehouse viewer marks open cells and shelves. A picker moves one cell
> north, south, east, or west, with each move costing one step. Return the shortest
> route between two positions without changing the displayed map. What happens
> if a position is blocked or no route exists?”

Constructed practice question. Prerequisite: [BFS](../../lessons/05-graphs.md).
A cell `(row,column)` is a graph vertex; legal adjacent moves are edges. The grid
supplies neighbors implicitly, so no separate adjacency list is necessary.

| Contract | Required behavior |
|---|---|
| Input | Nonempty rectangular 0/1 grid; two in-bounds integer coordinates |
| Output | Endpoint-inclusive shortest coordinate list; any shortest route accepted |
| Boundaries | 0 is open; 1 is wall; blocked/unreachable endpoints return `[]` |
| Failure | Empty/ragged grid, other cell values, or out-of-bounds endpoints raise `ValueError` |
| Scope | No diagonal moves, weighted terrain, moving walls, or input mutation |

For rows `[[0,1,0],[0,1,0],[0,0,0]]`, start `(0,0)` and goal `(0,2)` require six
moves around the shelf. The path is `[(0,0),(1,0),(2,0),(2,1),(2,2),(1,2),(0,2)]`.
In `[[0,1,0]]` the same endpoints are unreachable. Ask whether distance alone
would suffice: route output requires retaining reconstruction information.

```mermaid
flowchart TD
  S["start 0,0"] -->|"down"| A["1,0"]
  A -->|"down"| B["2,0"]
  B -->|"right"| C["2,1"]
  C -->|"right"| D["2,2"]
  D -->|"up"| E["1,2"]
  E -->|"up"| G["goal 0,2"]
```

Before reading further, hand-label each open cell with its shortest distance from
the start. Then implement a path-returning solution and test start equals goal.

<details>
<summary>Solution, distance layers, and follow-ups</summary>

Enumerating every simple route and keeping the shortest is a correct baseline but
can explore exponentially many routes on an open grid. Greedily moving toward
the goal fails immediately on the pictured shelf: the first required move increases
Manhattan distance. DFS's first path is also not necessarily shortest.

Use a FIFO queue and a parent map. Insert the start with no parent. When visiting
a cell, generate the four neighbors, discard outside/wall/discovered positions,
record the parent, and enqueue. On reaching the goal, follow parent links backward
and reverse. Never mark the input grid, because the caller still displays it.

**Invariant:** cells leave the queue in nondecreasing distance, and each saved
parent is one step closer to the start. First discovery is shortest because no
later parent can have a smaller distance. Mark on enqueue to bound the frontier;
otherwise two neighboring cells can enqueue the same position repeatedly.

| Grid row | Column 0 distance | Column 1 | Column 2 distance |
|---|---:|---|---:|
| 0 | 0 | wall | 6 |
| 1 | 1 | wall | 5 |
| 2 | 2 | 3 | 4 |

For R rows and C columns, validation/search take O(RC) time. Parent map and queue
use O(RC) auxiliary space in the worst case; the returned route uses O(P) for P
cells. Copying a full path into every queue entry would add avoidable path-length
cost. Parent pointers retain exactly the information reconstruction needs.

**Follow-up 1 — allow diagonal moves.** Predict the new shortest distance. If
corner cutting is allowed, the pictured route drops to four moves through the
bottom middle cell. If diagonals may not pass between a shelf and a boundary,
neighbor generation must check the adjacent orthogonal cells too. Define this
policy before changing the algorithm.

```mermaid
flowchart TD
  S["0,0"] -->|"down"| A["1,0"]
  A -->|"diagonal; corner policy required"| B["2,1"]
  B -->|"diagonal"| C["1,2"]
  C -->|"up"| G["0,2"]
```

**Follow-up 2 — terrain costs vary.** FIFO layers now measure moves, not cost. Use
[Dijkstra](../25-weighted-shortest-path/README.md) for nonnegative costs and define
whether cost belongs to entering a cell or traversing an edge. A* may reduce
exploration with an admissible heuristic; the correctness claim must name that
heuristic and the movement rules.

Senior depth is connecting neighbor policy, the shortestness proof, and tests for
mutation/unreachability. Lead depth adds map-version consistency for live requests.

Reference: [solution.py](solution.py); tests verify a forced detour, open-grid
distance, unchanged input, blocked endpoints, and malformed maps.

```bash
python -m unittest discover -s paths/interviews/coding/problems/24-grid-shortest-path -p 'test_*.py'
```

</details>
