"""Password lock for the private track.

Locked pages are published as ciphertext only. The browser derives a key from
the password with PBKDF2-SHA256, checks an HMAC-SHA256 tag, and decrypts with
a keystream produced by PBKDF2 with a single iteration, which is HMAC-SHA256
in counter mode. Every primitive is in Python's standard library and in every
browser's WebCrypto API, so the build gains no dependency.

The plain HTML never contains the locked text, titles, or links. What a crawler
sees is a blurred placeholder, an unlock form, and base64 noise.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets

from bs4 import BeautifulSoup

PASSWORD = os.environ.get("J2S_TRACK_PASSWORD", "hello123")
SALT = b"engineering-guide:private-track:v1"   # fixed, so a saved unlock survives rebuilds
ITERATIONS = 120_000
CHUNK = 32_768
GROUP = "crowdstrike"
MARKERS = ("crowdstrike",)
BLOCKS = {"tr", "li", "p", "h1", "h2", "h3", "h4", "blockquote", "figure", "dd", "dt", "pre"}


def is_locked(page: dict) -> bool:
    return page.get("group") == GROUP


def keys(password: str = PASSWORD) -> bytes:
    """64 bytes: the first half encrypts, the second half authenticates."""
    return hashlib.pbkdf2_hmac("sha256", password.encode(), SALT, ITERATIONS, 64)


def keystream(enc_key: bytes, nonce: bytes, length: int) -> bytes:
    out = bytearray()
    chunk = 0
    while len(out) < length:
        n = min(CHUNK, length - len(out))
        out += hashlib.pbkdf2_hmac("sha256", enc_key, nonce + chunk.to_bytes(4, "big"), 1, n)
        chunk += 1
    return bytes(out)


def _xor(a: bytes, b: bytes) -> bytes:
    return (int.from_bytes(a, "big") ^ int.from_bytes(b, "big")).to_bytes(len(a), "big")


def seal(text: str, key_bytes: bytes | None = None) -> str:
    key_bytes = key_bytes or key()
    data = text.encode()
    nonce = secrets.token_bytes(16)
    cipher = _xor(data, keystream(key_bytes[:32], nonce, len(data)))
    tag = hmac.new(key_bytes[32:], nonce + cipher, "sha256").digest()
    return base64.b64encode(nonce + tag + cipher).decode()


def open_blob(blob: str, key_bytes: bytes | None = None) -> str:
    key_bytes = key_bytes or key()
    raw = base64.b64decode(blob)
    nonce, tag, cipher = raw[:16], raw[16:48], raw[48:]
    if not hmac.compare_digest(tag, hmac.new(key_bytes[32:], nonce + cipher, "sha256").digest()):
        raise ValueError("wrong key for locked content")
    return _xor(cipher, keystream(key_bytes[:32], nonce, len(cipher))).decode()


_KEY: bytes | None = None
_sealed: dict[str, str] = {}


def key() -> bytes:
    global _KEY
    if _KEY is None:
        _KEY = keys()
    return _KEY


def seal_cached(text: str) -> str:
    """The rail repeats on every page; identical text gets one ciphertext."""
    digest = hashlib.sha256(text.encode()).hexdigest()
    if digest not in _sealed:
        _sealed[digest] = seal(text)
    return _sealed[digest]


GLYPH = ('<svg viewBox="0 0 16 16" width="11" height="11" aria-hidden="true" focusable="false">'
         '<rect x="3" y="7" width="10" height="8" rx="1.8" fill="currentColor"/>'
         '<path d="M5.2 7V5.2a2.8 2.8 0 0 1 5.6 0V7" fill="none" stroke="currentColor" stroke-width="1.7"/></svg>')


def widget(blob: str, mode: str, veil: str, variant: str = "") -> str:
    """A lock in the page.

    mode 'page': the blob is a whole document and replaces this one.
    mode 'replace': the blob replaces this element.
    veil: decoy markup shown blurred behind the form; it carries no real content.
    """
    return (f'<div class="track-lock {variant}" data-lock="{mode}">'
            f'<div class="track-lock-veil" aria-hidden="true">{veil}</div>'
            '<form class="track-lock-form" autocomplete="off">'
            f'<span class="track-lock-eyebrow">{GLYPH} PRIVATE TRACK</span>'
            '<div class="track-lock-row"><label><span class="sr-only">Password</span>'
            '<input type="password" name="password" placeholder="Password" required '
            'autocapitalize="off" spellcheck="false"></label>'
            '<button type="submit">Unlock</button></div>'
            '<p class="track-lock-note" aria-live="polite">Locked. The password opens it and stays unlocked on this device.</p>'
            '</form>'
            f'<script type="text/plain" class="track-lock-blob">{blob}</script></div>')


RAIL_VEIL = ('<div class="toc-part-heading"><span class="part-label">ITS OWN LEAGUE</span>'
             '<span class="part-title">Private track</span></div>'
             '<span class="toc-link part-intro">Start here · the track</span>'
             + ''.join(f'<div class="toc-chapter veil-row"><span class="chapter-number"><small>T</small> {n}</span>'
                       f'<span class="chapter-title">{t}</span><span class="chevron" aria-hidden="true">›</span></div>'
                       for n, t in ((1, "Locked chapter, first of three"), (2, "Locked chapter, second of three"),
                                    (3, "Locked chapter, third of three"))))

PAGE_VEIL = ('<h1>Private lesson</h1><p class="chapter-lede">This page belongs to a private track. '
             'The password opens the text, the diagrams, the worked problems, and the design cases.</p>'
             '<p>Nothing on this page is readable until it is unlocked. The unlock is saved on this device, '
             'so the next page in the track opens without asking again.</p>'
             '<h2>What the track holds</h2><p>A preparation chapter, a coding chapter, and an architecture '
             'chapter, each with its own lessons and worked examples. The table of contents on the left '
             'opens with the same password.</p><p>If the password does not work, ask the person who shared '
             'this site with you.</p>')

CARD_VEIL = ('<span class="veil-card"><span>PRIVATE TRACK</span><strong>Locked</strong>'
             '<small>Enter the password to open this path on this device.</small></span>')


def redact_html(fragment: str) -> str:
    """Remove every block on a public page that names or links the locked track."""
    lowered = fragment.lower()
    if not any(m in lowered for m in MARKERS):
        return fragment
    soup = BeautifulSoup(fragment, "html.parser")

    def names_track(el) -> bool:
        text = el.get_text(" ").lower()
        if any(m in text for m in MARKERS):
            return True
        for a in el.find_all(["a", "img"]):
            target = (a.get("href") or a.get("src") or "").lower()
            if any(m in target for m in MARKERS):
                return True
        return False

    doomed = []
    for el in soup.find_all(BLOCKS):
        if not names_track(el):
            continue
        if any(names_track(child) for child in el.find_all(BLOCKS)):
            continue
        doomed.append(el)
    for el in doomed:
        el.decompose()
    for table in soup.find_all("table"):
        if not table.find("td"):
            wrapper = table.parent if table.parent and table.parent.name == "div" and len(table.parent.find_all(recursive=False)) == 1 else None
            (wrapper or table).decompose()
    for lst in soup.find_all(["ul", "ol"]):
        if not lst.find("li"):
            lst.decompose()
    return str(soup)


def redact_text(text: str) -> str:
    """Drop sentences that name the track from search text."""
    return re.sub(r"[^.\n]*(?:" + "|".join(MARKERS) + r")[^.\n]*[.\n]?", " ", text, flags=re.I)


def redact_json(text: str) -> str:
    """Drop entries that name the track from copied JSON registries."""
    def clean(node):
        if isinstance(node, list):
            return [clean(item) for item in node if not any(m in json.dumps(item).lower() for m in MARKERS)]
        if isinstance(node, dict):
            return {k: clean(v) for k, v in node.items()}
        return node
    return json.dumps(clean(json.loads(text)), indent=2) + "\n"


def mentions(text: str) -> bool:
    lowered = text.lower()
    return any(m in lowered for m in MARKERS)
