from datetime import date, timedelta

import pytest

import schemas

from clinical_tools.pni_2026 import (
    evaluate_pni_pneumococcal_child_routine,
)

from clinical_tools.pni_history import (
    normalize_pneumococcal_history,
)


def vh(
    key,
    dates=None,
    *,
    state=None,
):
    dates = list(
        dates
        or []
    )

    if state is None:
        state = (
            "documented_doses"
            if dates
            else "documented_zero_dose"
        )

    return schemas.PniVaccineHistory(
        vaccine_key=key,
        history_state=state,
        doses=[
            schemas.PniDoseRecord(
                administration_date=value,
                product_key=key,
                documentation_source="official_registry",
            )
            for value in dates
        ],
    )


def evaluate(
    *,
    assessment,
    dob,
    vpc10=None,
    vpc20=None,
    safety="screened_no_concern",
    exception=False,
):
    histories = []

    if vpc10 is not None:
        histories.append(
            vpc10
        )

    if vpc20 is not None:
        histories.append(
            vpc20
        )

    normalized = normalize_pneumococcal_history(
        assessment_date=assessment,
        histories=histories,
        history_scope="complete",
    )

    result = evaluate_pni_pneumococcal_child_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        pneumococcal_history=normalized,
        administration_safety_screen_state=safety,
        exceptional_minimum_interval_authorized=exception,
    )

    validated = schemas.PniRuleResult.model_validate(
        result
    )

    assert validated.interpretation_pt.strip()
    assert validated.interpretation_en.strip()
    assert validated.interpretation_pt != validated.interpretation_en
    assert validated.special_condition_inferred is False
    assert validated.synthetic_score_applied is False

    return result


def zero10():
    return vh(
        "pneumococcal_10"
    )


def zero20():
    return vh(
        "pneumococcal_20"
    )


def test_rule_id():
    from clinical_tools import pni_2026

    assert (
        pni_2026.PNEUMOCOCCAL_CHILD_RULE_ID
        == "PNI26-PNEUMO-CHILD-ROUTINE-001"
    )


def test_missing_product_history_requires_reconciliation():
    result = evaluate(
        assessment=date(2026, 3, 1),
        dob=date(2026, 1, 1),
        vpc20=zero20(),
    )

    assert result["decision"] == "history_required"


def test_before_two_months_not_due():
    result = evaluate(
        assessment=date(2026, 2, 28),
        dob=date(2026, 1, 1),
        vpc10=zero10(),
        vpc20=zero20(),
    )

    assert result["decision"] == "not_due_now"


def test_exact_two_months_zero_history_recommends_vpc20_d1():
    result = evaluate(
        assessment=date(2026, 3, 1),
        dob=date(2026, 1, 1),
        vpc10=zero10(),
        vpc20=zero20(),
    )

    assert result["decision"] == "recommend_now"
    assert result["vaccine_key"] == "pneumococcal_20"


def test_timely_d2_after_vpc20_is_vpc10():
    d1 = date(2026, 3, 1)

    result = evaluate(
        assessment=d1 + timedelta(days=60),
        dob=date(2026, 1, 1),
        vpc10=zero10(),
        vpc20=vh(
            "pneumococcal_20",
            [
                d1,
            ],
        ),
    )

    assert result["decision"] == "recommend_now"
    assert result["vaccine_key"] == "pneumococcal_10"


def test_before_5m_d2_does_not_use_30_day_exception():
    d1 = date(2026, 3, 1)

    result = evaluate(
        assessment=d1 + timedelta(days=30),
        dob=date(2026, 1, 1),
        vpc10=zero10(),
        vpc20=vh(
            "pneumococcal_20",
            [
                d1,
            ],
        ),
        exception=True,
    )

    assert result["decision"] == "not_due_now"


def test_5_to_10m_vpc20_d1_recommends_vpc10_d2():
    d1 = date(2026, 6, 1)

    result = evaluate(
        assessment=d1 + timedelta(days=60),
        dob=date(2026, 1, 1),
        vpc10=zero10(),
        vpc20=vh(
            "pneumococcal_20",
            [
                d1,
            ],
        ),
    )

    assert result["decision"] == "recommend_now"
    assert result["vaccine_key"] == "pneumococcal_10"


