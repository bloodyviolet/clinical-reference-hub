#!/usr/bin/env python3
"""Production preflight. This is deliberately non-mutating."""
from __future__ import annotations
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import database
from config import load_settings
from scripts.check_dependencies import dependency_status
from scripts.clinical_content import validate_release_content


def fail(message: str) -> None:
    print(json.dumps({"status": "fail", "error": message}, ensure_ascii=False), file=sys.stderr)
    raise SystemExit(2)


def main() -> int:
    settings = load_settings()
    try:
        warnings = settings.assert_valid()
        required = [
            ROOT / "index.html", ROOT / "manifest.json", ROOT / "sw.js",
            ROOT / "assets" / "app.css", ROOT / "assets" / "app.js",
            ROOT / "assets" / "offline" / "sae.json",
            ROOT / "assets" / "offline" / "policies.json",
            ROOT / "data" / "clinical_content_manifest.json",
            ROOT / "assets" / "icons" / "icon-192.png",
            ROOT / "assets" / "icons" / "icon-512.png",
            ROOT / "assets" / "icons" / "apple-touch-icon.png",
            ROOT / "assets" / "icons" / "favicon.ico",
            ROOT / "assets" / "icons" / "favicon-32.png",
            ROOT / "assets" / "icons" / "favicon-16.png",
            ROOT / "pdfs" / "Nanda-I 2024-2026.pdf",
        ]
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            fail("Missing runtime files: " + ", ".join(missing))
        with (ROOT / "pdfs" / "Nanda-I 2024-2026.pdf").open("rb") as handle:
            if handle.read(5) != b"%PDF-":
                fail("Public NANDA PDF does not have a valid PDF signature.")
        database.assert_database_health(quick_check=True)
        revision = database.assert_schema_current()
        dependency_lock = "not_enforced"
        if settings.enforce_dependency_lock:
            deps_ok, deps = dependency_status()
            if not deps_ok:
                fail("Runtime dependency lock mismatch: " + json.dumps(deps["mismatches"], ensure_ascii=False))
            dependency_lock = "ok"
        path = database.sqlite_database_path()
        content = validate_release_content(
            ROOT,
            path,
            ROOT / "data" / "clinical_content_manifest.json",
        )
        sae = content["sae_count"]
        links = content["link_count"]
        policies = content["policy_count"]

        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        icons = manifest.get("icons") or []
        if len(icons) < 2 or any("://" in str(icon.get("src", "")) for icon in icons):
            fail("PWA manifest must use packaged local icons only.")

        sae_offline = json.loads((ROOT / "assets" / "offline" / "sae.json").read_text(encoding="utf-8"))
        policy_offline = json.loads((ROOT / "assets" / "offline" / "policies.json").read_text(encoding="utf-8"))
        if sae_offline.get("database_revision") != revision or sae_offline.get("count") != sae:
            fail("Offline SAE bundle is stale or does not match the runtime database.")
        if policy_offline.get("database_revision") != revision or policy_offline.get("count") != policies:
            fail("Offline policy bundle is stale or does not match the runtime database.")
        by_code = {str(item.get("code")): item for item in sae_offline.get("items", [])}
        sample = by_code.get("00068")
        if not sample:
            fail("Offline SAE bundle is missing NANDA 00068 regression sample.")
        if str(sample.get("description_en", "")).lower() in str(sample.get("intervention_pt", "")).lower():
            fail("Offline SAE bundle contains English diagnosis leakage in Portuguese intervention text.")
    except Exception as exc:
        fail(str(exc))
    result = {
        "status": "ok", "environment": settings.environment, "revision": revision,
        "sae_records": sae, "classification_links": links, "policy_directives": policies,
        "dependency_lock": dependency_lock, "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
