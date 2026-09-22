"""Find an orthogonal word path without reusing cells or changing the board."""


def word_search(board, word):
    if any(len(row) != (len(board[0]) if board else 0) for row in board):
        raise ValueError("rectangular board required")
    if any(not isinstance(c, str) or len(c) != 1 for row in board for c in row):
        raise ValueError("single-character cells required")
    if not isinstance(word, str):
        raise ValueError("word must be a string")
    if not word:
        return True
    if not board or not board[0] or len(word) > len(board) * len(board[0]):
        return False
    rows, cols = len(board), len(board[0])
    directions = ((1, 0), (0, 1), (-1, 0), (0, -1))
    for row in range(rows):
        for col in range(cols):
            if board[row][col] != word[0]:
                continue
            visited = {(row, col)}
            # Frame: row, col, next direction. Stack depth is matched length.
            stack = [[row, col, 0]]
            while stack:
                if len(stack) == len(word):
                    return True
                r, c, direction = stack[-1]
                if direction == 4:
                    stack.pop()
                    visited.remove((r, c))
                    continue
                stack[-1][2] += 1
                dr, dc = directions[direction]
                neighbor = nr, nc = r + dr, c + dc
                if (0 <= nr < rows and 0 <= nc < cols and neighbor not in visited
                        and board[nr][nc] == word[len(stack)]):
                    visited.add(neighbor)
                    stack.append([nr, nc, 0])
    return False
