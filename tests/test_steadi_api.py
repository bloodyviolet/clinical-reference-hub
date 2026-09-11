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

from clinical_tools.steadi import (  # noqa: E402
    STEADI_CHAIR_STAND_METADATA,
    STEADI_FOUR_STAGE_METADATA,
    STEADI_ORTHOSTATIC_BP_METADATA,
    STEADI_TUG_METADATA,
    calculate_steadi_chair_stand_30s,
    calculate_steadi_four_stage_balance,
    calculate_steadi_orthostatic_bp,
    calculate_steadi_tug,
)


client = TestClient(
    main.app
)


def tug_payload(
    **overrides,
):
    payload = {
        "time_seconds":
            10,
        "walking_aid_used":
            False,
        "standard_3m_protocol_confirmed":
            True,
    }

    payload.update(
        overrides
    )

    return payload


def chair_payload(
    **overrides,
):
    payload = {
        "age_years":
            60,
        "sex":
            "male",
        "repetitions":
            14,
        "arms_required_to_stand":
            False,
        "standard_30_second_protocol_confirmed":
            True,
    }

    payload.update(
        overrides
    )

    return payload


def balance_payload(
    **overrides,
):
    payload = {
        "side_by_side_seconds":
            10,
        "semi_tandem_seconds":
            10,
        "tandem_seconds":
            10,
        "one_leg_seconds":
            10,
        "assistive_device_used":
            False,
        "standard_four_stage_protocol_confirmed":
            True,
    }

    payload.update(
        overrides
    )

    return payload


def orthostatic_payload(
    **overrides,
):
    payload = {
        "supine_sbp_mm_hg":
            130,
        "supine_dbp_mm_hg":
            80,
        "supine_pulse_bpm":
            70,

        "standing_1m_sbp_mm_hg":
            125,
        "standing_1m_dbp_mm_hg":
            77,
        "standing_1m_pulse_bpm":
            76,

        "standing_3m_sbp_mm_hg":
            125,
        "standing_3m_dbp_mm_hg":
            77,
        "standing_3m_pulse_bpm":
            74,

        "lightheaded_or_dizzy":
            False,

        "standard_5_1_3_protocol_confirmed":
            True,
    }

    payload.update(
        overrides
    )

    return payload


def test_tug_api_matches_python_core():
    payload = tug_payload(
        time_seconds=12,
        walking_aid_used=True,
    )

    response = client.post(
        "/api/v1/tools/steadi-tug",
        json=payload,
    )

    assert response.status_code == 200

    assert (
        response.json()
        == calculate_steadi_tug(
            **payload
        )
    )


def test_tug_api_preserves_exact_12_second_boundary():
    below = client.post(
        "/api/v1/tools/steadi-tug",
        json=tug_payload(
            time_seconds=11.99,
        ),
    )

    exact = client.post(
        "/api/v1/tools/steadi-tug",
        json=tug_payload(
            time_seconds=12,
        ),
    )

    assert below.status_code == 200
    assert exact.status_code == 200

    assert (
        below.json()[
            "increased_fall_risk"
        ]
        is False
    )

    assert (
        exact.json()[
            "increased_fall_risk"
        ]
        is True
    )


def test_tug_api_rejects_unconfirmed_protocol():
    response = client.post(
        "/api/v1/tools/steadi-tug",
        json=tug_payload(
            standard_3m_protocol_confirmed=False,
        ),
    )

    assert response.status_code == 422

    assert (
        "3-m / 10-ft"
        in response.json()["detail"]
    )


def test_chair_api_matches_python_core():
    payload = chair_payload(
        age_years=85,
        sex="female",
        repetitions=7,
    )

    response = client.post(
        "/api/v1/tools/steadi-chair-stand-30s",
        json=payload,
    )

    assert response.status_code == 200

    assert (
        response.json()
        == calculate_steadi_chair_stand_30s(
            **payload
        )
    )


def test_chair_api_exact_threshold_is_not_below_average():
    response = client.post(
        "/api/v1/tools/steadi-chair-stand-30s",
        json=chair_payload(
            age_years=60,
            sex="male",
            repetitions=14,
        ),
    )

    assert response.status_code == 200

    result = response.json()

    assert (
        result[
            "below_average_threshold"
        ]
        == 14
    )

    assert (
        result["below_average"]
        is False
    )

    assert (
        result[
            "increased_fall_risk"
        ]
        is False
    )


