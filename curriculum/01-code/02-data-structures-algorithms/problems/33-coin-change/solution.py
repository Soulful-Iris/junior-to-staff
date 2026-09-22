"""Minimum unbounded coin count with one optimal witness."""


def minimum_coins(coins, amount):
    if not isinstance(amount, int) or amount < 0:
        raise ValueError("nonnegative integer amount required")
    unique = set()
    for coin in coins:
        if not isinstance(coin, int) or coin <= 0:
            raise ValueError("positive integer coins required")
        unique.add(coin)
    coins = sorted(unique)
    unreachable = amount + 1
    best = [0] + [unreachable] * amount
    last = [None] * (amount + 1)
    for subtotal in range(1, amount + 1):
        for coin in coins:
            if coin > subtotal:
                break
            candidate = best[subtotal - coin] + 1
            if candidate < best[subtotal]:
                best[subtotal], last[subtotal] = candidate, coin
    if best[amount] == unreachable:
        return -1, []
    used = []
    remaining = amount
    while remaining:
        used.append(last[remaining])
        remaining -= last[remaining]
    return best[amount], used
