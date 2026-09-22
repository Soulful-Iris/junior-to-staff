"""Deterministic topological order with duplicate-edge normalization."""
from collections import deque


def dependency_order(tasks, dependencies):
    """dependencies contains (prerequisite, dependent); cycles raise ValueError."""
    tasks = list(tasks)
    if len(set(tasks)) != len(tasks):
        raise ValueError("duplicate task")
    children = {task: [] for task in tasks}
    indegree = dict.fromkeys(tasks, 0)
    seen = set()
    for before, after in dependencies:
        if before not in children or after not in children:
            raise ValueError("unknown task")
        if (before, after) not in seen:
            seen.add((before, after))
            children[before].append(after)
            indegree[after] += 1
    ready = deque(task for task in tasks if indegree[task] == 0)
    result = []
    while ready:
        task = ready.popleft()
        result.append(task)
        for child in children[task]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    if len(result) != len(tasks):
        raise ValueError("dependency cycle")
    return result
