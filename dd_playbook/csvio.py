"""Small helpers for reading CSV files with clear error messages."""

from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path

from .errors import InputError


def read_bytes(path: Path, label: str) -> bytes:
    path = Path(path)
    if not path.exists():
        raise InputError(f"{label} not found: {path}")
    if path.is_dir():
        raise InputError(f"{label} is a folder, expected a CSV file: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise InputError(f"{label} could not be read ({path}): {exc.strerror or exc}")


def decode(raw: bytes, path: Path, label: str) -> str:
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError(
            f"{label} is not valid UTF-8 text ({path}). Save it as 'CSV UTF-8' and try again."
        )


def sha256_text(raw: bytes) -> str:
    """Hash with line endings normalised so the value is stable across platforms."""
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def read_rows(path: Path, label: str, required: list[str]) -> tuple[list[dict[str, str]], list[str], str]:
    """Return (rows, header, sha256). Row dictionaries have stripped values.

    Each row carries a hidden '_line' key with its line number in the file.
    """
    path = Path(path)
    raw = read_bytes(path, label)
    text = decode(raw, path, label)
    if not text.strip():
        raise InputError(f"{label} is empty: {path}")
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration:
        raise InputError(f"{label} is empty: {path}")
    header = [h.strip().lower() for h in header]
    missing = [c for c in required if c not in header]
    if missing:
        raise InputError(
            f"{label} is missing required column(s): {', '.join(missing)}. "
            f"Found columns: {', '.join(h for h in header if h) or '(none)'}."
        )
    problems = []
    dup = sorted({h for h in header if h and header.count(h) > 1})
    if dup:
        problems.append(f"{label} has duplicate column name(s): {', '.join(dup)}.")
        raise InputError(problems)
    rows: list[dict[str, str]] = []
    for line_no, rec in enumerate(reader, start=2):
        if not any(cell.strip() for cell in rec):
            continue
        row = {h: (rec[i].strip() if i < len(rec) else "") for i, h in enumerate(header)}
        row["_line"] = str(line_no)
        rows.append(row)
    return rows, header, sha256_text(raw)
