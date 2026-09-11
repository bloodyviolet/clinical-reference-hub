from __future__ import annotations

from pathlib import Path
import sys

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

from clinical_tools.falls_function import (  # noqa: E402
    CADERNETA_FALLS_METADATA,
    IVCF20_METADATA,
    calculate_caderneta_falls_checkup,
    calculate_ivcf20,
)


client = TestClient(
    main.app
)


def falls_payload(
    **overrides,
):
    payload = {
        "age_years": 60,
        "fall_previous_year": False,
        "cane_or_walker_recommended": False,
        "unsteady_while_walking": False,
        "uses_furniture_for_support": False,
        "concern_about_falling": False,
        "needs_hands_to_rise_from_chair": False,
        "difficulty_stepping_onto_curb": False,
        "toilet_urgency": False,
        "reduced_foot_sensation": False,
        "medication_dizziness_or_fatigue": False,
        "sleep_or_mood_medication": False,
        "sadness_or_depressed_mood": False,
    }

    payload.update(
        overrides
    )

    return payload


def ivcf_payload(
    **overrides,
):
    payload = {
        "age_years": 60,
        "self_rated_health_regular_or_poor": False,
        "stopped_shopping_due_health": False,
        "stopped_managing_money_due_health": False,
        "stopped_housework_due_health": False,
        "stopped_bathing_due_health": False,
        "forgetfulness_noted_by_others": False,
        "worsening_forgetfulness": False,
        "forgetfulness_impairs_daily_activity": False,
        "depressed_or_hopeless_last_month": False,
        "anhedonia_last_month": False,
        "unable_raise_arms_above_shoulders": False,
        "unable_handle_small_objects": False,
        "unintentional_weight_loss_criterion": False,
        "bmi_lt_22": False,
        "calf_circumference_lt_31_cm": False,
        "gait_4m_gt_5_seconds": False,
        "walking_difficulty_impairs_daily_activity": False,
        "two_or_more_falls_last_year": False,
        "urinary_or_fecal_incontinence": False,
        "vision_impairs_daily_activity": False,
        "hearing_impairs_daily_activity": False,
        "five_or_more_chronic_conditions": False,
        "five_or_more_daily_medications": False,
        "hospitalized_last_six_months": False,
    }

    payload.update(
        overrides
    )

    return payload


def test_caderneta_api_matches_python_core():
    payload = falls_payload(
        concern_about_falling=True,
        reduced_foot_sensation=True,
    )

    response = client.post(
        "/api/v1/tools/brazil-caderneta-falls",
        json=payload,
    )

    assert response.status_code == 200

    assert (
        response.json()
        == calculate_caderneta_falls_checkup(
            **payload
        )
    )


def test_caderneta_api_preserves_any_yes_not_weighted_score():
    response = client.post(
        "/api/v1/tools/brazil-caderneta-falls",
        json=falls_payload(
            fall_previous_year=True,
        ),
    )

    assert response.status_code == 200

    result = response.json()

    assert result["positive_items_count"] == 1
    assert result["assessment_indicated"] is True
    assert result["any_yes_rule_applied"] is True
    assert result["weighted_score_applied"] is False

    assert (
        result["foreign_weighted_score_imported"]
        is False
    )

    assert (
        result["fall_risk_classification_applied"]
        is False
    )

    assert (
        result["automatic_ivcf_inference_applied"]
        is False
    )

    assert (
        result[
            "synthetic_cross_instrument_score_applied"
        ]
        is False
    )


def test_caderneta_api_rejects_age_below_60():
    response = client.post(
        "/api/v1/tools/brazil-caderneta-falls",
        json=falls_payload(
            age_years=59,
        ),
    )

    assert response.status_code == 422


