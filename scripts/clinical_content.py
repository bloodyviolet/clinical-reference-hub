#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys


SAE_FIELDS = (
    "code", "description_en", "description_pt",
    "intervention_en", "intervention_pt",
    "outcome_en", "outcome_pt",
    "mapping_status", "mapping_methodology",
    "mapping_review_date", "mapping_notes",
    "nanda_edition", "nanda_domain", "nanda_class",
    "nanda_source_page", "nic_edition", "nic_code",
    "nic_label_en", "nic_label_pt", "noc_edition",
    "noc_code", "noc_label_en", "noc_label_pt",
    "mapping_confidence", "mapping_reference",
    "mapping_rationale", "nanda_pdf_page",
)

LINK_FIELDS = (
    "classification", "code", "label_en", "label_pt",
    "edition", "role", "applicability",
    "applicability_en", "applicability_pt",
    "confidence", "verification_status",
    "source_language", "source_reference",
    "source_page", "review_date", "notes", "sort_order",
)

POLICY_FIELDS = (
    "policy_name", "directive", "target_demographic",
    "clinical_guideline", "source_title", "source_url",
    "source_page", "source_publication_date",
    "effective_from", "effective_until",
    "last_clinical_review", "source_version",
    "status", "review_notes", "evidence_level",
)


def canonical_hash(value) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)
    return digest.hexdigest()


def row_dict(row, fields):
    return {
        field: row[field]
        for field in fields
    }


def database_fingerprint(db: Path) -> dict:
    con = sqlite3.connect(
        f"file:{db}?mode=ro",
        uri=True,
    )
    con.row_factory = sqlite3.Row

    try:
        revision = con.execute(
            "SELECT version_num "
            "FROM alembic_version LIMIT 1"
        ).fetchone()[0]

        sae_rows = [
            row_dict(row, SAE_FIELDS)
            for row in con.execute(
                "SELECT "
                + ",".join(SAE_FIELDS)
                + " FROM sae_diagnostics "
                  "ORDER BY code"
            )
        ]

        link_rows = []

        sql = """
            SELECT
                d.code AS diagnostic_code,
                l.*
            FROM sae_classification_links AS l
            JOIN sae_diagnostics AS d
              ON d.id = l.sae_diagnostic_id
            ORDER BY
                d.code,
                l.classification,
                l.sort_order,
                l.code,
                l.role,
                l.label_en
        """

        for row in con.execute(sql):
            item = {
                "diagnostic_code":
                    row["diagnostic_code"]
            }

            item.update(
                row_dict(row, LINK_FIELDS)
            )

            link_rows.append(item)

        policy_rows = [
            row_dict(row, POLICY_FIELDS)
            for row in con.execute(
                "SELECT "
                + ",".join(POLICY_FIELDS)
                + " FROM public_health_policies "
                  "ORDER BY "
                  "policy_name, directive, "
                  "target_demographic, source_url"
            )
        ]

        roles = dict(
            con.execute(
                """
                SELECT role, COUNT(*)
                FROM sae_classification_links
                GROUP BY role
                ORDER BY role
                """
            ).fetchall()
        )

        classifications = dict(
            con.execute(
                """
                SELECT classification, COUNT(*)
                FROM sae_classification_links
                GROUP BY classification
                ORDER BY classification
                """
            ).fetchall()
        )

        return {
            "database_revision": str(revision),
            "sae_count": len(sae_rows),
            "link_count": len(link_rows),
            "policy_count": len(policy_rows),
            "link_roles": roles,
            "link_classifications": classifications,
            "sae_semantic_sha256":
                canonical_hash(sae_rows),
            "links_semantic_sha256":
                canonical_hash(link_rows),
            "policies_semantic_sha256":
                canonical_hash(policy_rows),
        }

    finally:
        con.close()


def guidance_fingerprint(path: Path) -> dict:
    payload = json.loads(
        path.read_text(encoding="utf-8")
    )

    nic = payload.get("nic") or {}
    noc = payload.get("noc") or {}
    f03 = payload.get("f03") or {}

    return {
        "guidance_patch_sha256":
            file_hash(path),
        "guidance_semantic_sha256":
            canonical_hash(payload),
        "guidance_nic_count": len(nic),
        "guidance_noc_count": len(noc),
        "guidance_f03_count": len(f03),
    }


def compute(root: Path, db: Path) -> dict:
    result = {
        "manifest_version": 1,
    }

    result.update(
        database_fingerprint(db)
    )

    result.update(
        guidance_fingerprint(
            root / "data" /
            "f02_f03_candidate_patch.json"
        )
    )

    result.update({
        "offline_sae_sha256":
            file_hash(
                root / "assets" /
                "offline" / "sae.json"
            ),
        "offline_policies_sha256":
            file_hash(
                root / "assets" /
                "offline" / "policies.json"
            ),
    })

    return result


def compare(expected: dict, actual: dict):
    problems = []

    keys = sorted(
        set(expected) | set(actual)
    )

    for key in keys:
        if expected.get(key) != actual.get(key):
            problems.append(
                f"{key}: expected="
                f"{expected.get(key)!r} "
                f"actual={actual.get(key)!r}"
            )

    return problems



class ClinicalContentError(RuntimeError):
    """Certified clinical release content does not match its manifest."""


def load_manifest(path: Path) -> dict:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def validate_release_content(
    root: Path,
    db: Path,
    manifest_path: Path,
) -> dict:
    expected = load_manifest(manifest_path)
    actual = compute(root, db)
    problems = compare(expected, actual)

    if problems:
        raise ClinicalContentError(
            "Clinical content manifest mismatch: "
            + "; ".join(problems)
        )

    return actual


def validate_guidance_content(
    root: Path,
    manifest_path: Path,
) -> dict:
    expected = load_manifest(manifest_path)

    actual = guidance_fingerprint(
        root / "data" /
        "f02_f03_candidate_patch.json"
    )

    keys = (
        "guidance_patch_sha256",
        "guidance_semantic_sha256",
        "guidance_nic_count",
        "guidance_noc_count",
        "guidance_f03_count",
    )

    problems = []

    for key in keys:
        if expected.get(key) != actual.get(key):
            problems.append(
                f"{key}: expected="
                f"{expected.get(key)!r} "
                f"actual={actual.get(key)!r}"
            )

    if problems:
        raise ClinicalContentError(
            "Clinical guidance content mismatch: "
            + "; ".join(problems)
        )

    return actual

def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--root",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--database",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--generate",
        action="store_true",
    )

    args = parser.parse_args()

    actual = compute(
        args.root.resolve(),
        args.database.resolve(),
    )

    if args.generate:
        args.manifest.write_text(
            json.dumps(
                actual,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        print(
            json.dumps(
                {
                    "status": "generated",
                    **actual,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0

    expected = json.loads(
        args.manifest.read_text(
            encoding="utf-8"
        )
    )

    problems = compare(
        expected,
        actual,
    )

    if problems:
        print(
            json.dumps(
                {
                    "status": "fail",
                    "problems": problems,
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2

    print(
        json.dumps(
            {
                "status": "ok",
                **actual,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
