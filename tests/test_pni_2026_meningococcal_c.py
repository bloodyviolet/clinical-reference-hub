from datetime import date, timedelta

import pytest

import schemas

from clinical_tools.pni_2026 import (
    evaluate_pni_meningococcal_c_infant_routine,
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
        vaccine_key="meningococcal_c",
        history_state=state,
        doses=doses or [],
        reported_prior_doses_without_exact_dates=reported_prior,
    )


def dose(
    administration_date,
):
    return schemas.PniDoseRecord(
        administration_date=administration_date,
        product_key="meningococcal_c",
        documentation_source="official_registry",
    )


def evaluate(
    assessment,
    *,
    history_value,
    safety="screened_no_concern",
    exception=False,
):
    result = evaluate_pni_meningococcal_c_infant_routine(
        assessment_date=assessment,
        date_of_birth=DOB,
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
        validated.special_condition_inferred
        is False
    )

    assert (
        validated.synthetic_score_applied
        is False
    )

    return result


def test_rule_id():
    from clinical_tools import pni_2026

    assert (
        pni_2026.MENINGOCOCCAL_C_INFANT_RULE_ID
        == "PNI26-MENC-INFANT-ROUTINE-001"
    )


def test_before_three_months_not_due():
    result = evaluate(
        date(
            2026,
            3,
            31,
        ),
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "not_due_now"


def test_exact_three_months_zero_history_recommends():
    result = evaluate(
        date(
            2026,
            4,
            1,
        ),
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "recommend_now"


def test_six_months_zero_history_starts_two_dose_catchup():
    result = evaluate(
        date(
            2026,
            7,
            1,
        ),
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "recommend_now"

    assert (
        "duas doses"
        in result[
            "interpretation_pt"
        ].lower()
    )


def test_ten_months_zero_history_still_recommends_menc():
    result = evaluate(
        date(
            2026,
            11,
            1,
        ),
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "recommend_now"


def test_exact_eleven_months_zero_history_recommends_one_menc():
    result = evaluate(
        date(
            2026,
            12,
            1,
        ),
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "recommend_now"

    assert (
        "1 dose"
        in result[
            "interpretation_pt"
        ]
    )

    # Verify the semantic ACWY handoff without coupling the test
    # to one typography/spelling form such as "MenACWY" versus
    # "meningococcal-ACWY".
    assert (
        "acwy"
        in result[
            "interpretation_en"
        ].lower()
    )


def test_day_before_first_birthday_remains_menc_layer():
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

    assert result["decision"] == "recommend_now"


def test_exact_first_birthday_transitions_out_of_menc_layer():
    result = evaluate(
        date(
            2027,
            1,
            1,
        ),
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "not_applicable"

    # Verify the semantic ACWY handoff without coupling the test
    # to one typography/spelling form such as "MenACWY" versus
    # "meningococcal-ACWY".
    assert (
        "acwy"
        in result[
            "interpretation_en"
        ].lower()
    )


def test_one_dose_day29_not_due_even_with_exception():
    d1 = date(
        2026,
        4,
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


def test_one_dose_day30_standard_waits():
    d1 = date(
        2026,
        4,
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


def test_one_dose_day30_exception_recommends():
    d1 = date(
        2026,
        4,
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

    assert (
        result[
            "minimum_interval_applied"
        ]
        is True
    )


def test_one_dose_day60_recommends_without_exception():
    d1 = date(
        2026,
        4,
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

    assert (
        result[
            "minimum_interval_applied"
        ]
        is False
    )


def test_eleven_months_one_dose_and_valid_interval_recommends():
    d1 = date(
        2026,
        9,
        1,
    )

    result = evaluate(
        date(
            2026,
            12,
            1,
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


def test_two_doses_60_days_apart_complete_infant_series():
    d1 = date(
        2026,
        4,
        1,
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


def test_two_doses_under_30_days_route_review():
    d1 = date(
        2026,
        4,
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

    assert result["decision"] == "special_pathway_review"


def test_historical_30_to_59_days_routes_review():
    d1 = date(
        2026,
        4,
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

    assert result["decision"] == "special_pathway_review"


def test_dose_before_three_months_routes_review():
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
                    date(
                        2026,
                        3,
                        15,
                    )
                ),
            ],
        ),
    )

    assert result["decision"] == "special_pathway_review"


def test_unknown_history_requires_history():
    result = evaluate(
        date(
            2026,
            7,
            1,
        ),
        history_value=history(
            "unknown"
        ),
    )

    assert result["decision"] == "history_required"


def test_partial_history_requires_history():
    result = evaluate(
        date(
            2026,
            7,
            1,
        ),
        history_value=history(
            "partial_record",
            reported_prior=1,
        ),
    )

    assert result["decision"] == "history_required"


def test_missing_history_requires_history():
    result = evaluate(
        date(
            2026,
            7,
            1,
        ),
        history_value=None,
    )

    assert result["decision"] == "history_required"


def test_unscreened_due_dose_requires_context():
    result = evaluate(
        date(
            2026,
            4,
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
            4,
            1,
        ),
        history_value=history(
            "documented_zero_dose"
        ),
        safety="screened_concern",
    )

    assert result["decision"] == "special_pathway_review"


def test_menacwy_history_not_accepted_as_menc_history():
    wrong = schemas.PniVaccineHistory(
        vaccine_key="meningococcal_acwy",
        history_state="documented_zero_dose",
    )

    with pytest.raises(
        ValueError,
        match="vaccine_key=meningococcal_c",
    ):
        evaluate(
            date(
                2026,
                7,
                1,
            ),
            history_value=wrong,
        )


def test_exception_flag_requires_boolean():
    with pytest.raises(
        ValueError,
        match="must be boolean",
    ):
        evaluate_pni_meningococcal_c_infant_routine(
            assessment_date=date(
                2026,
                7,
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
                7,
                1,
            ),
            history_value=history(
                "documented_doses",
                doses=[
                    dose(
                        date(
                            2026,
                            7,
                            2,
                        )
                    ),
                ],
            ),
        )


@pytest.mark.parametrize(
    "assessment,history_value",
    [
        (
            date(
                2026,
                4,
                1,
            ),
            history(
                "documented_zero_dose"
            ),
        ),
        (
            date(
                2026,
                7,
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
                1,
            ),
            history(
                "documented_zero_dose"
            ),
        ),
        (
            date(
                2027,
                1,
                1,
            ),
            history(
                "documented_zero_dose"
            ),
        ),
    ],
)
def test_representative_results_are_bilingual(
    assessment,
    history_value,
):
    result = evaluate(
        assessment,
        history_value=history_value,
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
