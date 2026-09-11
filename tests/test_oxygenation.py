from pathlib import Path
import json
import sys

import pytest
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )


import main  # noqa: E402

from clinical_tools.oxygenation import (  # noqa: E402
    calculate_oxygenation,
)


client = TestClient(main.app)


VECTORS = json.loads(
    (
        ROOT
        / "tests"
        / "fixtures"
        / "oxygenation_vectors.json"
    ).read_text(
        encoding="utf-8"
    )
)


def test_shared_oxygenation_vectors():
    for vector in VECTORS:
        result = calculate_oxygenation(
            **vector["input"]
        )

        assert (
            result["pf_ratio_mm_hg"]
            == vector["pf_ratio"]
        )

        assert (
            result["sf_ratio"]
            == vector["sf_ratio"]
        )

        assert (
            result[
                "sf_spo2_above_97_caution"
            ]
            == vector["sf_caution"]
        )

        assert (
            result[
                "global_ards_sf_threshold_applicable"
            ]
            == vector[
                "sf_threshold_applicable"
            ]
        )


def test_pf_formula_reference():
    result = calculate_oxygenation(
        fio2_percent=40,
        pao2_mm_hg=80,
    )

    assert (
        result["fio2_fraction"]
        == 0.4
    )

    assert (
        result["pf_ratio_mm_hg"]
        == 200.0
    )


def test_sf_formula_reference():
    result = calculate_oxygenation(
        fio2_percent=40,
        spo2_percent=95,
    )

    assert (
        result["sf_ratio"]
        == 237.5
    )


def test_pao2_and_spo2_are_independently_optional():
    pf = calculate_oxygenation(
        fio2_percent=50,
        pao2_mm_hg=75,
    )

    assert (
        pf["pf_ratio_mm_hg"]
        == 150.0
    )
    assert pf["sf_ratio"] is None

    sf = calculate_oxygenation(
        fio2_percent=50,
        spo2_percent=90,
    )

    assert sf["pf_ratio_mm_hg"] is None
    assert sf["sf_ratio"] == 180.0


def test_at_least_one_oxygenation_measurement_is_required():
    with pytest.raises(
        ValueError,
        match="At least one",
    ):
        calculate_oxygenation(
            fio2_percent=40,
        )


@pytest.mark.parametrize(
    "fio2",
    [
        20.9,
        0.4,
        101,
    ],
)
def test_fio2_percent_contract_fails_closed(
    fio2,
):
    with pytest.raises(
        ValueError,
        match="between 21 and 100",
    ):
        calculate_oxygenation(
            fio2_percent=fio2,
            spo2_percent=95,
        )


def test_sf_above_97_has_explicit_caution():
    result = calculate_oxygenation(
        fio2_percent=50,
        spo2_percent=98,
    )

    assert (
        result[
            "sf_spo2_above_97_caution"
        ]
        is True
    )

    assert (
        result[
            "global_ards_sf_threshold_applicable"
        ]
        is False
    )

    assert (
        "97%"
        in result["sf_note_en"]
    )


def test_ratio_does_not_auto_classify_ards():
    result = calculate_oxygenation(
        fio2_percent=100,
        pao2_mm_hg=50,
        spo2_percent=80,
    )

    assert (
        result[
            "ards_classification_applied"
        ]
        is False
    )


def test_api_supports_both_ratios():
    response = client.post(
        "/api/v1/tools/oxygenation",
        json={
            "fio2_percent": 40,
            "pao2_mm_hg": 80,
            "spo2_percent": 95,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["pf_ratio_mm_hg"]
        == 200.0
    )

    assert (
        payload["sf_ratio"]
        == 237.5
    )

    assert payload["interpretation_pt"]
    assert payload["interpretation_en"]


def test_api_supports_spo2_only():
    response = client.post(
        "/api/v1/tools/oxygenation",
        json={
            "fio2_percent": 50,
            "spo2_percent": 90,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["pao2_mm_hg"] is None
    assert payload["pf_ratio_mm_hg"] is None
    assert payload["sf_ratio"] == 180.0


def test_api_rejects_no_measurement():
    response = client.post(
        "/api/v1/tools/oxygenation",
        json={
            "fio2_percent": 40,
        },
    )

    assert response.status_code == 422


def test_oxygenation_metadata_contract():
    response = client.get(
        "/api/v1/tools/oxygenation/meta"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["id"]
        == "oxygenation-ratios"
    )

    assert payload["name_pt"]
    assert payload["name_en"]

    assert payload["aliases_pt"]
    assert payload["aliases_en"]

    assert payload["limitations_pt"]
    assert payload["limitations_en"]

    assert (
        payload["offline_capable"]
        is True
    )
