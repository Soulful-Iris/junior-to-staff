"""Days until a strictly warmer temperature, using unresolved indices."""


def daily_temperatures(temperatures):
    temperatures = list(temperatures)
    if any(not isinstance(t, int) for t in temperatures):
        raise ValueError("integer temperatures required")
    answer = [0] * len(temperatures)
    stack = []
    for today, temperature in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < temperature:
            previous = stack.pop()
            answer[previous] = today - previous
        stack.append(today)
    return answer
