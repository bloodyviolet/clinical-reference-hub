from datetime import date, timedelta

import schemas

from clinical_tools.pni_2026 import (
    evaluate_pni_influenza_child_routine,
)

from clinical_tools.pni_history import (
    normalize_influenza_history,
)


def lifetime(
    dates=None,
    *,
    state=None,
    product_key="influenza",
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
        vaccine_key="influenza",
        history_state=state,
        doses=[
            schemas.PniDoseRecord(
                administration_date=value,
                product_key=product_key,
                documentation_source="official_registry",
            )
            for value in dates
        ],
    )


def evaluate(
    *,
    assessment,
    dob,
    current_dates=None,
    prior_dates=None,
    prior_state="documented_none",
    strategy="routine",
    safety="screened_no_concern",
    lifetime_state=None,
    product_key="influenza",
):
    current_dates = list(
        current_dates
        or []
    )

    prior_dates = list(
        prior_dates
        or []
    )

    all_dates = (
        prior_dates
        + current_dates
    )

    history = lifetime(
        all_dates,
        state=lifetime_state,
        product_key=product_key,
    )

    cycle_state = (
        "documented_doses"
        if current_dates
        else "documented_zero_dose"
    )

    normalized = normalize_influenza_history(
        assessment_date=assessment,
        history=history,
        history_scope="complete",
        current_cycle_key="OPAQUE-SOURCE-CYCLE",
        current_cycle_history_state=cycle_state,
        current_cycle_events=[
            {
                "administration_date":
                    value,

                "strategy_layer":
                    strategy,
            }
            for value in current_dates
        ],
        prior_cycle_vaccination_state=prior_state,
    )

    result = evaluate_pni_influenza_child_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        influenza_history=normalized,
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
        pni_2026.INFLUENZA_CHILD_RULE_ID
        == "PNI26-INFLUENZA-CHILD-ROUTINE-001"
    )