def test_5_to_10m_vpc10_d1_recommends_vpc20_d2():
    d1 = date(2026, 6, 1)

    result = evaluate(
        assessment=d1 + timedelta(days=60),
        dob=date(2026, 1, 1),
        vpc10=vh(
            "pneumococcal_10",
            [
                d1,
            ],
        ),
        vpc20=zero20(),
    )

    assert result["decision"] == "recommend_now"
    assert result["vaccine_key"] == "pneumococcal_20"


def test_5_to_10m_day30_requires_explicit_exception():
    d1 = date(2026, 7, 1)

    standard = evaluate(
        assessment=d1 + timedelta(days=30),
        dob=date(2026, 1, 1),
        vpc10=zero10(),
        vpc20=vh(
            "pneumococcal_20",
            [
                d1,
            ],
        ),
    )

    exceptional = evaluate(
        assessment=d1 + timedelta(days=30),
        dob=date(2026, 1, 1),
        vpc10=zero10(),
        vpc20=vh(
            "pneumococcal_20",
            [
                d1,
            ],
        ),
        exception=True,
    )

    assert standard["decision"] == "not_due_now"
    assert exceptional["decision"] == "recommend_now"
    assert exceptional["vaccine_key"] == "pneumococcal_10"
    assert exceptional["minimum_interval_applied"] is True


def test_historical_30_to_59_primary_interval_routes_review():
    result = evaluate(
        assessment=date(2026, 11, 1),
        dob=date(2026, 1, 1),
        vpc20=vh(
            "pneumococcal_20",
            [
                date(2026, 6, 1),
            ],
        ),
        vpc10=vh(
            "pneumococcal_10",
            [
                date(2026, 7, 15),
            ],
        ),
    )

    assert result["decision"] == "special_pathway_review"


def test_11m_zero_history_recommends_d1_vpc20():
    result = evaluate(
        assessment=date(2026, 12, 1),
        dob=date(2026, 1, 1),
        vpc10=zero10(),
        vpc20=zero20(),
    )

    assert result["decision"] == "recommend_now"
    assert result["vaccine_key"] == "pneumococcal_20"


def test_11m_prior_vpc10_d1_recommends_vpc20_d2():
    result = evaluate(
        assessment=date(2026, 12, 1),
        dob=date(2026, 1, 1),
        vpc10=vh(
            "pneumococcal_10",
            [
                date(2026, 10, 1),
            ],
        ),
        vpc20=zero20(),
    )

    assert result["decision"] == "recommend_now"
    assert result["vaccine_key"] == "pneumococcal_20"


def test_11m_only_prior_vpc20_is_remaining_source_hold():
    result = evaluate(
        assessment=date(2026, 12, 1),
        dob=date(2026, 1, 1),
        vpc10=zero10(),
        vpc20=vh(
            "pneumococcal_20",
            [
                date(2026, 10, 1),
            ],
        ),
    )

    assert result["decision"] == "special_pathway_review"


def test_two_valid_primary_doses_at_11m_wait_for_booster():
    result = evaluate(
        assessment=date(2026, 12, 1),
        dob=date(2026, 1, 1),
        vpc20=vh(
            "pneumococcal_20",
            [
                date(2026, 6, 1),
            ],
        ),
        vpc10=vh(
            "pneumococcal_10",
            [
                date(2026, 8, 1),
            ],
        ),
    )

    assert result["decision"] == "not_due_now"


def test_12m_zero_history_recommends_single_vpc20():
    result = evaluate(
        assessment=date(2027, 1, 1),
        dob=date(2026, 1, 1),
        vpc10=zero10(),
        vpc20=zero20(),
    )

    assert result["decision"] == "recommend_now"
    assert result["vaccine_key"] == "pneumococcal_20"


def test_single_vpc20_first_given_after_12m_is_complete():
    result = evaluate(
        assessment=date(2027, 4, 1),
        dob=date(2026, 1, 1),
        vpc10=zero10(),
        vpc20=vh(
            "pneumococcal_20",
            [
                date(2027, 2, 1),
            ],
        ),
    )

    assert result["decision"] == "not_due_now"


def test_single_vpc10_first_given_after_12m_routes_review():
    result = evaluate(
        assessment=date(2027, 4, 1),
        dob=date(2026, 1, 1),
        vpc10=vh(
            "pneumococcal_10",
            [
                date(2027, 2, 1),
            ],
        ),
        vpc20=zero20(),
    )

    assert result["decision"] == "special_pathway_review"


