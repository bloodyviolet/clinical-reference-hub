from datetime import date, timedelta

import pytest

import schemas

from clinical_tools.pni_2026 import (
    evaluate_pni_meningococcal_acwy_child_routine,
)


DOB = date(
    2022,
    1,
    1,
)


def menc_history(
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


def acwy_history(
    state,
    *,
    doses=None,
    reported_prior=0,
):
    return schemas.PniVaccineHistory(
        vaccine_key="meningococcal_acwy",
        history_state=state,
        doses=doses or [],
        reported_prior_doses_without_exact_dates=reported_prior,
    )


def menc_dose(
    administration_date,
):
    return schemas.PniDoseRecord(
        administration_date=administration_date,
        product_key="meningococcal_c",
        documentation_source="official_registry",
    )


def acwy_dose(
    administration_date,
):
    return schemas.PniDoseRecord(
        administration_date=administration_date,
        product_key="meningococcal_acwy",
        documentation_source="official_registry",
    )


def evaluate(
    assessment,
    *,
    menc,
    acwy,
    safety="screened_no_concern",
):
    result = evaluate_pni_meningococcal_acwy_child_routine(
        assessment_date=assessment,
        date_of_birth=DOB,
        menc_history=menc,
        menacwy_history=acwy,
        administration_safety_screen_state=safety,
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
        pni_2026.MENINGOCOCCAL_ACWY_CHILD_RULE_ID
        == "PNI26-MENACWY-CHILD-ROUTINE-001"
    )


def test_before_12_months_not_applicable():
    result = evaluate(
        date(
            2022,
            12,
            31,
        ),
        menc=menc_history(
            "documented_zero_dose"
        ),
        acwy=acwy_history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "not_applicable"


def test_exact_12_months_no_history_recommends_acwy():
    result = evaluate(
        date(
            2023,
            1,
            1,
        ),
        menc=menc_history(
            "documented_zero_dose"
        ),
        acwy=acwy_history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "recommend_now"


def test_exact_child_maximum_recommends():
    result = evaluate(
        date(
            2026,
            12,
            30,
        ),
        menc=menc_history(
            "documented_zero_dose"
        ),
        acwy=acwy_history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "recommend_now"


def test_day_after_child_maximum_closes_layer():
    result = evaluate(
        date(
            2026,
            12,
            31,
        ),
        menc=menc_history(
            "documented_zero_dose"
        ),
        acwy=acwy_history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "not_applicable"

    assert (
        "11"
        in result[
            "interpretation_en"
        ]
    )


def test_valid_child_acwy_suppresses_duplicate():
    result = evaluate(
        date(
            2024,
            1,
            1,
        ),
        menc=menc_history(
            "unknown"
        ),
        acwy=acwy_history(
            "documented_doses",
            doses=[
                acwy_dose(
                    date(
                        2023,
                        1,
                        1,
                    )
                ),
            ],
        ),
    )

    assert result["decision"] == "not_due_now"


def test_acwy_before_12_months_routes_review():
    result = evaluate(
        date(
            2023,
            2,
            1,
        ),
        menc=menc_history(
            "documented_zero_dose"
        ),
        acwy=acwy_history(
            "documented_doses",
            doses=[
                acwy_dose(
                    date(
                        2022,
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


def test_two_child_acwy_doses_route_review():
    result = evaluate(
        date(
            2024,
            1,
            1,
        ),
        menc=menc_history(
            "documented_zero_dose"
        ),
        acwy=acwy_history(
            "documented_doses",
            doses=[
                acwy_dose(
                    date(
                        2023,
                        1,
                        1,
                    )
                ),
                acwy_dose(
                    date(
                        2023,
                        6,
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


def test_unknown_acwy_history_requires_reconciliation():
    result = evaluate(
        date(
            2023,
            2,
            1,
        ),
        menc=menc_history(
            "documented_zero_dose"
        ),
        acwy=acwy_history(
            "unknown"
        ),
    )

    assert result["decision"] == "history_required"


def test_unknown_menc_history_requires_reconciliation_when_acwy_zero():
    result = evaluate(
        date(
            2023,
            2,
            1,
        ),
        menc=menc_history(
            "unknown"
        ),
        acwy=acwy_history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "history_required"


def test_one_old_menc_dose_does_not_block_acwy():
    result = evaluate(
        date(
            2023,
            1,
            1,
        ),
        menc=menc_history(
            "documented_doses",
            doses=[
                menc_dose(
                    date(
                        2022,
                        6,
                        1,
                    )
                ),
            ],
        ),
        acwy=acwy_history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "recommend_now"


def test_recent_menc_day59_waits():
    latest = date(
        2022,
        11,
        15,
    )

    result = evaluate(
        latest
        + timedelta(
            days=59,
        ),
        menc=menc_history(
            "documented_doses",
            doses=[
                menc_dose(
                    latest
                ),
            ],
        ),
        acwy=acwy_history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "not_due_now"

    assert result["minimum_interval_days"] == 60


def test_recent_menc_day60_allows_acwy():
    latest = date(
        2022,
        11,
        15,
    )

    result = evaluate(
        latest
        + timedelta(
            days=60,
        ),
        menc=menc_history(
            "documented_doses",
            doses=[
                menc_dose(
                    latest
                ),
            ],
        ),
        acwy=acwy_history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "recommend_now"


def test_complete_basic_menc_without_booster_recommends_acwy():
    result = evaluate(
        date(
            2023,
            1,
            1,
        ),
        menc=menc_history(
            "documented_doses",
            doses=[
                menc_dose(
                    date(
                        2022,
                        4,
                        1,
                    )
                ),
                menc_dose(
                    date(
                        2022,
                        6,
                        1,
                    )
                ),
            ],
        ),
        acwy=acwy_history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "recommend_now"


def test_legacy_complete_menc_plus_menc_booster_suppresses_acwy():
    result = evaluate(
        date(
            2023,
            6,
            1,
        ),
        menc=menc_history(
            "documented_doses",
            doses=[
                menc_dose(
                    date(
                        2022,
                        4,
                        1,
                    )
                ),
                menc_dose(
                    date(
                        2022,
                        6,
                        1,
                    )
                ),
                menc_dose(
                    date(
                        2023,
                        1,
                        1,
                    )
                ),
            ],
        ),
        acwy=acwy_history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "not_due_now"


def test_ambiguous_legacy_menc_booster_interval_routes_review():
    result = evaluate(
        date(
            2023,
            3,
            1,
        ),
        menc=menc_history(
            "documented_doses",
            doses=[
                menc_dose(
                    date(
                        2022,
                        4,
                        1,
                    )
                ),
                menc_dose(
                    date(
                        2022,
                        5,
                        15,
                    )
                ),
                menc_dose(
                    date(
                        2023,
                        1,
                        1,
                    )
                ),
            ],
        ),
        acwy=acwy_history(
            "documented_zero_dose"
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_post_12m_menc_without_legacy_pattern_routes_review():
    result = evaluate(
        date(
            2023,
            3,
            1,
        ),
        menc=menc_history(
            "documented_doses",
            doses=[
                menc_dose(
                    date(
                        2023,
                        1,
                        15,
                    )
                ),
            ],
        ),
        acwy=acwy_history(
            "documented_zero_dose"
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_partial_menc_history_requires_reconciliation():
    result = evaluate(
        date(
            2023,
            2,
            1,
        ),
        menc=menc_history(
            "partial_record",
            reported_prior=1,
        ),
        acwy=acwy_history(
            "documented_zero_dose"
        ),
    )

    assert result["decision"] == "history_required"


def test_unscreened_due_acwy_requires_context():
    result = evaluate(
        date(
            2023,
            1,
            1,
        ),
        menc=menc_history(
            "documented_zero_dose"
        ),
        acwy=acwy_history(
            "documented_zero_dose"
        ),
        safety="not_screened",
    )

    assert result["decision"] == "context_required"


def test_safety_concern_routes_review():
    result = evaluate(
        date(
            2023,
            1,
            1,
        ),
        menc=menc_history(
            "documented_zero_dose"
        ),
        acwy=acwy_history(
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


def test_swapped_history_keys_rejected():
    with pytest.raises(
        ValueError,
        match="vaccine_key=meningococcal_c",
    ):
        evaluate_pni_meningococcal_acwy_child_routine(
            assessment_date=date(
                2023,
                1,
                1,
            ),
            date_of_birth=DOB,
            menc_history=acwy_history(
                "documented_zero_dose"
            ),
            menacwy_history=acwy_history(
                "documented_zero_dose"
            ),
            administration_safety_screen_state="screened_no_concern",
        )


def test_request_model_preserves_both_history_keys():
    request = schemas.PniAssessmentRequest(
        context=schemas.PniAssessmentContext(
            assessment_date=date(
                2023,
                1,
                1,
            ),
            date_of_birth=DOB,
        ),
        histories=[
            menc_history(
                "documented_zero_dose"
            ),
            acwy_history(
                "documented_zero_dose"
            ),
        ],
    )

    assert {
        value.vaccine_key
        for value
        in request.histories
    } == {
        "meningococcal_c",
        "meningococcal_acwy",
    }


@pytest.mark.parametrize(
    "assessment,menc,acwy",
    [
        (
            date(
                2023,
                1,
                1,
            ),
            menc_history(
                "documented_zero_dose"
            ),
            acwy_history(
                "documented_zero_dose"
            ),
        ),
        (
            date(
                2023,
                2,
                1,
            ),
            menc_history(
                "unknown"
            ),
            acwy_history(
                "documented_zero_dose"
            ),
        ),
        (
            date(
                2024,
                1,
                1,
            ),
            menc_history(
                "unknown"
            ),
            acwy_history(
                "documented_doses",
                doses=[
                    acwy_dose(
                        date(
                            2023,
                            1,
                            1,
                        )
                    ),
                ],
            ),
        ),
    ],
)
def test_representative_results_bilingual(
    assessment,
    menc,
    acwy,
):
    result = evaluate(
        assessment,
        menc=menc,
        acwy=acwy,
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
