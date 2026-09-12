from datetime import date, timedelta

import pytest

import schemas

from clinical_tools.pni_2026 import (
    evaluate_pni_ipv_child_routine,
)

from clinical_tools.pni_history import (
    normalize_polio_history,
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


def normal(
    assessment,
    histories,
):
    return normalize_polio_history(
        assessment_date=assessment,
        histories=histories,
        history_scope="complete",
    )


def evaluate(
    *,
    assessment,
    dob,
    histories,
    safety="screened_no_concern",
    exception=False,
):
    result = evaluate_pni_ipv_child_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        polio_history=normal(
            assessment,
            histories,
        ),
        administration_safety_screen_state=safety,
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
        pni_2026.IPV_CHILD_RULE_ID
        == "PNI26-IPV-CHILD-ROUTINE-001"
    )


def test_before_two_months_not_due():
    result = evaluate(
        assessment=date(2026, 2, 28),
        dob=date(2026, 1, 1),
        histories=[
            vh("ipv"),
        ],
    )

    assert result["decision"] == "not_due_now"


def test_exact_two_months_zero_history_recommends_d1():
    result = evaluate(
        assessment=date(2026, 3, 1),
        dob=date(2026, 1, 1),
        histories=[
            vh("ipv"),
        ],
    )

    assert result["decision"] == "recommend_now"


def test_primary_d1_before_two_months_routes_review():
    result = evaluate(
        assessment=date(2026, 4, 20),
        dob=date(2026, 1, 1),
        histories=[
            vh(
                "ipv",
                [
                    date(2026, 2, 20),
                ],
            ),
        ],
    )

    assert (
        result["decision"]
        == "special_pathway_review"
    )


def test_d2_day29_not_due_even_with_exception():
    d1 = date(2026, 3, 1)

    result = evaluate(
        assessment=d1 + timedelta(days=29),
        dob=date(2026, 1, 1),
        histories=[
            vh("ipv", [d1]),
        ],
        exception=True,
    )

    assert result["decision"] == "not_due_now"


def test_d2_day30_requires_explicit_exception():
    d1 = date(2026, 3, 1)

    standard = evaluate(
        assessment=d1 + timedelta(days=30),
        dob=date(2026, 1, 1),
        histories=[
            vh("ipv", [d1]),
        ],
    )

    exceptional = evaluate(
        assessment=d1 + timedelta(days=30),
        dob=date(2026, 1, 1),
        histories=[
            vh("ipv", [d1]),
        ],
        exception=True,
    )

    assert standard["decision"] == "not_due_now"
    assert exceptional["decision"] == "recommend_now"
    assert exceptional["minimum_interval_applied"] is True


def test_d2_day60_recommends():
    d1 = date(2026, 3, 1)

    result = evaluate(
        assessment=d1 + timedelta(days=60),
        dob=date(2026, 1, 1),
        histories=[
            vh("ipv", [d1]),
        ],
    )

    assert result["decision"] == "recommend_now"


def test_historical_primary_30_to_59_interval_routes_review():
    result = evaluate(
        assessment=date(2026, 5, 1),
        dob=date(2026, 1, 1),
        histories=[
            vh(
                "ipv",
                [
                    date(2026, 3, 1),
                    date(2026, 4, 15),
                ],
            ),
        ],
    )

    assert (
        result["decision"]
        == "special_pathway_review"
    )


def test_mixed_supported_products_complete_primary_series():
    assessment = date(2027, 1, 1)

    result = evaluate(
        assessment=assessment,
        dob=date(2026, 1, 1),
        histories=[
            vh(
                "ipv",
                [
                    date(2026, 3, 1),
                ],
            ),
            vh(
                "penta_acellular_ipv",
                [
                    date(2026, 5, 1),
                ],
            ),
            vh(
                "tetra_acellular_ipv",
                [
                    date(2026, 7, 1),
                ],
            ),
            vh(
                "opv_bivalent_legacy",
            ),
        ],
    )

    assert result["decision"] == "not_due_now"


