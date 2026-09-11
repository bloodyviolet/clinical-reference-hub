from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parents[1]


SOURCE_PATH = (
    ROOT
    / "data"
    / "clinical-sources"
    / "falls_function_steadi_complementary.json"
)


AUDIT_PATH = (
    ROOT
    / "data"
    / "brazil_clinical_harmonization.json"
)


DOC_PATH = (
    ROOT
    / "docs"
    / "FALLS_FUNCTION_STEADI_SOURCE_VERIFICATION.md"
)


def source():
    return json.loads(
        SOURCE_PATH.read_text(
            encoding="utf-8"
        )
    )


def audit():
    return json.loads(
        AUDIT_PATH.read_text(
            encoding="utf-8"
        )
    )


def test_source_dossier_is_source_only_and_complementary():
    data = source()

    assert (
        data["implementation_status"]
        == "source_review_complete_implementation_pending"
    )

    assert (
        data["source_role"]
        == "complementary_international_guidance"
    )

    assert (
        data["brazil_applicability_status"]
        == "no_national_variant_identified"
    )

    assert (
        data[
            "national_sus_adoption_of_steadi_identified"
        ]
        is False
    )


def test_brazil_primary_checkpoint_is_locked():
    assert (
        source()[
            "brazil_primary_checkpoint"
        ]
        == "78add2d1572d79179b66440114f703bdbdfd9fc6"
    )


def test_current_resource_retains_four_assessments():
    resource = source()[
        "current_resource"
    ]

    assert (
        resource[
            "current_page_retains_all_four_assessments"
        ]
        is True
    )

    assert set(
        resource[
            "assessments"
        ]
    ) == {
        "Timed Up and Go",
        "30-Second Chair Stand",
        "4-Stage Balance",
        "Measuring Orthostatic Blood Pressure",
    }


def test_tug_exact_contract():
    tug = source()[
        "timed_up_and_go"
    ]

    assert tug["course_distance_m"] == 3
    assert tug["course_distance_ft"] == 10

    assert (
        tug[
            "usual_walking_aid_allowed_if_needed"
        ]
        is True
    )

    assert (
        tug[
            "increased_fall_risk_if_seconds_gte"
        ]
        == 12
    )

    assert (
        tug[
            "not_equivalent_to_ivcf_four_meter_gait"
        ]
        is True
    )


def test_chair_stand_exact_reference_table():
    chair = source()[
        "chair_stand_30s"
    ]

    assert (
        chair[
            "arms_required_to_stand_rule"
        ]
        == "stop test and record zero"
    )

    assert (
        chair[
            "cutoff_semantics"
        ]
        == (
            "below_average_if_repetitions_"
            "strictly_less_than_threshold"
        )
    )

    expected = {
        "60-64": {
            "men": 14,
            "women": 12,
        },
        "65-69": {
            "men": 12,
            "women": 11,
        },
        "70-74": {
            "men": 12,
            "women": 10,
        },
        "75-79": {
            "men": 11,
            "women": 10,
        },
        "80-84": {
            "men": 10,
            "women": 9,
        },
        "85-89": {
            "men": 8,
            "women": 8,
        },
        "90-94": {
            "men": 7,
            "women": 4,
        },
    }

    assert (
        chair[
            "below_average_if_repetitions_lt"
        ]
        == expected
    )


def test_chair_stand_does_not_extrapolate_beyond_94():
    chair = source()[
        "chair_stand_30s"
    ]

    assert (
        chair[
            "reference_table_age_range_years"
        ]
        == {
            "minimum": 60,
            "maximum": 94,
        }
    )

    assert (
        chair[
            "cutoff_extrapolation_beyond_age_94_allowed"
        ]
        is False
    )


def test_four_stage_exact_contract():
    balance = source()[
        "four_stage_balance"
    ]

    assert balance[
        "target_seconds_per_position"
    ] == 10

    assert (
        balance[
            "progress_only_if_position_held_for_seconds"
        ]
        == 10
    )

    assert (
        balance[
            "increased_fall_risk_if_tandem_seconds_lt"
        ]
        == 10
    )

    assert (
        balance[
            "assistive_device_allowed_during_test"
        ]
        is False
    )

    assert balance["eyes_open"] is True


