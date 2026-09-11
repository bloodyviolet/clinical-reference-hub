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

from clinical_tools.hemodynamics import (  # noqa: E402
    calculate_hemodynamics,
)


client = TestClient(main.app)


VECTORS = json.loads(
    (
        ROOT
        / "tests"
        / "fixtures"
        / "hemodynamics_vectors.json"
    ).read_text(
        encoding="utf-8"
    )
)


def test_shared_hemodynamics_vectors():
    for vector in VECTORS:
        result = calculate_hemodynamics(
            **vector["input"]
        )

        assert (
            result["pulse_pressure_mm_hg"]
            == vector["pulse_pressure"]
        )

        assert (
            result["mean_arterial_pressure_mm_hg"]
            == vector["map"]
        )

        assert (
            result["shock_index"]
            == vector["shock_index"]
        )

        assert (
            result["modified_shock_index"]
            == vector[
                "modified_shock_index"
            ]
        )


def test_reference_formula_values():
    result = calculate_hemodynamics(
        systolic_bp=120,
        diastolic_bp=80,
        heart_rate=60,
    )

    assert (
        result["pulse_pressure_mm_hg"]
        == 40.0
    )

    assert (
        result["mean_arterial_pressure_mm_hg"]
        == 93.3
    )

    assert result["shock_index"] == 0.5

    assert (
        result["modified_shock_index"]
        == 0.643
    )


def test_no_universal_shock_threshold_is_applied():
    result = calculate_hemodynamics(
        systolic_bp=90,
        diastolic_bp=60,
        heart_rate=110,
    )

    assert (
        result[
            "threshold_classification_applied"
        ]
        is False
    )

    assert (
        "universal"
        in result["interpretation_en"]
    )


def test_equal_systolic_and_diastolic_is_calculable():
    result = calculate_hemodynamics(
        systolic_bp=80,
        diastolic_bp=80,
        heart_rate=80,
    )

    assert (
        result["pulse_pressure_mm_hg"]
        == 0.0
    )

    assert (
        result["mean_arterial_pressure_mm_hg"]
        == 80.0
    )


def test_systolic_below_diastolic_fails_closed():
    with pytest.raises(
        ValueError,
        match="cannot be lower",
    ):
        calculate_hemodynamics(
            systolic_bp=70,
            diastolic_bp=80,
            heart_rate=60,
        )


@pytest.mark.parametrize(
    (
        "systolic",
        "diastolic",
        "heart_rate",
    ),
    [
        (0, 80, 60),
        (120, 0, 60),
        (120, 80, 0),
        (-1, 80, 60),
    ],
)
def test_non_positive_inputs_fail_closed(
    systolic,
    diastolic,
    heart_rate,
):
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        calculate_hemodynamics(
            systolic_bp=systolic,
            diastolic_bp=diastolic,
            heart_rate=heart_rate,
        )


def test_hemodynamics_api():
    response = client.post(
        "/api/v1/tools/hemodynamics",
        json={
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "heart_rate": 60,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload[
            "pulse_pressure_mm_hg"
        ]
        == 40.0
    )

    assert (
        payload[
            "mean_arterial_pressure_mm_hg"
        ]
        == 93.3
    )

    assert (
        payload["shock_index"]
        == 0.5
    )

    assert (
        payload[
            "modified_shock_index"
        ]
        == 0.643
    )

    assert payload["interpretation_pt"]
    assert payload["interpretation_en"]


def test_hemodynamics_api_rejects_reversed_pressure():
    response = client.post(
        "/api/v1/tools/hemodynamics",
        json={
            "systolic_bp": 70,
            "diastolic_bp": 80,
            "heart_rate": 60,
        },
    )

    assert response.status_code == 422


def test_hemodynamics_metadata_contract():
    response = client.get(
        "/api/v1/tools/hemodynamics/meta"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["id"]
        == "hemodynamics"
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