def test_three_primary_before_15_months_booster_not_due():
    result = evaluate(
        assessment=date(2027, 3, 31),
        dob=date(2026, 1, 1),
        histories=[
            vh(
                "ipv",
                [
                    date(2026, 3, 1),
                    date(2026, 5, 1),
                    date(2026, 7, 1),
                ],
            ),
            vh("opv_bivalent_legacy"),
        ],
    )

    assert result["decision"] == "not_due_now"


def test_booster_exact_15_months_and_nine_months_from_d3_recommends():
    result = evaluate(
        assessment=date(2027, 4, 1),
        dob=date(2026, 1, 1),
        histories=[
            vh(
                "ipv",
                [
                    date(2026, 3, 1),
                    date(2026, 5, 1),
                    date(2026, 7, 1),
                ],
            ),
            vh("opv_bivalent_legacy"),
        ],
    )

    assert result["decision"] == "recommend_now"


def test_delayed_d3_booster_minimum_six_months_can_recommend_before_nine():
    result = evaluate(
        assessment=date(2027, 7, 1),
        dob=date(2026, 1, 1),
        histories=[
            vh(
                "ipv",
                [
                    date(2026, 3, 1),
                    date(2026, 6, 1),
                    date(2027, 1, 1),
                ],
            ),
            vh("opv_bivalent_legacy"),
        ],
    )

    assert result["decision"] == "recommend_now"


def test_booster_before_six_calendar_months_not_due():
    result = evaluate(
        assessment=date(2027, 6, 30),
        dob=date(2026, 1, 1),
        histories=[
            vh(
                "ipv",
                [
                    date(2026, 3, 1),
                    date(2026, 6, 1),
                    date(2027, 1, 1),
                ],
            ),
            vh("opv_bivalent_legacy"),
        ],
    )

    assert result["decision"] == "not_due_now"


def test_valid_fourth_ipv_event_completes_current_schedule():
    result = evaluate(
        assessment=date(2027, 4, 1),
        dob=date(2026, 1, 1),
        histories=[
            vh(
                "ipv",
                [
                    date(2026, 3, 1),
                    date(2026, 5, 1),
                    date(2026, 7, 1),
                    date(2027, 4, 1),
                ],
            ),
            vh("opv_bivalent_legacy"),
        ],
    )

    assert result["decision"] == "not_due_now"

    assert (
        "segundo"
        in result["interpretation_pt"].lower()
    )


def test_fourth_ipv_before_15_months_routes_review():
    result = evaluate(
        assessment=date(2027, 1, 1),
        dob=date(2026, 1, 1),
        histories=[
            vh(
                "ipv",
                [
                    date(2026, 3, 1),
                    date(2026, 5, 1),
                    date(2026, 7, 1),
                    date(2027, 1, 1),
                ],
            ),
            vh("opv_bivalent_legacy"),
        ],
    )

    assert (
        result["decision"]
        == "special_pathway_review"
    )


def test_legacy_history_absent_requires_reconciliation_for_old_child():
    result = evaluate(
        assessment=date(2026, 9, 11),
        dob=date(2023, 1, 1),
        histories=[
            vh(
                "ipv",
                [
                    date(2023, 3, 1),
                    date(2023, 5, 1),
                    date(2023, 7, 1),
                ],
            ),
        ],
    )

    assert result["decision"] == "history_required"


def test_documented_zero_legacy_history_allows_current_booster_decision():
    result = evaluate(
        assessment=date(2026, 9, 11),
        dob=date(2023, 1, 1),
        histories=[
            vh(
                "ipv",
                [
                    date(2023, 3, 1),
                    date(2023, 5, 1),
                    date(2023, 7, 1),
                ],
            ),
            vh("opv_bivalent_legacy"),
        ],
    )

    assert result["decision"] == "recommend_now"


def test_one_historical_vop_requires_transition_vip():
    result = evaluate(
        assessment=date(2026, 9, 11),
        dob=date(2023, 1, 1),
        histories=[
            vh(
                "ipv",
                [
                    date(2023, 3, 1),
                    date(2023, 5, 1),
                    date(2023, 7, 1),
                ],
            ),
            vh(
                "opv_bivalent_legacy",
                [
                    date(2024, 8, 1),
                ],
            ),
        ],
    )

    assert result["decision"] == "recommend_now"
    assert result["minimum_interval_days"] == 30


