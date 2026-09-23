"""Deterministic topological order with duplicate-edge normalization."""
from collections import deque


def dependency_order(tasks, dependencies):
    """dependencies contains (prerequisite, dependent); cycles raise ValueError."""
    tasks = list(tasks)
    if len(set(tasks)) != len(tasks):
        raise ValueError("duplicate task")
    dependents = {task: [] for task in tasks}
    remaining_prerequisites = dict.fromkeys(tasks, 0)
    unique_edges = set()
    for before, after in dependencies:
        if before not in dependents or after not in dependents:
            raise ValueError("unknown task")
        if (before, after) not in unique_edges:
            unique_edges.add((before, after))
            dependents[before].append(after)
            remaining_prerequisites[after] += 1
    ready = deque(task for task in tasks if remaining_prerequisites[task] == 0)
    result = []
    while ready:
        task = ready.popleft()
        result.append(task)
        for child in dependents[task]:
            remaining_prerequisites[child] -= 1
            if remaining_prerequisites[child] == 0:
                ready.append(child)
    if len(result) != len(tasks):
        raise ValueError("dependency cycle")
    return result
