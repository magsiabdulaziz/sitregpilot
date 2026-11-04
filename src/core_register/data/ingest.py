"""Streaming ingestion of the released CORE TSV files.

Format (verified in the Phase 1 audit): one record per ``\\n``-terminated line,
three tab-separated fields ``labels <TAB> id <TAB> text``, UTF-8, no header,
no quoting. The file is read in binary and split on ``\\n`` only, so other
characters (e.g. ``\\r``, U+2028) can never start a new record. The text is
everything after the second tab and is preserved byte-for-byte; a trailing
``\\r`` before the newline is treated as line-ending, not text.
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
    OK = "OK"
    EMPTY_INPUT = "EMPTY_INPUT"  # well-formed row with empty text: never classified
    UNKNOWN_CODE = "UNKNOWN_CODE"  # label field empty or contains a code not in the schema
    MALFORMED = "MALFORMED"  # not UTF-8, or fewer than 3 tab-separated fields


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
            parsed = parse_label_string(raw_labels, schema)
            if parsed.unknown or not parsed.labels:
                status, issue = Status.UNKNOWN_CODE, (
                    f"unknown codes: {list(parsed.unknown)}" if parsed.unknown else "empty label field"
                )
            elif text == "":
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
