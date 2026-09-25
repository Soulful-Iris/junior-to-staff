import heapq


def network_delay(n, links, source):
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError("n must be a positive int")
    if not (1 <= source <= n):
        raise ValueError("source outside 1..n")
    adjacency = {node: [] for node in range(1, n + 1)}
    for u, v, w in links:
        if not (1 <= u <= n and 1 <= v <= n):
            raise ValueError(f"link {(u, v, w)} names an unknown node")
        if w < 0:
            raise ValueError("negative link time")
        adjacency[u].append((v, w))
    best = {source: 0}
    heap = [(0, source)]
    while heap:
        dist, node = heapq.heappop(heap)
        if dist > best.get(node, float("inf")):
            continue
        for neighbour, weight in adjacency[node]:
            candidate = dist + weight
            if candidate < best.get(neighbour, float("inf")):
                best[neighbour] = candidate
                heapq.heappush(heap, (candidate, neighbour))
    if len(best) < n:
        return None
    return max(best.values())
