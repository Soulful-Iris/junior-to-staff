"""Identify the actual local classifier code, prompt and configured model."""
import hashlib
import os
from pathlib import Path

from storage import fingerprint


def manifest(model):
    root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for name in ("app.py", "models.py", "storage.py", "invoice_fields.py", "candidate.py"):
        digest.update(name.encode() + b"\0" + (root / name).read_bytes())
    # A release build can supply its commit; byte identity is checked regardless.
    return {"source_commit": os.getenv("AI_SOURCE_COMMIT"),
            "source_sha256": digest.hexdigest(),
            "prompt_sha256": fingerprint(model.instructions["classify"]),
            "model_identifier": model.version,
            "inference_config": dict(model.inference_config),
            "retrieval_version": "none-classifier-v1", "policy": "demo-gate-v1"}
