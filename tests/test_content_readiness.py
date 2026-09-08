from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import main
from scripts.clinical_content import file_hash


ROOT = Path(__file__).resolve().parents[1]


def test_lifespan_certifies_content_and_readiness_exposes_it():
    main._CLINICAL_CONTENT_CERTIFICATION = None

    with TestClient(main.app) as client:
        response = client.get(
            "/api/v1/readyz"
        )

        assert response.status_code == 200

        payload = response.json()

        assert payload[
            "clinical_content"
        ] == "certified"

        expected_hash = file_hash(
            ROOT / "data" /
            "clinical_content_manifest.json"
        )

        assert payload[
            "clinical_content_manifest_sha256"
        ] == expected_hash

        assert (
            main._CLINICAL_CONTENT_CERTIFICATION[
                "database_revision"
            ]
            == "0007"
        )


def test_readiness_rejects_revision_different_from_certification(
    monkeypatch,
):
    main._CLINICAL_CONTENT_CERTIFICATION = {
        "database_revision": "9999",
        "manifest_version": 1,
        "manifest_sha256": "0" * 64,
    }

    monkeypatch.setattr(
        main.database,
        "assert_database_health",
        lambda quick_check=False: None,
    )

    monkeypatch.setattr(
        main.database,
        "assert_schema_current",
        lambda: "0007",
    )

    with pytest.raises(
        RuntimeError,
        match="startup-certified",
    ):
        main._readiness_payload()

    main._CLINICAL_CONTENT_CERTIFICATION = None
