"""Source-file integrity checks, run before any corpus file is read."""

from __future__ import annotations

import hashlib
from pathlib import Path

from core_register.config import DataConfig


class SourceIntegrityError(RuntimeError):
    """A source file is missing or its hash does not match the pinned value."""


def sha256_file(path: Path, block_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            h.update(block)
    return h.hexdigest()


def verify_source_files(cfg: DataConfig) -> dict[str, str]:
    """Hash every configured file (splits and legend). Read-only.

    Returns {file name: observed sha256}. Raises SourceIntegrityError on a
    missing file or, when ``cfg.verify_hashes`` is true, on any mismatch.
    """
    names = [*cfg.files.values(), cfg.legend_file]
    observed: dict[str, str] = {}
    for name in names:
        path = cfg.raw_dir / name
        if not path.is_file():
            raise SourceIntegrityError(f"missing source file: {path}")
        observed[name] = sha256_file(path)
    if cfg.verify_hashes:
        bad = {
            n: (cfg.expected_sha256[n], observed[n])
            for n in names
            if n in cfg.expected_sha256 and cfg.expected_sha256[n] != observed[n]
        }
        if bad:
            details = "; ".join(f"{n}: expected {e[:12]}…, got {o[:12]}…" for n, (e, o) in bad.items())
            raise SourceIntegrityError(f"sha256 mismatch: {details}")
    return observed