def test_chair_api_accepts_age_above_94_without_extrapolation():
    response = client.post(
        "/api/v1/tools/steadi-chair-stand-30s",
        json=chair_payload(
            age_years=125,
            sex="female",
            repetitions=1,
        ),
    )

    assert response.status_code == 200

    result = response.json()

    assert result[
        "age_years"
    ] == 125

    assert (
        result[
            "reference_classification_available"
        ]
        is False
    )

    assert (
        result[
            "reference_age_band"
        ]
        is None
    )

    assert (
        result[
            "below_average_threshold"
        ]
        is None
    )

    assert (
        result[
            "below_average"
        ]
        is None
    )

    assert (
        result[
            "increased_fall_risk"
        ]
        is None
    )

    assert (
        result[
            "cutoff_extrapolated"
        ]
        is False
    )


def test_chair_api_arm_use_records_zero():
    response = client.post(
        "/api/v1/tools/steadi-chair-stand-30s",
        json=chair_payload(
            repetitions=12,
            arms_required_to_stand=True,
        ),
    )

    assert response.status_code == 200

    result = response.json()

    assert (
        result[
            "observed_repetitions_input"
        ]
        == 12
    )

    assert (
        result[
            "recorded_repetitions"
        ]
        == 0
    )

    assert (
        result[
            "test_stopped_due_to_arm_use"
        ]
        is True
    )


def test_balance_api_matches_python_core():
    payload = balance_payload(
        tandem_seconds=9,
        one_leg_seconds=None,
    )

    response = client.post(
        "/api/v1/tools/steadi-four-stage-balance",
        json=payload,
    )

    assert response.status_code == 200

    assert (
        response.json()
        == calculate_steadi_four_stage_balance(
            **payload
        )
    )


def test_balance_api_rejects_invalid_stage_progression():
    response = client.post(
        "/api/v1/tools/steadi-four-stage-balance",
        json=balance_payload(
            side_by_side_seconds=8,
            semi_tandem_seconds=5,
            tandem_seconds=None,
            one_leg_seconds=None,
        ),
    )

    assert response.status_code == 422

    assert (
        "Later"
        in response.json()["detail"]
    )


def test_balance_api_rejects_assistive_device():
    response = client.post(
        "/api/v1/tools/steadi-four-stage-balance",
        json=balance_payload(
            assistive_device_used=True,
        ),
    )

    assert response.status_code == 422

    assert (
        "assistive device"
        in response.json()["detail"]
    )


def test_orthostatic_api_matches_python_core():
    payload = orthostatic_payload(
        standing_1m_sbp_mm_hg=110,
    )

    response = client.post(
        "/api/v1/tools/steadi-orthostatic-bp",
        json=payload,
    )

    assert response.status_code == 200

    assert (
        response.json()
        == calculate_steadi_orthostatic_bp(
            **payload
        )
    )


def test_orthostatic_api_exact_20_10_boundaries():
    response = client.post(
        "/api/v1/tools/steadi-orthostatic-bp",
        json=orthostatic_payload(
            standing_1m_sbp_mm_hg=110,
            standing_3m_dbp_mm_hg=70,
        ),
    )

    assert response.status_code == 200

    result = response.json()

    assert (
        result[
            "systolic_drop_1m_mm_hg"
        ]
        == 20
    )

    assert (
        result[
            "diastolic_drop_3m_mm_hg"
        ]
        == 10
    )

    assert (
        result[
            "systolic_threshold_met"
        ]
        is True
    )

    assert (
        result[
            "diastolic_threshold_met"
        ]
        is True
    )

    assert (
        result[
            "abnormal_steadi_orthostatic_assessment"
        ]
        is True
    )


def test_orthostatic_api_symptoms_alone_are_abnormal():
    response = client.post(
        "/api/v1/tools/steadi-orthostatic-bp",
        json=orthostatic_payload(
            lightheaded_or_dizzy=True,
        ),
    )

    assert response.status_code == 200

    result = response.json()

    assert (
        result[
            "systolic_threshold_met"
        ]
        is False
    )

    assert (
        result[
            "diastolic_threshold_met"
        ]
        is False
    )

    assert (
        result[
            "abnormal_steadi_orthostatic_assessment"
        ]
        is True
    )


