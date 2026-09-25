import heapq


class CycleError(ValueError):
    def __init__(self, cycle):
        super().__init__(f"dependency cycle: {' -> '.join(map(str, cycle))}")
        self.cycle = cycle


def order(tasks, edges):
    tasks = list(tasks)
    known = set(tasks)
    if len(known) != len(tasks):
        raise ValueError("duplicate task names")
    dependents = {t: set() for t in tasks}
    for prerequisite, dependent in edges:
        if prerequisite not in known or dependent not in known:
            raise ValueError(f"unknown task in edge {(prerequisite, dependent)}")
        dependents[prerequisite].add(dependent)
    indegree = {t: 0 for t in tasks}
    for prerequisite in tasks:
        for dependent in dependents[prerequisite]:
            indegree[dependent] += 1
    ready = [t for t in tasks if indegree[t] == 0]
    heapq.heapify(ready)
    result = []
    while ready:
        task = heapq.heappop(ready)
        result.append(task)
        for dependent in dependents[task]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(ready, dependent)
    if len(result) == len(tasks):
        return result
    remaining = {t for t in tasks if indegree[t] > 0}
    prerequisites = {t: [p for p in remaining if t in dependents[p]] for t in remaining}
    start = min(remaining)
    path, seen = [], {}
    node = start
    while node not in seen:
        seen[node] = len(path)
        path.append(node)
        node = min(prerequisites[node])
    # The walk followed prerequisite edges backwards; reverse so pairs are forward edges.
    cycle = list(reversed(path[seen[node]:] + [node]))
    raise CycleError(cycle)
