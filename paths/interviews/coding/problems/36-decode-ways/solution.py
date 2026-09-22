"""Count 1..26 decodings; 0 cannot stand alone and pairs cannot start with 0."""


def decode_ways(digits):
    if not isinstance(digits, str) or any(c not in '0123456789' for c in digits):
        raise ValueError("ASCII digit string required")
    if not digits:
        return 0
    two_back, one_back = 1, int(digits[0] != '0')
    for i in range(1, len(digits)):
        current = one_back if digits[i] != '0' else 0
        if '10' <= digits[i - 1:i + 1] <= '26':
            current += two_back
        two_back, one_back = one_back, current
    return one_back
