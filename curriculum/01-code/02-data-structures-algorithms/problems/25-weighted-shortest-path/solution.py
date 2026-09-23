"""Dijkstra with a lazy heap, stale-entry rejection, and path reconstruction."""
import heapq
import math
from itertools import count


def weighted_shortest_path(graph, source, target):
    """Return a cheapest path; raise OverflowError on an unrepresentable sum.

    Integer-only routes retain arbitrary precision. Float routes use Python
    float precision; every evaluated relaxation must have a finite result.
    """
    if source not in graph or target not in graph:
        raise ValueError("missing endpoint")
    for edges in graph.values():
        for neighbor, weight in edges:
            if neighbor not in graph or type(weight) not in (int, float):
                raise ValueError("invalid edge")
            if (isinstance(weight, float) and not math.isfinite(weight)) or weight < 0:
                raise ValueError("finite nonnegative weights required")
    distance = {source: 0}
    root_marker = object()
    parent = {source: root_marker}
    sequence = count()
    heap = [(0, next(sequence), source)]
    while heap:
        cost, _, vertex = heapq.heappop(heap)
        if cost != distance[vertex]:
            continue
        if vertex == target:
            path = [vertex]
            while parent[path[-1]] is not root_marker:
                path.append(parent[path[-1]])
            return cost, path[::-1]
        for neighbor, weight in graph[vertex]:
            try:
                new_cost = cost + weight
            except OverflowError as exc:
                raise OverflowError("path cost is not representable") from exc
            if isinstance(new_cost, float) and not math.isfinite(new_cost):
                raise OverflowError("path cost is not representable")
            if new_cost < distance.get(neighbor, math.inf):
                distance[neighbor] = new_cost
                parent[neighbor] = vertex
                heapq.heappush(heap, (new_cost, next(sequence), neighbor))
    return math.inf, []
