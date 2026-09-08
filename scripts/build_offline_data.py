#!/usr/bin/env python3
"""Build deterministic static bundles used by the PWA when the API is offline."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import database
import main
import schemas

OUT_DIR = BASE_DIR / "assets" / "offline"
SAE_OUT = OUT_DIR / "sae.json"
POLICY_OUT = OUT_DIR / "policies.json"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=str)
    path.write_text(text + "\n", encoding="utf-8")


def build() -> tuple[int, int]:
    session = database.SessionLocal()
    try:
        revision_row = session.execute(database.text("SELECT version_num FROM alembic_version LIMIT 1")).first()
        revision = revision_row[0] if revision_row else ""

        diagnoses = (
            session.query(database.SAEDiagnostic)
            .order_by(database.SAEDiagnostic.code.asc())
            .all()
        )
        sae_items = [main._sae_payload(row) for row in diagnoses]

        policies = (
            session.query(database.PublicHealthPolicy)
            .order_by(database.PublicHealthPolicy.policy_name.asc(), database.PublicHealthPolicy.directive.asc())
            .all()
        )
        grouped: dict[str, list[dict]] = defaultdict(list)
        for row in policies:
            grouped[row.policy_name].append(
                schemas.PolicyOut.model_validate(row).model_dump(mode="json")
            )

        _write_json(
            SAE_OUT,
            {
                "schema_version": 1,
                "api_version": main.API_VERSION,
                "database_revision": revision,
                "count": len(sae_items),
                "items": sae_items,
            },
        )
        _write_json(
            POLICY_OUT,
            {
                "schema_version": 1,
                "api_version": main.API_VERSION,
                "database_revision": revision,
                "count": len(policies),
                "policies": {
                    name: {
                        "policy_name": name,
                        "returned": len(items),
                        "items": items,
                    }
                    for name, items in sorted(grouped.items())
                },
            },
        )
    finally:
        session.close()

    print(f"Built offline SAE bundle: {SAE_OUT} ({len(sae_items)} diagnoses)")
    print(f"Built offline policy bundle: {POLICY_OUT} ({len(policies)} directives)")
    return len(sae_items), len(policies)


if __name__ == "__main__":
    build()