def test_orthostatic_api_rejects_unconfirmed_protocol():
    response = client.post(
        "/api/v1/tools/steadi-orthostatic-bp",
        json=orthostatic_payload(
            standard_5_1_3_protocol_confirmed=False,
        ),
    )

    assert response.status_code == 422

    assert (
        "5-minute"
        in response.json()["detail"]
    )


def test_all_four_metadata_endpoints():
    cases = (
        (
            "/api/v1/tools/steadi-tug/meta",
            STEADI_TUG_METADATA,
        ),
        (
            "/api/v1/tools/steadi-chair-stand-30s/meta",
            STEADI_CHAIR_STAND_METADATA,
        ),
        (
            "/api/v1/tools/steadi-four-stage-balance/meta",
            STEADI_FOUR_STAGE_METADATA,
        ),
        (
            "/api/v1/tools/steadi-orthostatic-bp/meta",
            STEADI_ORTHOSTATIC_BP_METADATA,
        ),
    )

    for (
        endpoint,
        expected,
    ) in cases:
        response = client.get(
            endpoint
        )

        assert response.status_code == 200

        result = response.json()

        assert (
            result["id"]
            == expected["id"]
        )

        assert (
            result[
                "brazil_applicability_status"
            ]
            == "no_national_variant_identified"
        )

        assert (
            result[
                "final_brazil_review_status"
            ]
            == "pass"
        )

        assert (
            result[
                "canonical_language"
            ]
            == "en-US"
        )


def test_all_steadi_api_results_preserve_separation_flags():
    responses = (
        client.post(
            "/api/v1/tools/steadi-tug",
            json=tug_payload(),
        ),

        client.post(
            "/api/v1/tools/steadi-chair-stand-30s",
            json=chair_payload(),
        ),

        client.post(
            "/api/v1/tools/steadi-four-stage-balance",
            json=balance_payload(),
        ),

        client.post(
            "/api/v1/tools/steadi-orthostatic-bp",
            json=orthostatic_payload(),
        ),
    )

    for response in responses:
        assert response.status_code == 200

        result = response.json()

        assert (
            result[
                "national_sus_threshold_applied"
            ]
            is False
        )

        assert (
            result[
                "automatic_cross_instrument_inference_applied"
            ]
            is False
        )

        assert (
            result[
                "synthetic_cross_instrument_score_applied"
            ]
            is False
        )


def test_openapi_exposes_all_eight_steadi_routes():
    openapi = main.app.openapi()

    paths = openapi[
        "paths"
    ]

    expected = {
        "/api/v1/tools/steadi-tug",
        "/api/v1/tools/steadi-tug/meta",
        "/api/v1/tools/steadi-chair-stand-30s",
        "/api/v1/tools/steadi-chair-stand-30s/meta",
        "/api/v1/tools/steadi-four-stage-balance",
        "/api/v1/tools/steadi-four-stage-balance/meta",
        "/api/v1/tools/steadi-orthostatic-bp",
        "/api/v1/tools/steadi-orthostatic-bp/meta",
    }

    assert expected.issubset(
        paths
    )

    for path in expected:
        if path.endswith(
            "/meta"
        ):
            assert (
                "get"
                in paths[path]
            )
        else:
            assert (
                "post"
                in paths[path]
            )


def test_openapi_chair_age_is_open_ended_above_60():
    openapi = main.app.openapi()

    schema = (
        openapi[
            "components"
        ][
            "schemas"
        ][
            "SteadiChairStand30sInput"
        ]
    )

    age = schema[
        "properties"
    ][
        "age_years"
    ]

    assert age[
        "minimum"
    ] == 60

    assert (
        "maximum"
        not in age
    )


def test_openapi_protocol_confirmation_fields_are_required():
    openapi = main.app.openapi()

    schemas = (
        openapi[
            "components"
        ][
            "schemas"
        ]
    )

    expected = {
        "SteadiTUGInput":
            "standard_3m_protocol_confirmed",

        "SteadiChairStand30sInput":
            "standard_30_second_protocol_confirmed",

        "SteadiFourStageBalanceInput":
            "standard_four_stage_protocol_confirmed",

        "SteadiOrthostaticBPInput":
            "standard_5_1_3_protocol_confirmed",
    }

    for (
        schema_name,
        field_name,
    ) in expected.items():
        required = schemas[
            schema_name
        ][
            "required"
        ]

        assert (
            field_name
            in required
        )
