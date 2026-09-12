from datetime import date

import pytest

import schemas

from clinical_tools.pni_2026 import (
    evaluate_pni_hepatitis_a_child_routine,
)


ASSESSMENT_DATE = date(
    2026,
    9,
    11,
)


def history(
    state,
    *,
    doses=None,
):
    return schemas.PniVaccineHistory(
        vaccine_key="hepatitis_a",
        history_state=state,
        doses=doses or [],
    )


def dose(
    administration_date,
):
    return schemas.PniDoseRecord(
        administration_date=administration_date,
        product_key="hepatitis_a",
        documentation_source="official_registry",
    )


def evaluate(
    *,
    date_of_birth=date(
        2025,
        6,
        11,
    ),
    history_value=None,
    safety="screened_no_concern",
):
    result = (
        evaluate_pni_hepatitis_a_child_routine(
            assessment_date=ASSESSMENT_DATE,
            date_of_birth=date_of_birth,
            history=history_value,
            administration_safety_screen_state=safety,
        )
    )

    validated = (
        schemas
        .PniRuleResult
        .model_validate(
            result
        )
    )

    assert (
        validated.interpretation_pt.strip()
    )

    assert (
        validated.interpretation_en.strip()
    )

    assert (
        validated.interpretation_pt
        != validated.interpretation_en
    )

    assert (
        validated.special_condition_inferred
        is False
    )

    assert (
        validated.synthetic_score_applied
        is False
    )

    return result


def test_rule_id_is_stable():
    from clinical_tools import pni_2026

    assert (
        pni_2026.HEPATITIS_A_CHILD_RULE_ID
        == "PNI26-HA-CHILD-ROUTINE-001"
    )


def test_child_under_12_months_is_not_due():
    result = evaluate(
        date_of_birth=date(
            2026,
            1,
            1,
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "not_due_now"
    )


def test_child_at_14_months_is_not_due_by_routine_agenda():
    result = evaluate(
        date_of_birth=date(
            2025,
            7,
            11,
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "not_due_now"
    )


def test_exact_15_months_unknown_history_requires_history():
    result = evaluate(
        history_value=history(
            "unknown"
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "history_required"
    )


def test_exact_15_months_documented_zero_recommends_now():
    result = evaluate(
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "recommend_now"
    )


def test_missed_opportunity_before_fifth_birthday_recommends_now():
    result = evaluate(
        date_of_birth=date(
            2021,
            9,
            12,
        ),
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "recommend_now"
    )


def test_exact_fifth_birthday_without_valid_dose_is_not_applicable():
    result = evaluate(
        date_of_birth=date(
            2021,
            9,
            11,
        ),
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "not_applicable"
    )


def test_documented_dose_at_12_months_satisfies_child_rule():
    dob = date(
        2024,
        1,
        1,
    )

    result = evaluate(
        date_of_birth=dob,
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    date(
                        2025,
                        1,
                        1,
                    )
                ),
            ],
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "not_due_now"
    )


def test_documented_dose_at_15_months_satisfies_child_rule():
    dob = date(
        2024,
        1,
        1,
    )

    result = evaluate(
        date_of_birth=dob,
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    date(
                        2025,
                        4,
                        1,
                    )
                ),
            ],
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "not_due_now"
    )


def test_documented_dose_before_12_months_routes_special_review():
    dob = date(
        2024,
        1,
        1,
    )

    result = evaluate(
        date_of_birth=dob,
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    date(
                        2024,
                        12,
                        1,
                    )
                ),
            ],
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_missing_history_in_due_window_requires_history():
    result = evaluate(
        history_value=None,
    )

    assert (
        result[
            "decision"
        ]
        == "history_required"
    )


def test_unscreened_due_dose_does_not_auto_recommend():
    result = evaluate(
        history_value=history(
            "documented_zero_dose"
        ),
        safety="not_screened",
    )

    assert (
        result[
            "decision"
        ]
        == "context_required"
    )

    assert result[
        "missing_context"
    ] == [
        "administration_safety_screen_state",
    ]


def test_safety_concern_routes_special_review():
    result = evaluate(
        history_value=history(
            "documented_zero_dose"
        ),
        safety="screened_concern",
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_future_dose_is_rejected():
    with pytest.raises(
        ValueError,
        match="cannot follow assessment_date",
    ):
        evaluate(
            history_value=history(
                "documented_doses",
                doses=[
                    dose(
                        date(
                            2026,
                            9,
                            12,
                        )
                    ),
                ],
            ),
        )


def test_dose_before_birth_is_rejected():
    with pytest.raises(
        ValueError,
        match="cannot precede date_of_birth",
    ):
        evaluate(
            history_value=history(
                "documented_doses",
                doses=[
                    dose(
                        date(
                            2025,
                            1,
                            1,
                        )
                    ),
                ],
            ),
        )


def test_wrong_vaccine_history_key_is_rejected():
    wrong = schemas.PniVaccineHistory(
        vaccine_key="hepatitis_b",
        history_state="documented_zero_dose",
    )

    with pytest.raises(
        ValueError,
        match="vaccine_key=hepatitis_a",
    ):
        evaluate(
            history_value=wrong,
        )


def test_no_spacing_interval_is_invented():
    result = evaluate(
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert (
        result[
            "recommended_interval_days"
        ]
        is None
    )

    assert (
        result[
            "minimum_interval_days"
        ]
        is None
    )

    assert (
        result[
            "minimum_interval_applied"
        ]
        is False
    )


def test_provenance_is_national_2026_source():
    result = evaluate(
        history_value=history(
            "documented_zero_dose"
        ),
    )

    provenance = result[
        "provenance"
    ]

    assert (
        provenance[
            "rule_id"
        ]
        == "PNI26-HA-CHILD-ROUTINE-001"
    )

    assert (
        provenance[
            "authority"
        ]
        == "Ministério da Saúde / SVSA / DPNI"
    )

    assert (
        provenance[
            "source_snapshot_date"
        ]
        == date(
            2026,
            9,
            11,
        )
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "date_of_birth":
                date(
                    2026,
                    1,
                    1,
                ),
        },
        {
            "history_value":
                history(
                    "documented_zero_dose"
                ),
        },
        {
            "history_value":
                history(
                    "documented_zero_dose"
                ),
            "safety":
                "not_screened",
        },
        {
            "history_value":
                history(
                    "documented_zero_dose"
                ),
            "safety":
                "screened_concern",
        },
        {
            "date_of_birth":
                date(
                    2021,
                    9,
                    11,
                ),
            "history_value":
                history(
                    "documented_zero_dose"
                ),
        },
    ],
)
def test_representative_results_are_bilingual(
    kwargs,
):
    result = evaluate(
        **kwargs
    )

    assert (
        len(
            result[
                "interpretation_pt"
            ]
        )
        > 20
    )

    assert (
        len(
            result[
                "interpretation_en"
            ]
        )
        > 20
    )

    assert (
        result[
            "interpretation_pt"
        ]
        != result[
            "interpretation_en"
        ]
    )
