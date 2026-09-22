"""Four-direction unit-cost BFS; input is never changed."""
from collections import deque


def shortest_grid_path(grid, start, goal):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("nonempty rectangular grid required")
    rows, cols = len(grid), len(grid[0])
    if any(cell not in (0, 1) for row in grid for cell in row):
        raise ValueError("cells must be 0 (open) or 1 (wall)")
    for point in (start, goal):
        if (len(point) != 2 or any(not isinstance(x, int) for x in point)
                or not 0 <= point[0] < rows or not 0 <= point[1] < cols):
            raise ValueError("endpoint outside grid")
    start, goal = tuple(start), tuple(goal)
    if grid[start[0]][start[1]] or grid[goal[0]][goal[1]]:
        return []
    queue = deque([start])
    parent = {start: None}
    while queue:
        cell = queue.popleft()
        if cell == goal:
            path = [cell]
            while parent[path[-1]] is not None:
                path.append(parent[path[-1]])
            return path[::-1]
        r, c = cell
        for nr, nc in ((r + 1, c), (r, c + 1), (r - 1, c), (r, c - 1)):
            neighbor = (nr, nc)
            if (0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0
                    and neighbor not in parent):
                parent[neighbor] = cell
                queue.append(neighbor)
    return []
