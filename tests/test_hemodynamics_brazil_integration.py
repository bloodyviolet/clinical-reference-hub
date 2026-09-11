from __future__ import annotations

from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient


ROOT = Path(
    __file__
).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )


import main  # noqa: E402

from clinical_tools.hemodynamics import (  # noqa: E402
    HEMODYNAMICS_METADATA,
    calculate_hemodynamics,
)


client = TestClient(
    main.app
)


def test_generic_result_remains_threshold_neutral():
    result = calculate_hemodynamics(
        systolic_bp=90,
        diastolic_bp=60,
        heart_rate=100,
    )

    assert (
        result[
            "clinical_context"
        ]
        == "none"
    )

    assert (
        result[
            "threshold_classification_applied"
        ]
        is False
    )

    assert (
        result[
            "universal_threshold_inference_applied"
        ]
        is False
    )

    assert (
        result[
            "brazil_context_guidance_applied"
        ]
        is False
    )

    assert (
        result[
            "brazil_context_rule_met"
        ]
        is None
    )


def test_septic_shock_map_exact_65_meets_context_target():
    result = calculate_hemodynamics(
        systolic_bp=85,
        diastolic_bp=55,
        heart_rate=90,
        clinical_context="septic_shock",
    )

    assert (
        result[
            "mean_arterial_pressure_mm_hg"
        ]
        == 65.0
    )

    assert (
        result[
            "brazil_context_rule_code"
        ]
        == "septic_shock_map_target"
    )

    assert (
        result[
            "brazil_context_operator"
        ]
        == ">="
    )

    assert (
        result[
            "brazil_context_threshold_value"
        ]
        == 65.0
    )

    assert (
        result[
            "brazil_context_rule_met"
        ]
        is True
    )


def test_septic_shock_map_below_65_is_contextually_flagged():
    result = calculate_hemodynamics(
        systolic_bp=84,
        diastolic_bp=54,
        heart_rate=90,
        clinical_context="septic_shock",
    )

    assert (
        result[
            "mean_arterial_pressure_mm_hg"
        ]
        == 64.0
    )

    assert (
        result[
            "brazil_context_rule_met"
        ]
        is False
    )

    assert (
        result[
            "threshold_classification_applied"
        ]
        is False
    )


def test_obstetric_si_exact_09_does_not_meet_strict_ministry_trigger():
    result = calculate_hemodynamics(
        systolic_bp=100,
        diastolic_bp=70,
        heart_rate=90,
        clinical_context="obstetric_hemorrhage",
    )

    assert (
        result[
            "shock_index"
        ]
        == 0.9
    )

    assert (
        result[
            "brazil_context_operator"
        ]
        == ">"
    )

    assert (
        result[
            "brazil_context_rule_met"
        ]
        is False
    )


def test_obstetric_si_above_09_meets_context_trigger():
    result = calculate_hemodynamics(
        systolic_bp=100,
        diastolic_bp=70,
        heart_rate=91,
        clinical_context="obstetric_hemorrhage",
    )

    assert (
        result[
            "shock_index"
        ]
        == 0.91
    )

    assert (
        result[
            "brazil_context_rule_code"
        ]
        == (
            "obstetric_hemorrhage_"
            "si_trigger"
        )
    )

    assert (
        result[
            "brazil_context_rule_met"
        ]
        is True
    )


def test_context_does_not_change_base_math():
    generic = calculate_hemodynamics(
        systolic_bp=100,
        diastolic_bp=70,
        heart_rate=91,
    )

    contextual = calculate_hemodynamics(
        systolic_bp=100,
        diastolic_bp=70,
        heart_rate=91,
        clinical_context="obstetric_hemorrhage",
    )

    for field in (
        "pulse_pressure_mm_hg",
        "mean_arterial_pressure_mm_hg",
        "shock_index",
        "modified_shock_index",
    ):
        assert (
            generic[field]
            == contextual[field]
        )


def test_unknown_context_fails_closed_in_python():
    with pytest.raises(
        ValueError,
        match="clinical_context",
    ):
        calculate_hemodynamics(
            systolic_bp=120,
            diastolic_bp=80,
            heart_rate=60,
            clinical_context="generic_shock",
        )


def test_api_exposes_septic_context_without_universal_classification():
    response = client.post(
        "/api/v1/tools/hemodynamics",
        json={
            "systolic_bp": 85,
            "diastolic_bp": 55,
            "heart_rate": 90,
            "clinical_context": "septic_shock",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload[
            "brazil_context_guidance_applied"
        ]
        is True
    )

    assert (
        payload[
            "brazil_context_rule_met"
        ]
        is True
    )

    assert (
        payload[
            "threshold_classification_applied"
        ]
        is False
    )


def test_api_rejects_unknown_context():
    response = client.post(
        "/api/v1/tools/hemodynamics",
        json={
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "heart_rate": 60,
            "clinical_context": "generic_shock",
        },
    )

    assert response.status_code == 422


def test_metadata_exposes_brazil_context_only_policy():
    assert (
        HEMODYNAMICS_METADATA[
            "brazil_applicability_status"
        ]
        == "complementary_brazil_guidance"
    )

    assert (
        HEMODYNAMICS_METADATA[
            "brazil_differs_from_international"
        ]
        is False
    )

    assert (
        HEMODYNAMICS_METADATA[
            "final_brazil_review_status"
        ]
        == "pass"
    )

    assert (
        "universal"
        in HEMODYNAMICS_METADATA[
            "brazil_difference_notes_en"
        ]
    )


def test_metadata_api_exposes_brazil_layer():
    response = client.get(
        "/api/v1/tools/hemodynamics/meta"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload[
            "brazil_review_date"
        ]
        == "2026-09-11"
    )

    assert (
        payload[
            "final_brazil_review_status"
        ]
        == "pass"
    )
