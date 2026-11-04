"""Label schema loading and label-string parsing.

Labels are treated as sets (order in the release carries no meaning, see
ISS-003) and returned in the frozen schema order. Hierarchy information in the
schema is a *reference* only (D-03): nothing here adds or removes labels.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LabelSchema:
    version: str
    codes: tuple[str, ...]
    main: tuple[str, ...]
    sub: tuple[str, ...]
    other_code: str
    display_names: dict[str, str]

    @property
    def code_set(self) -> frozenset[str]:
        return frozenset(self.codes)

    def index(self, code: str) -> int:
        return self.codes.index(code)


@dataclass(frozen=True)
class ParsedLabels:
    labels: tuple[str, ...]  # known codes, de-duplicated, schema order
    unknown: tuple[str, ...]  # codes not in the schema, in order of appearance
    had_duplicates: bool


def load_label_schema(path: Path) -> LabelSchema:
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data["codes"]
    codes = tuple(e["code"] for e in entries)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{path}: duplicate codes in label schema")
    others = [e["code"] for e in entries if e["level"] == "annotation_outcome"]
    if len(others) != 1:
        raise ValueError(f"{path}: expected exactly one annotation_outcome code, found {others}")
    main_order = tuple(data["main_order_article"])
    main_set = {e["code"] for e in entries if e["level"] == "main"}
    if set(main_order) != main_set:
        raise ValueError(f"{path}: main_order_article does not match main-level codes")
    return LabelSchema(
        version=str(data["version"]),
        codes=codes,
        main=main_order,
        sub=tuple(e["code"] for e in entries if e["level"] == "sub"),
        other_code=others[0],
        display_names={e["code"]: e["display_name"] for e in entries},
    )


def parse_label_string(raw: str, schema: LabelSchema) -> ParsedLabels:
    tokens = raw.split()
    known = schema.code_set
    unknown = tuple(t for t in tokens if t not in known)
    present = {t for t in tokens if t in known}
    return ParsedLabels(
        labels=tuple(c for c in schema.codes if c in present),
        unknown=unknown,
        had_duplicates=len(tokens) != len(set(tokens)),
    )
