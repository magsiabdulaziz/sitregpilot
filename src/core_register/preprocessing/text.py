"""Lexical text view (methodology section 4): NFKC, URL/e-mail masking, lowercase, D-06 window.

The raw text is never modified on disk; this builds a derived string for lexical models only.
"""

from __future__ import annotations

import re
import unicodedata

URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
URL_TOKEN = " URLTOKEN "
EMAIL_TOKEN = " EMAILTOKEN "


def lexical_view(text: str, window_words: int, *, unicode: str = "NFKC", lowercase: bool = True,
                 mask_urls_emails: bool = True) -> str:
    out = unicodedata.normalize(unicode, text)  # type: ignore[arg-type]
    if mask_urls_emails:
        out = EMAIL_RE.sub(EMAIL_TOKEN, out)
        out = URL_RE.sub(URL_TOKEN, out)
    if lowercase:
        out = out.lower()
    return " ".join(out.split()[:window_words])