def test_12m_plus_one_pre12_d1_waits_until_day60():
    d1 = date(2026, 11, 30)

    result = evaluate(
        assessment=d1 + timedelta(days=59),
        dob=date(2025, 12, 1),
        vpc10=zero10(),
        vpc20=vh(
            "pneumococcal_20",
            [
                d1,
            ],
        ),
    )

    assert result["decision"] == "not_due_now"


def test_12m_plus_one_pre12_d1_day60_recommends_vpc20_booster():
    d1 = date(2026, 11, 30)

    result = evaluate(
        assessment=d1 + timedelta(days=60),
        dob=date(2025, 12, 1),
        vpc10=zero10(),
        vpc20=vh(
            "pneumococcal_20",
            [
                d1,
            ],
        ),
    )

    assert result["decision"] == "recommend_now"
    assert result["vaccine_key"] == "pneumococcal_20"


def test_two_pre12_primary_doses_then_booster_due_after_60_days():
    result = evaluate(
        assessment=date(2027, 2, 1),
        dob=date(2026, 1, 1),
        vpc20=vh(
            "pneumococcal_20",
            [
                date(2026, 6, 1),
            ],
        ),
        vpc10=vh(
            "pneumococcal_10",
            [
                date(2026, 8, 1),
            ],
        ),
    )

    assert result["decision"] == "recommend_now"
    assert result["vaccine_key"] == "pneumococcal_20"


def test_one_pre12_d1_plus_valid_post12_vpc20_is_complete():
    result = evaluate(
        assessment=date(2027, 3, 1),
        dob=date(2026, 1, 1),
        vpc10=zero10(),
        vpc20=vh(
            "pneumococcal_20",
            [
                date(2026, 10, 1),
                date(2027, 1, 1),
            ],
        ),
    )

    assert result["decision"] == "not_due_now"


def test_two_pre12_primary_plus_post12_vpc20_booster_complete():
    result = evaluate(
        assessment=date(2027, 3, 1),
        dob=date(2026, 1, 1),
        vpc20=vh(
            "pneumococcal_20",
            [
                date(2026, 6, 1),
                date(2027, 1, 1),
            ],
        ),
        vpc10=vh(
            "pneumococcal_10",
            [
                date(2026, 8, 1),
            ],
        ),
    )

    assert result["decision"] == "not_due_now"


def test_vpc20_vpc20_pair_pre12_routes_review():
    result = evaluate(
        assessment=date(2027, 1, 1),
        dob=date(2026, 1, 1),
        vpc10=zero10(),
        vpc20=vh(
            "pneumococcal_20",
            [
                date(2026, 6, 1),
                date(2026, 8, 1),
            ],
        ),
    )

    assert result["decision"] == "special_pathway_review"


def test_unknown_history_requires_history():
    result = evaluate(
        assessment=date(2026, 6, 1),
        dob=date(2026, 1, 1),
        vpc10=zero10(),
        vpc20=vh(
            "pneumococcal_20",
            state="unknown",
        ),
    )

    assert result["decision"] == "history_required"


def test_unscreened_due_dose_requires_context():
    result = evaluate(
        assessment=date(2026, 3, 1),
        dob=date(2026, 1, 1),
        vpc10=zero10(),
        vpc20=zero20(),
        safety="not_screened",
    )

    assert result["decision"] == "context_required"


def test_safety_concern_routes_review():
    result = evaluate(
        assessment=date(2026, 3, 1),
        dob=date(2026, 1, 1),
        vpc10=zero10(),
        vpc20=zero20(),
        safety="screened_concern",
    )

    assert result["decision"] == "special_pathway_review"


def test_after_60_month_birthday_not_applicable():
    result = evaluate(
        assessment=date(2031, 1, 1),
        dob=date(2026, 1, 1),
        vpc10=zero10(),
        vpc20=zero20(),
    )

    assert result["decision"] == "not_applicable"


def test_exception_flag_requires_boolean():
    normalized = normalize_pneumococcal_history(
        assessment_date=date(2026, 7, 1),
        histories=[
            zero10(),
            zero20(),
        ],
        history_scope="complete",
    )

    with pytest.raises(
        ValueError,
        match="exceptional_minimum_interval_authorized",
    ):
        evaluate_pni_pneumococcal_child_routine(
            assessment_date=date(2026, 7, 1),
            date_of_birth=date(2026, 1, 1),
            pneumococcal_history=normalized,
            administration_safety_screen_state="screened_no_concern",
            exceptional_minimum_interval_authorized=1,
        )