def test_orthostatic_exact_contract():
    bp = source()[
        "orthostatic_blood_pressure"
    ]

    assert bp[
        "supine_rest_minutes"
    ] == 5

    assert bp[
        "standing_measurement_minutes"
    ] == [
        1,
        3,
    ]

    assert (
        bp[
            "abnormal_if_systolic_drop_mm_hg_gte"
        ]
        == 20
    )

    assert (
        bp[
            "abnormal_if_diastolic_drop_mm_hg_gte"
        ]
        == 10
    )

    assert (
        bp[
            "abnormal_if_lightheaded_or_dizzy"
        ]
        is True
    )

    assert (
        bp["abnormal_rule"]
        == "any_of"
    )


def test_brazil_boundary_remains_explicit():
    boundary = source()[
        "brazil_boundary"
    ]

    assert boundary[
        "primary_national_layer_remains"
    ] == [
        "Caderneta Brasileira da Pessoa Idosa 2026",
        "IVCF-20",
    ]

    assert (
        boundary[
            "generic_national_sus_tug_cutoff_identified"
        ]
        is False
    )

    assert (
        boundary[
            "generic_national_sus_chair_stand_cutoff_identified"
        ]
        is False
    )

    assert (
        boundary[
            "generic_national_sus_four_stage_cutoff_identified"
        ]
        is False
    )

    assert (
        boundary[
            "caderneta_2026_defines_full_steadi_orthostatic_timing"
        ]
        is False
    )


def test_no_cross_instrument_synthesis_allowed():
    data = source()

    assert (
        data[
            "synthetic_cross_instrument_score_allowed"
        ]
        is False
    )

    assert (
        data[
            "automatic_cross_instrument_inference_allowed"
        ]
        is False
    )


def test_durable_boundary_ids_are_complete():
    ids = {
        row["id"]
        for row in source()[
            "durable_boundaries"
        ]
    }

    assert ids == {
        "STEADI-BRAZIL-LAYER-01",
        "STEADI-SYNTHETIC-SCORE-02",
        "STEADI-TUG-IVCF-03",
        "STEADI-CHAIR-AGE-04",
        "STEADI-CHAIR-STRICT-05",
        "STEADI-BALANCE-DEVICE-06",
        "STEADI-BP-BRAZIL-07",
    }


def test_item7_harmonization_records_complementary_gate():
    item7 = audit()[
        "future_items"
    ][
        "7"
    ]

    assert (
        item7[
            "brazil_primary_checkpoint"
        ]
        == "78add2d1572d79179b66440114f703bdbdfd9fc6"
    )

    assert (
        item7[
            "brazil_primary_implementation_state"
        ]
        == "qualified_committed_pushed"
    )

    assert (
        item7[
            "complementary_steadi_source_review_status"
        ]
        == "pass"
    )

    assert (
        item7[
            "complementary_steadi_implementation_state"
        ]
        == "implementation_complete"
    )

    assert (
        item7[
            "complementary_steadi_brazil_applicability_status"
        ]
        == "no_national_variant_identified"
    )

    assert (
        item7[
            "national_steadi_adoption_identified"
        ]
        is False
    )

    assert (
        item7[
            "synthetic_cross_instrument_score_allowed"
        ]
        is False
    )


def test_source_verification_document_exists():
    assert DOC_PATH.is_file()

    text = DOC_PATH.read_text(
        encoding="utf-8"
    )

    for token in (
        "STEADI-BRAZIL-LAYER-01",
        "STEADI-SYNTHETIC-SCORE-02",
        "STEADI-TUG-IVCF-03",
        "STEADI-CHAIR-AGE-04",
        "STEADI-CHAIR-STRICT-05",
        "STEADI-BALANCE-DEVICE-06",
        "STEADI-BP-BRAZIL-07",
    ):
        assert token in text
