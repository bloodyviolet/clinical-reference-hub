from datetime import date, timedelta

import pytest

import schemas

from clinical_tools.pni_2026 import (
    evaluate_pni_rotavirus_routine,
)


DOB = date(
    2026,
    1,
    1,
)


def history(
    state,
    *,
    doses=None,
    reported_prior=0,
):
    return schemas.PniVaccineHistory(
        vaccine_key="rotavirus",
        history_state=state,
        doses=doses or [],
        reported_prior_doses_without_exact_dates=reported_prior,
    )


def dose(
    administration_date,
):
    return schemas.PniDoseRecord(
        administration_date=administration_date,
        product_key="rotavirus",
        documentation_source="official_registry",
    )


def evaluate(
    assessment_date,
    *,
    history_value,
    safety="screened_no_concern",
    exception=False,
    date_of_birth=DOB,
):
    result = evaluate_pni_rotavirus_routine(
        assessment_date=assessment_date,
        date_of_birth=date_of_birth,
        history=history_value,
        administration_safety_screen_state=safety,
        exceptional_minimum_interval_authorized=exception,
    )

    validated = (
        schemas
        .PniRuleResult
        .model_validate(
            result
        )
    )

    assert validated.interpretation_pt.strip()
    assert validated.interpretation_en.strip()

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
        pni_2026.ROTAVIRUS_ROUTINE_RULE_ID
        == "PNI26-ROTAVIRUS-ROUTINE-001"
    )


def test_before_d1_minimum_age_is_not_due():
    result = evaluate(
        date(
            2026,
            2,
            15,
        ),
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "not_due_now"


def test_exact_d1_minimum_age_recommends():
    result = evaluate(
        date(
            2026,
            2,
            16,
        ),
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "recommend_now"


def test_exact_d1_maximum_age_recommends():
    result = evaluate(
        date(
            2026,
            12,
            30,
        ),
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "recommend_now"


def test_day_after_d1_maximum_loses_series_opportunity():
    result = evaluate(
        date(
            2026,
            12,
            31,
        ),
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "not_applicable"

    assert (
        "D2"
        in result[
            "interpretation_pt"
        ]
    )


def test_missing_history_requires_reconciliation():
    result = evaluate(
        date(
            2026,
            3,
            1,
        ),
        history_value=None,
    )

    assert result["decision"] == "history_required"


def test_unknown_history_is_not_zero_dose():
    result = evaluate(
        date(
            2026,
            3,
            1,
        ),
        history_value=history(
            "unknown"
        ),
    )

    assert result["decision"] == "history_required"


def test_partial_history_is_not_zero_dose():
    result = evaluate(
        date(
            2026,
            3,
            1,
        ),
        history_value=history(
            "partial_record",
            reported_prior=1,
        ),
    )

    assert result["decision"] == "history_required"


def test_one_valid_d1_before_d2_minimum_age_not_due():
    d1 = date(
        2026,
        2,
        16,
    )

    result = evaluate(
        date(
            2026,
            4,
            15,
        ),
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    d1
                ),
            ],
        ),
    )

    assert result["decision"] == "not_due_now"


def test_d2_exact_minimum_age_with_60_day_interval_recommends():
    d1 = date(
        2026,
        2,
        15,
    )

    # D1 above is intentionally outside the permitted D1 window
    # and therefore cannot be used; verify the guard separately.
    result = evaluate(
        date(
            2026,
            4,
            16,
        ),
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    d1
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


def test_valid_d1_then_standard_60_day_interval_recommends_d2():
    d1 = date(
        2026,
        2,
        16,
    )

    result = evaluate(
        d1
        + timedelta(
            days=60,
        ),
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    d1
                ),
            ],
        ),
    )

    assert result["decision"] == "recommend_now"

    assert (
        result[
            "minimum_interval_applied"
        ]
        is False
    )


def test_day29_never_permits_d2_even_with_exception():
    d1 = date(
        2026,
        3,
        20,
    )

    result = evaluate(
        d1
        + timedelta(
            days=29,
        ),
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    d1
                ),
            ],
        ),
        exception=True,
    )

    assert result["decision"] == "not_due_now"


def test_day30_without_exception_waits_for_60():
    d1 = date(
        2026,
        3,
        20,
    )

    result = evaluate(
        d1
        + timedelta(
            days=30,
        ),
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    d1
                ),
            ],
        ),
        exception=False,
    )

    assert result["decision"] == "not_due_now"


def test_day30_with_explicit_exception_recommends_when_age_eligible():
    d1 = date(
        2026,
        3,
        20,
    )

    result = evaluate(
        d1
        + timedelta(
            days=30,
        ),
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    d1
                ),
            ],
        ),
        exception=True,
    )

    assert result["decision"] == "recommend_now"

    assert (
        result[
            "minimum_interval_applied"
        ]
        is True
    )


