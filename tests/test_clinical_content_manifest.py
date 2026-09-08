from __future__ import annotations

import json
from pathlib import Path
import shutil
import sqlite3

import pytest

from scripts.clinical_content import (
    ClinicalContentError,
    validate_guidance_content,
    validate_release_content,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = (
    ROOT / "data" /
    "clinical_content_manifest.json"
)


def test_certified_release_content_matches_manifest():
    actual = validate_release_content(
        ROOT,
        ROOT / "medical.db",
        MANIFEST,
    )

    assert actual["sae_count"] == 277
    assert actual["link_count"] == 627
    assert actual["policy_count"] == 54

    assert actual["link_roles"] == {
        "alternative": 73,
        "primary": 554,
    }


def test_missing_alternative_links_fail_manifest(
    tmp_path,
):
    db = tmp_path / "medical.db"

    shutil.copyfile(
        ROOT / "medical.db",
        db,
    )

    con = sqlite3.connect(db)

    try:
        con.execute(
            "DELETE FROM sae_classification_links "
            "WHERE role='alternative'"
        )
        con.commit()
    finally:
        con.close()

    with pytest.raises(
        ClinicalContentError,
        match="Clinical content manifest mismatch",
    ):
        validate_release_content(
            ROOT,
            db,
            MANIFEST,
        )


def test_reviewed_guidance_body_drift_fails(
    tmp_path,
):
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    guidance = (
        data_dir /
        "f02_f03_candidate_patch.json"
    )

    shutil.copyfile(
        ROOT / "data" /
        "f02_f03_candidate_patch.json",
        guidance,
    )

    shutil.copyfile(
        MANIFEST,
        data_dir /
        "clinical_content_manifest.json",
    )

    payload = json.loads(
        guidance.read_text(encoding="utf-8")
    )

    code = sorted(payload["nic"])[0]

    payload["nic"][code][
        "intervention_pt"
    ] += " DRIFT-QC"

    guidance.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ClinicalContentError,
        match="Clinical guidance content mismatch",
    ):
        validate_guidance_content(
            tmp_path,
            data_dir /
            "clinical_content_manifest.json",
        )