def test_transition_vip_waits_until_day30_after_vop():
    assessment = date(2024, 8, 30)

    result = evaluate(
        assessment=assessment,
        dob=date(2023, 1, 1),
        histories=[
            vh(
                "ipv",
                [
                    date(2023, 3, 1),
                    date(2023, 5, 1),
                    date(2023, 7, 1),
                ],
            ),
            vh(
                "opv_bivalent_legacy",
                [
                    date(2024, 8, 1),
                ],
            ),
        ],
    )

    assert result["decision"] == "not_due_now"


def test_transition_vip_exact_day30_after_vop_recommends():
    result = evaluate(
        assessment=date(2024, 8, 31),
        dob=date(2023, 1, 1),
        histories=[
            vh(
                "ipv",
                [
                    date(2023, 3, 1),
                    date(2023, 5, 1),
                    date(2023, 7, 1),
                ],
            ),
            vh(
                "opv_bivalent_legacy",
                [
                    date(2024, 8, 1),
                ],
            ),
        ],
    )

    assert result["decision"] == "recommend_now"


def test_two_historical_vop_boosters_complete_transition():
    result = evaluate(
        assessment=date(2026, 9, 11),
        dob=date(2022, 1, 1),
        histories=[
            vh(
                "ipv",
                [
                    date(2022, 3, 1),
                    date(2022, 5, 1),
                    date(2022, 7, 1),
                ],
            ),
            vh(
                "opv_bivalent_legacy",
                [
                    date(2023, 4, 1),
                    date(2024, 8, 1),
                ],
            ),
        ],
    )

    assert result["decision"] == "not_due_now"


def test_vop_before_complete_primary_routes_review():
    result = evaluate(
        assessment=date(2026, 9, 11),
        dob=date(2023, 1, 1),
        histories=[
            vh(
                "ipv",
                [
                    date(2023, 3, 1),
                    date(2023, 5, 1),
                ],
            ),
            vh(
                "opv_bivalent_legacy",
                [
                    date(2023, 6, 1),
                ],
            ),
        ],
    )

    assert (
        result["decision"]
        == "special_pathway_review"
    )


def test_rie_exposure_routes_review():
    result = evaluate(
        assessment=date(2026, 9, 11),
        dob=date(2026, 1, 1),
        histories=[
            vh(
                "hexa_acellular_rie",
                [
                    date(2026, 3, 1),
                ],
            ),
        ],
    )

    assert (
        result["decision"]
        == "special_pathway_review"
    )


def test_unknown_relevant_history_requires_history():
    result = evaluate(
        assessment=date(2026, 9, 11),
        dob=date(2026, 1, 1),
        histories=[
            vh(
                "ipv",
                state="unknown",
            ),
        ],
    )

    assert result["decision"] == "history_required"


def test_unscreened_due_dose_requires_context():
    result = evaluate(
        assessment=date(2026, 3, 1),
        dob=date(2026, 1, 1),
        histories=[
            vh("ipv"),
        ],
        safety="not_screened",
    )

    assert result["decision"] == "context_required"


def test_safety_concern_routes_review():
    result = evaluate(
        assessment=date(2026, 3, 1),
        dob=date(2026, 1, 1),
        histories=[
            vh("ipv"),
        ],
        safety="screened_concern",
    )

    assert (
        result["decision"]
        == "special_pathway_review"
    )


def test_after_child_age_scope_not_applicable():
    result = evaluate(
        assessment=date(2031, 1, 1),
        dob=date(2026, 1, 1),
        histories=[
            vh("ipv"),
        ],
    )

    assert result["decision"] == "not_applicable"


def test_primary_exception_flag_requires_boolean():
    normalized = normal(
        date(2026, 5, 1),
        [
            vh(
                "ipv",
                [
                    date(2026, 3, 1),
                ],
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match="exceptional_minimum_interval_authorized",
    ):
        evaluate_pni_ipv_child_routine(
            assessment_date=date(2026, 5, 1),
            date_of_birth=date(2026, 1, 1),
            polio_history=normalized,
            administration_safety_screen_state="screened_no_concern",
            exceptional_minimum_interval_authorized=1,
        )
