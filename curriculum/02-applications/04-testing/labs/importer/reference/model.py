"""Domain validation: cents are integers; malformed pages have no partial effect."""
from decimal import Decimal, InvalidOperation


def normalize(item):
    if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
        raise ValueError("id required")
    if item.get("currency") != "USD" or not isinstance(item.get("amount"), str) or len(item["amount"]) > 128:
        raise ValueError("USD amount must be a decimal string")
    try:
        amount = Decimal(item["amount"])
        if not amount.is_finite():
            raise ValueError("whole cents required")
        if amount.copy_abs() > Decimal("10000000000"):
            raise ValueError("amount out of range")
        # Never multiply under Decimal's ambient context: it can round away a tiny
        # fractional cent. The parsed coefficient and exponent are exact.
        sign, digits, exponent = amount.as_tuple()
        coefficient = 0
        for digit in digits:
            coefficient = coefficient * 10 + digit
        if not coefficient:
            cents = 0
        elif exponent >= -2:
            cents = coefficient * 10 ** (exponent + 2)
        else:
            places = -exponent - 2
            if places > len(digits):
                raise ValueError("whole cents required")
            cents, fraction = divmod(coefficient, 10 ** places)
            if fraction:
                raise ValueError("whole cents required")
        return (item["id"], -cents if sign else cents, "USD")
    except InvalidOperation as exc:
        raise ValueError("invalid amount") from exc


def page(body):
    if not isinstance(body, dict) or not isinstance(body.get("items"), list):
        raise ValueError("items list required")
    if "nextCursor" not in body or (body["nextCursor"] is not None and
                                      (not isinstance(body["nextCursor"], str) or not body["nextCursor"])):
        raise ValueError("opaque cursor or null required")
    return [normalize(item) for item in body["items"]], body["nextCursor"]