def test_ivcf20_api_matches_python_core():
    payload = ivcf_payload(
        age_years=85,
        stopped_bathing_due_health=True,
        two_or_more_falls_last_year=True,
        gait_4m_gt_5_seconds=True,
    )

    response = client.post(
        "/api/v1/tools/ivcf20",
        json=payload,
    )

    assert response.status_code == 200

    assert (
        response.json()
        == calculate_ivcf20(
            **payload
        )
    )


def test_ivcf20_api_accepts_age_above_120():
    response = client.post(
        "/api/v1/tools/ivcf20",
        json=ivcf_payload(
            age_years=125,
        ),
    )

    assert response.status_code == 200

    result = response.json()

    assert result["age_years"] == 125
    assert result["dimension_scores"]["age"] == 3
    assert result["total_score"] == 3


def test_ivcf20_api_requires_complete_assessment():
    payload = ivcf_payload()

    del payload[
        "hearing_impairs_daily_activity"
    ]

    response = client.post(
        "/api/v1/tools/ivcf20",
        json=payload,
    )

    assert response.status_code == 422


def test_ivcf20_api_preserves_instrument_boundaries():
    response = client.post(
        "/api/v1/tools/ivcf20",
        json=ivcf_payload(
            gait_4m_gt_5_seconds=True,
            two_or_more_falls_last_year=True,
        ),
    )

    assert response.status_code == 200

    result = response.json()

    assert result["gait_4m_is_tug"] is False

    assert (
        result["fall_risk_classification_applied"]
        is False
    )

    assert (
        result["automatic_caderneta_inference_applied"]
        is False
    )

    assert (
        result[
            "synthetic_cross_instrument_score_applied"
        ]
        is False
    )


def test_caderneta_metadata_api():
    response = client.get(
        "/api/v1/tools/brazil-caderneta-falls/meta"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["id"]
        == CADERNETA_FALLS_METADATA["id"]
    )

    assert (
        payload["brazil_applicability_status"]
        == "national_standard"
    )

    assert (
        payload["final_brazil_review_status"]
        == "pass"
    )

    assert (
        payload["canonical_language"]
        == "pt-BR"
    )


def test_ivcf20_metadata_api():
    response = client.get(
        "/api/v1/tools/ivcf20/meta"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["id"]
        == IVCF20_METADATA["id"]
    )

    assert (
        payload["brazil_applicability_status"]
        == "national_standard"
    )

    assert (
        payload["final_brazil_review_status"]
        == "pass"
    )

    assert (
        payload["canonical_language"]
        == "pt-BR"
    )


def test_openapi_exposes_all_four_item7_routes():
    openapi = main.app.openapi()

    paths = openapi.get(
        "paths",
        {},
    )

    expected = {
        "/api/v1/tools/brazil-caderneta-falls",
        "/api/v1/tools/brazil-caderneta-falls/meta",
        "/api/v1/tools/ivcf20",
        "/api/v1/tools/ivcf20/meta",
    }

    assert expected.issubset(
        paths
    )

    assert (
        "post"
        in paths[
            "/api/v1/tools/brazil-caderneta-falls"
        ]
    )

    assert (
        "post"
        in paths[
            "/api/v1/tools/ivcf20"
        ]
    )


def test_openapi_ivcf_age_has_minimum_but_no_upper_cap():
    openapi = main.app.openapi()

    ivcf = (
        openapi[
            "components"
        ][
            "schemas"
        ][
            "IVCF20Input"
        ]
    )

    age = ivcf[
        "properties"
    ][
        "age_years"
    ]

    assert age["minimum"] == 60

    assert (
        "maximum"
        not in age
    )


def test_openapi_caderneta_age_has_minimum_but_no_upper_cap():
    openapi = main.app.openapi()

    schema = (
        openapi[
            "components"
        ][
            "schemas"
        ][
            "CadernetaFallsInput"
        ]
    )

    age = schema[
        "properties"
    ][
        "age_years"
    ]

    assert age["minimum"] == 60

    assert (
        "maximum"
        not in age
    )
