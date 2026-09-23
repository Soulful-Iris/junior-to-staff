"""Content identity and integrity checks for required diagram outputs."""
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

SCHEMA = 1


def key(code: str, inputs: dict) -> str:
    value = {"schema": SCHEMA, "code": code.replace("\r\n", "\n").strip(), "inputs": inputs}
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:32]


def valid_svg(path: Path) -> bool:
    try:
        root = ET.fromstring(path.read_bytes())
        if root.tag != "{http://www.w3.org/2000/svg}svg":
            return False
        box = [float(v) for v in root.get("viewBox", "").replace(",", " ").split()]
        return len(box) == 4 and all(map(math.isfinite, box)) and box[2] > 0 and box[3] > 0
    except (OSError, ValueError, ET.ParseError):
        return False