def test_before_6_months_not_due():
    result = evaluate(
        assessment=date(
            2026,
            6,
            30,
        ),
        dob=date(
            2026,
            1,
            1,
        ),
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == date(
        2026,
        7,
        1,
    )


def test_exact_6_months_first_ever_recommends_d1():
    result = evaluate(
        assessment=date(
            2026,
            7,
            1,
        ),
        dob=date(
            2026,
            1,
            1,
        ),
    )

    assert result[
        "decision"
    ] == "recommend_now"

    assert result[
        "vaccine_key"
    ] == "influenza"


def test_first_ever_d1_day29_not_due():
    d1 = date(
        2026,
        4,
        1,
    )

    result = evaluate(
        assessment=(
            d1
            + timedelta(
                days=29,
            )
        ),
        dob=date(
            2021,
            1,
            1,
        ),
        current_dates=[
            d1,
        ],
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == (
        d1
        + timedelta(
            days=30,
        )
    )


def test_first_ever_d1_day30_recommends_d2():
    d1 = date(
        2026,
        4,
        1,
    )

    result = evaluate(
        assessment=(
            d1
            + timedelta(
                days=30,
            )
        ),
        dob=date(
            2021,
            1,
            1,
        ),
        current_dates=[
            d1,
        ],
    )

    assert result[
        "decision"
    ] == "recommend_now"

    assert result[
        "recommended_interval_days"
    ] == 30


def test_first_ever_two_valid_doses_complete():
    d1 = date(
        2026,
        4,
        1,
    )

    d2 = (
        d1
        + timedelta(
            days=30,
        )
    )

    result = evaluate(
        assessment=date(
            2026,
            6,
            1,
        ),
        dob=date(
            2021,
            1,
            1,
        ),
        current_dates=[
            d1,
            d2,
        ],
    )

    assert result[
        "decision"
    ] == "not_due_now"


def test_first_ever_historical_interval_under_30_routes_review():
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
        assessment=date(
            2026,
            6,
            1,
        ),
        dob=date(
            2021,
            1,
            1,
        ),
        current_dates=[
            d1,
            d2,
        ],
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_previously_vaccinated_zero_current_recommends_annual_dose():
    result = evaluate(
        assessment=date(
            2026,
            4,
            1,
        ),
        dob=date(
            2021,
            1,
            1,
        ),
        prior_dates=[
            date(
                2025,
                4,
                1,
            ),
        ],
        prior_state="documented_prior",
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_previously_vaccinated_one_current_dose_complete():
    result = evaluate(
        assessment=date(
            2026,
            5,
            1,
        ),
        dob=date(
            2021,
            1,
            1,
        ),
        prior_dates=[
            date(
                2025,
                4,
                1,
            ),
        ],
        current_dates=[
            date(
                2026,
                4,
                1,
            ),
        ],
        prior_state="documented_prior",
    )

    assert result[
        "decision"
    ] == "not_due_now"


def test_previously_vaccinated_two_current_doses_routes_review():
    result = evaluate(
        assessment=date(
            2026,
            6,
            1,
        ),
        dob=date(
            2021,
            1,
            1,
        ),
        prior_dates=[
            date(
                2025,
                4,
                1,
            ),
        ],
        current_dates=[
            date(
                2026,
                4,
                1,
            ),
            date(
                2026,
                5,
                1,
            ),
        ],
        prior_state="documented_prior",
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_unknown_priming_fails_closed():
    normalized = normalize_influenza_history(
        assessment_date=date(
            2026,
            4,
            1,
        ),
        history=lifetime(),
        history_scope="complete",
        current_cycle_key="OPAQUE-SOURCE-CYCLE",
        current_cycle_history_state="documented_zero_dose",
        current_cycle_events=[],
        prior_cycle_vaccination_state="unknown",
    )

    result = evaluate_pni_influenza_child_routine(
        assessment_date=date(
            2026,
            4,
            1,
        ),
        date_of_birth=date(
            2021,
            1,
            1,
        ),
        influenza_history=normalized,
        administration_safety_screen_state="screened_no_concern",
    )

    assert result[
        "decision"
    ] == "history_required"


def test_special_strategy_routes_review():
    result = evaluate(
        assessment=date(
            2026,
            5,
            1,
        ),
        dob=date(
            2021,
            1,
            1,
        ),
        current_dates=[
            date(
                2026,
                4,
                1,
            ),
        ],
        prior_dates=[
            date(
                2025,
                4,
                1,
            ),
        ],
        prior_state="documented_prior",
        strategy="special",
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_unsupported_private_product_routes_review():
    result = evaluate(
        assessment=date(
            2026,
            5,
            1,
        ),
        dob=date(
            2021,
            1,
            1,
        ),
        current_dates=[
            date(
                2026,
                4,
                1,
            ),
        ],
        prior_state="documented_prior",
        product_key="influenza_quadrivalent_private",
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_routine_event_before_6_months_routes_review():
    result = evaluate(
        assessment=date(
            2026,
            7,
            1,
        ),
        dob=date(
            2026,
            1,
            1,
        ),
        current_dates=[
            date(
                2026,
                6,
                30,
            ),
        ],
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_exact_6_year_birthday_without_pending_priming_not_applicable():
    result = evaluate(
        assessment=date(
            2026,
            10,
            1,
        ),
        dob=date(
            2020,
            10,
            1,
        ),
        prior_state="documented_prior",
    )

    assert result[
        "decision"
    ] == "not_applicable"


def test_d1_with_day30_exactly_on_sixth_birthday_is_source_hold():
    dob = date(
        2020,
        10,
        1,
    )

    d1 = date(
        2026,
        9,
        1,
    )

    result = evaluate(
        assessment=date(
            2026,
            9,
            30,
        ),
        dob=dob,
        current_dates=[
            d1,
        ],
        prior_state="documented_none",
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )

    assert result[
        "recommended_date"
    ] == date(
        2026,
        10,
        1,
    )

    assert (
        "authoritative_age_out_completion_rule"
        in result[
            "missing_context"
        ]
    )


def test_d1_with_day30_after_sixth_birthday_is_source_hold():
    dob = date(
        2020,
        10,
        1,
    )

    d1 = date(
        2026,
        9,
        15,
    )

    result = evaluate(
        assessment=date(
            2026,
            9,
            30,
        ),
        dob=dob,
        current_dates=[
            d1,
        ],
        prior_state="documented_none",
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )

    assert result[
        "recommended_date"
    ] == date(
        2026,
        10,
        15,
    )


def test_d1_with_day30_still_before_sixth_birthday_uses_normal_logic():
    dob = date(
        2020,
        10,
        1,
    )

    d1 = date(
        2026,
        8,
        31,
    )

    day30 = (
        d1
        + timedelta(
            days=30,
        )
    )

    result = evaluate(
        assessment=day30,
        dob=dob,
        current_dates=[
            d1,
        ],
        prior_state="documented_none",
    )

    assert day30 < date(
        2026,
        10,
        1,
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_unscreened_due_dose_requires_context():
    result = evaluate(
        assessment=date(
            2026,
            7,
            1,
        ),
        dob=date(
            2026,
            1,
            1,
        ),
        safety="not_screened",
    )

    assert result[
        "decision"
    ] == "context_required"


def test_safety_concern_routes_review():
    result = evaluate(
        assessment=date(
            2026,
            7,
            1,
        ),
        dob=date(
            2026,
            1,
            1,
        ),
        safety="screened_concern",
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_cycle_identity_flags_are_enforced():
    normalized = normalize_influenza_history(
        assessment_date=date(
            2026,
            7,
            1,
        ),
        history=lifetime(),
        history_scope="complete",
        current_cycle_key="OPAQUE-SOURCE-CYCLE",
        current_cycle_history_state="documented_zero_dose",
        current_cycle_events=[],
        prior_cycle_vaccination_state="documented_none",
    )

    normalized[
        "cycle_key_parsed"
    ] = True

    try:
        evaluate_pni_influenza_child_routine(
            assessment_date=date(
                2026,
                7,
                1,
            ),
            date_of_birth=date(
                2026,
                1,
                1,
            ),
            influenza_history=normalized,
            administration_safety_screen_state="screened_no_concern",
        )

    except ValueError as exc:
        assert "cycle key parsing" in str(
            exc
        )

    else:
        raise AssertionError(
            "Parsed influenza cycle key unexpectedly accepted"
        )


def test_result_remains_bilingual_and_language_neutral():
    result = evaluate(
        assessment=date(
            2026,
            7,
            1,
        ),
        dob=date(
            2026,
            1,
            1,
        ),
    )

    assert result[
        "decision"
    ] == "recommend_now"

    assert result[
        "interpretation_pt"
    ].strip()

    assert result[
        "interpretation_en"
    ].strip()

    assert (
        result[
            "interpretation_pt"
        ]
        != result[
            "interpretation_en"
        ]
    )

    assert result[
        "special_condition_inferred"
    ] is False

    assert result[
        "synthetic_score_applied"
    ] is False
