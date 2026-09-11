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
    / "falls_function_brazil_2026.json"
)


AUDIT_PATH = (
    ROOT
    / "data"
    / "brazil_clinical_harmonization.json"
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


def test_source_dossier_exists_and_blocks_implementation_until_review():
    assert SOURCE_PATH.is_file()

    data = source()

    assert (
        data["implementation_status"]
        == "source_review_complete_implementation_pending"
    )

    assert (
        data["brazil_applicability_status"]
        == "national_standard"
    )


def test_current_caderneta_is_2026_national_primary_source():
    caderneta = source()[
        "primary_brazil_framework"
    ][
        "caderneta_2026"
    ]

    assert caderneta["year"] == 2026

    assert (
        caderneta["published"]
        == "2026-06-19"
    )

    assert (
        caderneta["source_type"]
        == "national_standard"
    )

    assert (
        caderneta["older_person_age_years"]
        == 60
    )


def test_brazil_falls_checklist_is_yes_no_without_imported_weighted_score():
    checklist = source()[
        "primary_brazil_framework"
    ][
        "caderneta_2026"
    ][
        "falls_checklist"
    ]

    assert checklist["item_count"] == 12

    assert (
        checklist["response_format"]
        == "yes_no"
    )

    assert (
        checklist[
            "numeric_weighting_in_current_caderneta"
        ]
        is False
    )

    assert (
        checklist["action_rule"]
        == "seek assessment if any item is answered yes"
    )

    assert len(checklist["domains"]) == 12


def test_ivcf20_is_current_national_aps_layer():
    ivcf = source()[
        "primary_brazil_framework"
    ][
        "ivcf20"
    ]

    assert (
        "e-SUS APS PEC"
        in ivcf["national_digital_integration"]
    )

    assert (
        "e-SUS Território"
        in ivcf["national_digital_integration"]
    )

    assert (
        ivcf["population"]["age_years_gte"]
        == 60
    )


def test_ivcf20_risk_categories_and_reapplication():
    ivcf = source()[
        "primary_brazil_framework"
    ][
        "ivcf20"
    ]

    assert ivcf["risk_categories"] == {
        "low": "0-6",
        "moderate": "7-14",
        "high": "15-40",
    }

    repeat = ivcf[
        "minimum_reapplication"
    ]

    assert repeat[
        "score_0_6_months"
    ] == 12

    assert repeat[
        "score_gt_6_months"
    ] == 6

    assert repeat[
        "sentinel_event_requires_reassessment"
    ] is True


def test_fall_is_ivcf_sentinel_event():
    assert (
        source()[
            "primary_brazil_framework"
        ][
            "ivcf20"
        ][
            "falls_as_sentinel_event"
        ]
        is True
    )


def test_ivcf_mobility_rules_are_not_tug():
    mobility = source()[
        "primary_brazil_framework"
    ][
        "ivcf20"
    ][
        "mobility_components_relevant_to_item7"
    ]

    gait = mobility[
        "four_meter_gait"
    ]

    assert (
        gait["finding"]
        == "time greater than 5 seconds"
    )

    assert (
        "not a TUG substitute"
        in gait["role"]
    )

    assert (
        mobility[
            "two_or_more_falls_previous_year"
        ]
        is True
    )


def test_current_caderneta_records_bp_postures_without_steadi_protocol_claim():
    record = source()[
        "primary_brazil_framework"
    ][
        "caderneta_2026"
    ][
        "clinical_record"
    ]

    assert record[
        "blood_pressure_positions"
    ] == [
        "lying",
        "sitting",
        "standing",
    ]

    assert (
        record[
            "explicit_current_orthostatic_numeric_cutoff"
        ]
        is False
    )


def test_no_national_tug_chair_or_four_stage_cutoff_was_identified():
    review = source()[
        "requested_item7_tests_brazil_review"
    ]

    for key in (
        "timed_up_and_go",
        "thirty_second_chair_stand",
        "four_stage_balance",
    ):
        assert (
            review[key][
                "generic_national_sus_cutoff_identified"
            ]
            is False
        )


def test_complementary_steadi_tug_chair_and_balance_contract():
    steadi = source()[
        "complementary_steadi"
    ]

    assert (
        steadi["tug"][
            "risk_if_seconds_gte"
        ]
        == 12
    )

    assert (
        steadi[
            "chair_stand_30s"
        ][
            "below_average_if_repetitions_lt"
        ][
            "60-64"
        ][
            "men"
        ]
        == 14
    )

    assert (
        steadi[
            "chair_stand_30s"
        ][
            "below_average_if_repetitions_lt"
        ][
            "90-94"
        ][
            "women"
        ]
        == 4
    )

    assert (
        steadi[
            "four_stage_balance"
        ][
            "increased_fall_risk_if_tandem_seconds_lt"
        ]
        == 10
    )


def test_complementary_steadi_orthostatic_contract():
    ortho = source()[
        "complementary_steadi"
    ][
        "orthostatic_blood_pressure"
    ]

    assert (
        ortho["supine_rest_minutes"]
        == 5
    )

    assert (
        ortho["standing_measurement_minutes"]
        == [1, 3]
    )

    assert (
        ortho[
            "abnormal_if_systolic_drop_mm_hg_gte"
        ]
        == 20
    )

    assert (
        ortho[
            "abnormal_if_diastolic_drop_mm_hg_gte"
        ]
        == 10
    )

    assert (
        ortho[
            "abnormal_if_lightheaded_or_dizzy"
        ]
        is True
    )


def test_item7_governance_is_ready_for_brazil_first_implementation():
    item7 = audit()[
        "future_items"
    ][
        "7"
    ]

    assert (
        item7["implementation_state"]
        == "source_review_complete_implementation_pending"
    )

    assert (
        item7["brazil_applicability_status"]
        == "national_standard"
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
