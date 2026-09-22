"""Dijkstra with a lazy heap, stale-entry rejection, and path reconstruction."""
import heapq
import math
from itertools import count


def weighted_shortest_path(graph, source, target):
    """graph maps every vertex to (neighbor, finite nonnegative weight) edges."""
    if source not in graph or target not in graph:
        raise ValueError("missing endpoint")
    for edges in graph.values():
        for neighbor, weight in edges:
            if neighbor not in graph or not isinstance(weight, (int, float)):
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
            new_cost = cost + weight
            if new_cost < distance.get(neighbor, math.inf):
                distance[neighbor] = new_cost
                parent[neighbor] = vertex
                heapq.heappush(heap, (new_cost, next(sequence), neighbor))
    return math.inf, []
