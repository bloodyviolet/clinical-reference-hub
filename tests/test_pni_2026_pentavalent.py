from datetime import date, timedelta

import pytest

import schemas

from clinical_tools.pni_2026 import (
    evaluate_pni_pentavalent_child_routine,
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
        vaccine_key="pentavalent",
        history_state=state,
        doses=doses or [],
        reported_prior_doses_without_exact_dates=reported_prior,
    )


def dose(
    administration_date,
):
    return schemas.PniDoseRecord(
        administration_date=administration_date,
        product_key="pentavalent",
        documentation_source="official_registry",
    )


def evaluate(
    assessment,
    *,
    history_value,
    safety="screened_no_concern",
    early=False,
    exception=False,
    dob=DOB,
):
    result = evaluate_pni_pentavalent_child_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        history=history_value,
        administration_safety_screen_state=safety,
        exceptional_early_start_authorized=early,
        exceptional_minimum_interval_authorized=exception,
    )

    validated = schemas.PniRuleResult.model_validate(
        result
    )

    assert validated.interpretation_pt.strip()
    assert validated.interpretation_en.strip()

    assert (
        validated.interpretation_pt
        != validated.interpretation_en
    )

    assert validated.special_condition_inferred is False
    assert validated.synthetic_score_applied is False

    return result


def test_rule_id():
    from clinical_tools import pni_2026

    assert (
        pni_2026.PENTAVALENT_CHILD_RULE_ID
        == "PNI26-PENTAVALENT-CHILD-ROUTINE-001"
    )


def test_before_absolute_minimum_not_due():
    result = evaluate(
        date(
            2026,
            2,
            15,
        ),
        history_value=history(
            "documented_zero_dose"
        ),
        early=True,
    )

    assert result["decision"] == "not_due_now"


def test_exact_1m15d_without_exception_not_due():
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

    assert result["decision"] == "not_due_now"


def test_exact_1m15d_with_explicit_early_start_recommends():
    result = evaluate(
        date(
            2026,
            2,
            16,
        ),
        history_value=history(
            "documented_zero_dose"
        ),
        early=True,
    )

    assert result["decision"] == "recommend_now"


def test_exact_two_months_recommends_without_exception():
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

    assert result["decision"] == "recommend_now"


def test_exact_upper_age_active():
    result = evaluate(
        date(
            2032,
            12,
            30,
        ),
        dob=DOB,
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "recommend_now"


def test_day_after_project_upper_boundary_closes_layer():
    result = evaluate(
        date(
            2032,
            12,
            31,
        ),
        dob=DOB,
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "not_applicable"


def test_unknown_history_not_zero():
    result = evaluate(
        date(
            2026,
            4,
            1,
        ),
        history_value=history(
            "unknown"
        ),
    )

    assert result["decision"] == "history_required"


def test_partial_history_not_zero():
    result = evaluate(
        date(
            2026,
            4,
            1,
        ),
        history_value=history(
            "partial_record",
            reported_prior=1,
        ),
    )

    assert result["decision"] == "history_required"


def test_undated_prior_dose_requires_history():
    # An undated-only record is not "documented_doses":
    # PniVaccineHistory requires that state to contain at least one
    # exact dated dose.  Known prior dose evidence without an exact
    # date is correctly represented as partial_record.
    result = evaluate(
        date(
            2026,
            4,
            1,
        ),
        history_value=history(
            "partial_record",
            reported_prior=1,
        ),
    )

    assert result["decision"] == "history_required"


def test_documented_d1_before_1m15d_routes_review():
    result = evaluate(
        date(
            2026,
            4,
            20,
        ),
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    date(
                        2026,
                        2,
                        15,
                    )
                ),
            ],
        ),
        early=True,
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_historical_early_d1_requires_explicit_confirmation():
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
        early=False,
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_confirmed_historical_early_d1_can_progress_to_d2():
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
        early=True,
    )

    assert result["decision"] == "recommend_now"


