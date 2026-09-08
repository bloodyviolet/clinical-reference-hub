#!/usr/bin/env python3
"""Verify installed runtime packages exactly match requirements.lock."""
from __future__ import annotations
import importlib.metadata
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "requirements.lock"
_PATTERN = re.compile(r"^([A-Za-z0-9_.-]+)==([^;\s]+)$")


def expected_versions(path: Path = LOCK) -> dict[str, str]:
    result = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = _PATTERN.fullmatch(line)
        if not match:
            raise RuntimeError(f"Unsupported/unpinned lock entry: {line!r}")
        result[match.group(1)] = match.group(2)
    return result


def dependency_status() -> tuple[bool, dict]:
    expected = expected_versions()
    installed = {}
    mismatches = []
    for name, wanted in expected.items():
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            actual = None
        installed[name] = actual
        if actual != wanted:
            mismatches.append({"package": name, "expected": wanted, "installed": actual})
    return not mismatches, {"expected_count": len(expected), "mismatches": mismatches, "installed": installed}


def main() -> int:
    ok, details = dependency_status()
    print(json.dumps({"status": "ok" if ok else "fail", **details}, indent=2, sort_keys=True))
    return 0 if ok else 2

if __name__ == "__main__":
    raise SystemExit(main())
