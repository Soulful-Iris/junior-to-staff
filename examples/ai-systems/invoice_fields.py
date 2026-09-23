"""The bounded invoice grammar is an application contract, not a model decision."""
import re


def source_total(source):
    """Return (exact evidence, integer cents), or None for review.

    Exactly one standalone TOTAL marker is permitted. Its field runs until a
    semicolon, line ending, or EOF, and must be TOTAL USD digits.two_digits.
    Prefix prose and other fields are allowed; unsupported suffixes are not.
    """
    markers = list(re.finditer(r"(?<!\w)TOTAL(?!\w)", source))
    if len(markers) != 1:
        return None
    field = re.split(r"[;\r\n]", source[markers[0].start():], maxsplit=1)[0].rstrip(" \t")
    match = re.fullmatch(r"TOTAL[ \t]+USD[ \t]+([0-9]{1,6})\.([0-9]{2})", field)
    if match is None:
        return None
    value = int(match[1]) * 100 + int(match[2])
    return (field, value) if 0 < value <= 100000 else None
