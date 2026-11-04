"""Streaming ingestion of the released CORE TSV files.

Format (verified in the Phase 1 audit): one record per ``\\n``-terminated line,
three tab-separated fields ``labels <TAB> id <TAB> text``, UTF-8, no header,
no quoting. The file is read in binary and split on ``\\n`` only, so other
characters (e.g. ``\\r``, U+2028) can never start a new record. The text is
everything after the second tab and is preserved byte-for-byte; a trailing
``\\r`` before the newline is treated as line-ending, not text. A bare ``\\r``
inside a line stays in the text (the stdlib reference audit, which reads in text
mode, would split there instead; the released corpus contains none, as checked in
the PR #14 review). Document IDs are not format-checked beyond being non-empty:
all released IDs are 7-digit strings (Phase 1 audit).
"""

from __future__ import annotations

import gzip
import hashlib
from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from core_register.config import Split
from core_register.data.labels import LabelSchema, parse_label_string


class Status(StrEnum):
    """Row status, in order of precedence (first matching rule wins)."""

    MALFORMED = "MALFORMED"  # not UTF-8, fewer than 3 tab-separated fields, or empty ID field
    UNKNOWN_CODE = "UNKNOWN_CODE"  # label problem: a code not in the schema, or no code at all
    EMPTY_INPUT = "EMPTY_INPUT"  # text empty or whitespace-only: never classified
    OK = "OK"


_MAX_ISSUE_CHARS = 80  # issue strings may echo label tokens; keep them short in any manifest


@dataclass(frozen=True)
class Record:
    doc_id: str  # always a string: leading zeros are significant
    split: Split
    source_file: str
    line_no: int  # 1-based physical line in the decompressed file
    raw_labels: str  # exactly as released
    labels: tuple[str, ...]  # set semantics, schema order
    unknown_codes: tuple[str, ...]
    text: str
    text_sha256: str
    n_ws_words: int  # whitespace tokens (str.split); NOT a linguistic token count
    status: Status
    issue: str = ""


def _strip_eol(line: bytes) -> bytes:
    if line.endswith(b"\n"):
        line = line[:-1]
    if line.endswith(b"\r"):
        line = line[:-1]
    return line


def iter_records(path: Path, split: Split, schema: LabelSchema) -> Iterator[Record]:
    """Yield one Record per physical line. Never raises on bad rows: they get a status."""
    with gzip.open(path, "rb") as f:
        for line_no, raw_line in enumerate(f, start=1):
            body = _strip_eol(raw_line)
            try:
                decoded = body.decode("utf-8")
            except UnicodeDecodeError as exc:
                yield _malformed(path, split, line_no, f"invalid UTF-8 at byte {exc.start}")
                continue
            parts = decoded.split("\t", 2)
            if len(parts) < 3:
                yield _malformed(path, split, line_no, f"{len(parts)} tab-separated field(s), expected 3")
                continue
            raw_labels, doc_id, text = parts
            if doc_id == "":
                yield _malformed(path, split, line_no, "empty document ID field")
                continue
            parsed = parse_label_string(raw_labels, schema)
            if parsed.unknown or not parsed.labels:
                status = Status.UNKNOWN_CODE
                issue = f"unknown codes: {list(parsed.unknown)}" if parsed.unknown else "no label code"
                issue = issue[:_MAX_ISSUE_CHARS]
            elif text.strip() == "":
                status, issue = Status.EMPTY_INPUT, ""
            else:
                status, issue = Status.OK, ""
            yield Record(
                doc_id=doc_id,
                split=split,
                source_file=path.name,
                line_no=line_no,
                raw_labels=raw_labels,
                labels=parsed.labels,
                unknown_codes=parsed.unknown,
                text=text,
                text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                n_ws_words=len(text.split()),
                status=status,
                issue=issue,
            )


def _malformed(path: Path, split: Split, line_no: int, issue: str) -> Record:
    return Record(
        doc_id="",
        split=split,
        source_file=path.name,
        line_no=line_no,
        raw_labels="",
        labels=(),
        unknown_codes=(),
        text="",
        text_sha256="",
        n_ws_words=0,
        status=Status.MALFORMED,
        issue=issue,
    )
