def count_islands(grid):
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])
    for row in grid:
        if len(row) != cols:
            raise ValueError("grid rows must have equal length")
        for cell in row:
            if cell not in (0, 1) or isinstance(cell, bool):
                raise ValueError("cells must be 0 or 1")
    visited = [[False] * cols for _ in range(rows)]
    count = 0
    for r0 in range(rows):
        for c0 in range(cols):
            if grid[r0][c0] != 1 or visited[r0][c0]:
                continue
            count += 1
            visited[r0][c0] = True
            stack = [(r0, c0)]
            while stack:
                r, c = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1 and not visited[nr][nc]:
                        visited[nr][nc] = True
                        stack.append((nr, nc))
    return count