def test_d2_day29_not_due_even_with_exception():
    d1 = date(
        2026,
        3,
        1,
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


def test_d2_day30_without_exception_waits():
    d1 = date(
        2026,
        3,
        1,
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
    )

    assert result["decision"] == "not_due_now"


def test_d2_day30_with_exception_recommends():
    d1 = date(
        2026,
        3,
        1,
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
    assert result["minimum_interval_applied"] is True


def test_d2_day60_recommends():
    d1 = date(
        2026,
        3,
        1,
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
    assert result["minimum_interval_applied"] is False


def test_historical_d1_d2_under_30_routes_review():
    d1 = date(
        2026,
        3,
        1,
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


def test_historical_d1_d2_30_to_59_routes_review():
    d1 = date(
        2026,
        3,
        1,
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


def test_d3_waits_for_four_calendar_months_and_six_month_age():
    d1 = date(
        2026,
        3,
        1,
    )

    d2 = date(
        2026,
        4,
        30,
    )

    result = evaluate(
        date(
            2026,
            6,
            30,
        ),
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


def test_d3_exact_six_months_and_four_months_from_d1_recommends():
    d1 = date(
        2026,
        3,
        1,
    )

    d2 = date(
        2026,
        5,
        1,
    )

    result = evaluate(
        date(
            2026,
            7,
            1,
        ),
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

    assert result["decision"] == "recommend_now"


def test_d3_exceptional_30_day_interval_still_requires_other_constraints():
    d1 = date(
        2026,
        3,
        1,
    )

    d2 = date(
        2026,
        5,
        31,
    )

    result = evaluate(
        date(
            2026,
            7,
            1,
        ),
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
        exception=True,
    )

    assert result["decision"] == "recommend_now"
    assert result["minimum_interval_applied"] is True


def test_d3_same_case_without_exception_waits():
    d1 = date(
        2026,
        3,
        1,
    )

    d2 = date(
        2026,
        5,
        31,
    )

    result = evaluate(
        date(
            2026,
            7,
            1,
        ),
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
        exception=False,
    )

    assert result["decision"] == "not_due_now"


def test_valid_three_dose_series_complete():
    result = evaluate(
        date(
            2026,
            7,
            1,
        ),
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    date(
                        2026,
                        3,
                        1,
                    )
                ),
                dose(
                    date(
                        2026,
                        5,
                        1,
                    )
                ),
                dose(
                    date(
                        2026,
                        7,
                        1,
                    )
                ),
            ],
        ),
    )

    assert result["decision"] == "not_due_now"

    assert (
        "DTP"
        in result[
            "interpretation_pt"
        ]
    )


def test_historical_d3_before_six_months_routes_review():
    result = evaluate(
        date(
            2026,
            6,
            16,
        ),
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    date(
                        2026,
                        2,
                        16,
                    )
                ),
                dose(
                    date(
                        2026,
                        4,
                        17,
                    )
                ),
                dose(
                    date(
                        2026,
                        6,
                        16,
                    )
                ),
            ],
        ),
        early=True,
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_historical_d1_to_d3_under_four_calendar_months_routes_review():
    result = evaluate(
        date(
            2026,
            8,
            29,
        ),
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    date(
                        2026,
                        5,
                        1,
                    )
                ),
                dose(
                    date(
                        2026,
                        6,
                        30,
                    )
                ),
                dose(
                    date(
                        2026,
                        8,
                        29,
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


def test_more_than_three_penta_doses_routes_review():
    result = evaluate(
        date(
            2027,
            1,
            1,
        ),
        history_value=history(
            "documented_doses",
            doses=[
                dose(date(2026, 3, 1)),
                dose(date(2026, 5, 1)),
                dose(date(2026, 7, 1)),
                dose(date(2026, 12, 1)),
            ],
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


@pytest.mark.parametrize(
    "wrong_key",
    [
        "hepatitis_b",
        "dtp",
        "hexa_acellular_rie",
    ],
)
def test_other_component_or_related_keys_do_not_count_as_penta(
    wrong_key,
):
    wrong = schemas.PniVaccineHistory(
        vaccine_key=wrong_key,
        history_state="documented_zero_dose",
    )

    with pytest.raises(
        ValueError,
        match="vaccine_key=pentavalent",
    ):
        evaluate(
            date(
                2026,
                3,
                1,
            ),
            history_value=wrong,
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


def test_early_start_flag_requires_boolean():
    with pytest.raises(
        ValueError,
        match="exceptional_early_start_authorized must be boolean",
    ):
        evaluate_pni_pentavalent_child_routine(
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
            exceptional_early_start_authorized=1,
        )


def test_interval_exception_flag_requires_boolean():
    with pytest.raises(
        ValueError,
        match="exceptional_minimum_interval_authorized",
    ):
        evaluate_pni_pentavalent_child_routine(
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


def test_future_dose_rejected():
    with pytest.raises(
        ValueError,
        match="cannot follow assessment_date",
    ):
        evaluate(
            date(
                2026,
                4,
                1,
            ),
            history_value=history(
                "documented_doses",
                doses=[
                    dose(
                        date(
                            2026,
                            4,
                            2,
                        )
                    ),
                ],
            ),
        )


@pytest.mark.parametrize(
    "assessment,history_value,early,exception",
    [
        (
            date(
                2026,
                3,
                1,
            ),
            history(
                "documented_zero_dose"
            ),
            False,
            False,
        ),
        (
            date(
                2026,
                2,
                16,
            ),
            history(
                "documented_zero_dose"
            ),
            True,
            False,
        ),
        (
            date(
                2026,
                4,
                1,
            ),
            history(
                "unknown"
            ),
            False,
            False,
        ),
        (
            date(
                2026,
                7,
                1,
            ),
            history(
                "documented_doses",
                doses=[
                    dose(
                        date(
                            2026,
                            3,
                            1,
                        )
                    ),
                    dose(
                        date(
                            2026,
                            5,
                            1,
                        )
                    ),
                ],
            ),
            False,
            False,
        ),
    ],
)
def test_representative_results_are_bilingual(
    assessment,
    history_value,
    early,
    exception,
):
    result = evaluate(
        assessment,
        history_value=history_value,
        early=early,
        exception=exception,
    )

    assert result["interpretation_pt"].strip()
    assert result["interpretation_en"].strip()

    assert (
        result[
            "interpretation_pt"
        ]
        != result[
            "interpretation_en"
        ]
    )