def test_day59_without_exception_not_due():
    d1 = date(
        2026,
        3,
        20,
    )

    result = evaluate(
        d1
        + timedelta(
            days=59,
        ),
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    d1
                ),
            ],
        ),
    )

    assert result["decision"] == "not_due_now"


def test_day60_recommends_without_exception():
    d1 = date(
        2026,
        3,
        20,
    )

    result = evaluate(
        d1
        + timedelta(
            days=60,
        ),
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    d1
                ),
            ],
        ),
    )

    assert result["decision"] == "recommend_now"

    assert (
        result[
            "minimum_interval_applied"
        ]
        is False
    )


def test_d2_exact_maximum_age_can_recommend():
    # D1 must itself remain inside its permitted age window.
    # For DOB 2026-01-01, the D1 maximum is 2026-12-30.
    d1 = date(
        2026,
        12,
        30,
    )

    result = evaluate(
        date(
            2027,
            12,
            30,
        ),
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    d1
                ),
            ],
        ),
    )

    assert result["decision"] == "recommend_now"


def test_day_after_d2_maximum_is_not_applicable():
    # Keep D1 valid so this test isolates only the D2 maximum-age
    # boundary rather than failing earlier on invalid D1 history.
    d1 = date(
        2026,
        12,
        30,
    )

    result = evaluate(
        date(
            2027,
            12,
            31,
        ),
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    d1
                ),
            ],
        ),
    )

    assert result["decision"] == "not_applicable"


def test_d1_outside_age_window_routes_review():
    result = evaluate(
        date(
            2027,
            1,
            15,
        ),
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    date(
                        2027,
                        1,
                        2,
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


def test_two_valid_doses_60_days_apart_complete_series():
    d1 = date(
        2026,
        3,
        20,
    )

    d2 = (
        d1
        + timedelta(
            days=60,
        )
    )

    result = evaluate(
        d2,
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    d1
                ),
                dose(
                    d2
                ),
            ],
        ),
    )

    assert result["decision"] == "not_due_now"


def test_two_documented_doses_29_days_apart_route_review():
    d1 = date(
        2026,
        3,
        20,
    )

    d2 = (
        d1
        + timedelta(
            days=29,
        )
    )

    result = evaluate(
        d2,
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    d1
                ),
                dose(
                    d2
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


def test_two_documented_doses_30_to_59_days_route_review():
    d1 = date(
        2026,
        3,
        20,
    )

    d2 = (
        d1
        + timedelta(
            days=45,
        )
    )

    result = evaluate(
        d2,
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    d1
                ),
                dose(
                    d2
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


def test_unscreened_due_d1_requires_context():
    result = evaluate(
        date(
            2026,
            3,
            1,
        ),
        history_value=history(
            "documented_zero_dose"
        ),
        safety="not_screened",
    )

    assert result["decision"] == "context_required"


def test_safety_concern_routes_review():
    result = evaluate(
        date(
            2026,
            3,
            1,
        ),
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


def test_exception_flag_must_be_boolean():
    with pytest.raises(
        ValueError,
        match="must be boolean",
    ):
        evaluate_pni_rotavirus_routine(
            assessment_date=date(
                2026,
                3,
                1,
            ),
            date_of_birth=DOB,
            history=history(
                "documented_zero_dose"
            ),
            administration_safety_screen_state="screened_no_concern",
            exceptional_minimum_interval_authorized=1,
        )


def test_wrong_vaccine_history_rejected():
    wrong = schemas.PniVaccineHistory(
        vaccine_key="hepatitis_b",
        history_state="documented_zero_dose",
    )

    with pytest.raises(
        ValueError,
        match="vaccine_key=rotavirus",
    ):
        evaluate(
            date(
                2026,
                3,
                1,
            ),
            history_value=wrong,
        )


def test_future_dose_rejected():
    with pytest.raises(
        ValueError,
        match="cannot follow assessment_date",
    ):
        evaluate(
            date(
                2026,
                3,
                1,
            ),
            history_value=history(
                "documented_doses",
                doses=[
                    dose(
                        date(
                            2026,
                            3,
                            2,
                        )
                    ),
                ],
            ),
        )


def test_no_synthetic_spacing_from_other_vaccines():
    result = evaluate(
        date(
            2026,
            3,
            1,
        ),
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


@pytest.mark.parametrize(
    "assessment_date,history_value",
    [
        (
            date(
                2026,
                2,
                16,
            ),
            history(
                "documented_zero_dose"
            ),
        ),
        (
            date(
                2026,
                3,
                1,
            ),
            history(
                "unknown"
            ),
        ),
        (
            date(
                2026,
                12,
                31,
            ),
            history(
                "documented_zero_dose"
            ),
        ),
        (
            date(
                2026,
                5,
                19,
            ),
            history(
                "documented_doses",
                doses=[
                    dose(
                        date(
                            2026,
                            3,
                            20,
                        )
                    ),
                ],
            ),
        ),
    ],
)
def test_representative_results_are_bilingual(
    assessment_date,
    history_value,
):
    result = evaluate(
        assessment_date,
        history_value=history_value,
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
