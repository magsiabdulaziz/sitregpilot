"""Typed configuration. Unknown keys are rejected (``extra="forbid"``).

Relative paths in a config file are resolved against the current working
directory; run commands from the repository root.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator, model_validator

Split = Literal["train", "dev", "test"]
SPLITS: tuple[Split, ...] = ("train", "dev", "test")

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DataConfig(StrictModel):
    """Location and integrity of the released CORE files."""

    raw_dir: Path
    files: dict[Split, str]
    expected_sha256: dict[str, str] = Field(description="file name -> lowercase hex sha256")
    legend_file: str = "register_label_abbreviations.txt"
    label_schema: Path
    verify_hashes: StrictBool = True  # a YAML string such as "yes" is rejected, not coerced

    @field_validator("expected_sha256")
    @classmethod
    def _hex_digests(cls, v: dict[str, str]) -> dict[str, str]:
        for name, digest in v.items():
            if not _SHA256.match(digest):
                raise ValueError(f"expected_sha256[{name!r}] is not a lowercase 64-char hex digest")
        return v

    @model_validator(mode="after")
    def _consistent(self) -> DataConfig:
        missing_splits = set(SPLITS) - set(self.files)
        if missing_splits:
            raise ValueError(f"files is missing splits: {sorted(missing_splits)}")
        names = [*self.files.values(), self.legend_file]
        if len(set(names)) != len(names):
            raise ValueError(f"each split and the legend must use a distinct file: {names}")
        stray = sorted(set(self.expected_sha256) - set(names))
        if stray:
            raise ValueError(f"expected_sha256 has entries for unconfigured files: {stray}")
        if self.verify_hashes:
            unhashed = [f for f in (*self.files.values(), self.legend_file) if f not in self.expected_sha256]
            if unhashed:
                raise ValueError(f"verify_hashes=true but no expected_sha256 for: {unhashed}")
        return self

    def split_path(self, split: Split) -> Path:
        return self.raw_dir / self.files[split]


def load_data_config(path: Path) -> DataConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: top level must be a mapping")
    return DataConfig.model_validate(raw)
