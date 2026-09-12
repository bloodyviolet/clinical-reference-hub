from datetime import date, timedelta

import pytest

import schemas

from clinical_tools.pni_2026 import (
    YELLOW_FEVER_RULE_ID,
    evaluate_pni_yellow_fever_routine,
)

from clinical_tools.pni_history import (
    YELLOW_FEVER_PRODUCT_FRACTIONAL_2018,
    YELLOW_FEVER_PRODUCT_STANDARD,
    normalize_yellow_fever_history,
)


S = YELLOW_FEVER_PRODUCT_STANDARD
F = YELLOW_FEVER_PRODUCT_FRACTIONAL_2018


def normalized(
    *,
    assessment,
    dob,
    events=None,
    state=None,
    scope="complete",
):
    events = list(
        events
        or []
    )

    if state is None:
        state = (
            "documented_doses"
            if events
            else "documented_zero_dose"
        )

    return normalize_yellow_fever_history(
        assessment_date=assessment,
        date_of_birth=dob,
        history=schemas.PniVaccineHistory(
            vaccine_key="yellow_fever",
            history_state=state,
            doses=[
                schemas.PniDoseRecord(
                    administration_date=d,
                    product_key=p,
                    documentation_source="official_registry",
                )
                for d, p
                in events
            ],
        ),
        history_scope=scope,
    )


def clear_interaction():
    return schemas.PniYellowFeverInteractionContext(
        history_screen_state=(
            "screened_no_relevant_recent_live_vaccine"
        ),
    )


def evaluate(
    history,
    *,
    assessment,
    dob,
    routine_context=(
        "screened_routine_no_special_condition"
    ),
    interaction=None,
    safety="screened_no_concern",
):
    return evaluate_pni_yellow_fever_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        yellow_fever_history=history,
        routine_context_state=routine_context,
        interaction_context=interaction,
        administration_safety_screen_state=safety,
    )


def test_rule_id():
    assert (
        YELLOW_FEVER_RULE_ID
        == "PNI26-YELLOW-FEVER-ROUTINE-001"
    )


def test_interaction_model_is_dedicated_not_generic_history_field():
    assert hasattr(
        schemas,
        "PniYellowFeverInteractionContext",
    )

    assert not any(
        "yellow_fever"
        in field.lower()
        for field
        in schemas.PniVaccineHistory.model_fields
    )


def test_before_9m_routine_not_due():
    dob = date(
        2026,
        1,
        1,
    )

    assessment = date(
        2026,
        9,
        30,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
        interaction=None,
        safety="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == date(
        2026,
        10,
        1,
    )


def test_d0_can_delay_nominal_9m_first_standard():
    dob = date(
        2026,
        1,
        1,
    )

    d0 = date(
        2026,
        9,
        20,
    )

    assessment = date(
        2026,
        10,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
            events=[
                (
                    d0,
                    S,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == date(
        2026,
        10,
        20,
    )


def test_exact_9m_zero_history_due_with_clear_context():
    dob = date(
        2026,
        1,
        1,
    )

    assessment = date(
        2026,
        10,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
        interaction=clear_interaction(),
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_due_requires_routine_special_condition_screen():
    dob = date(
        2026,
        1,
        1,
    )

    assessment = date(
        2026,
        10,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
        routine_context="not_screened",
        interaction=clear_interaction(),
    )

    assert result[
        "decision"
    ] == "context_required"


def test_special_condition_routes_out():
    dob = date(
        2026,
        1,
        1,
    )

    assessment = date(
        2026,
        10,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
        routine_context="screened_special_condition_present",
        interaction=clear_interaction(),
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_due_requires_live_vaccine_context():
    dob = date(
        2026,
        1,
        1,
    )

    assessment = date(
        2026,
        10,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
        interaction=None,
    )

    assert result[
        "decision"
    ] == "context_required"


def test_due_requires_administration_safety():
    dob = date(
        2026,
        1,
        1,
    )

    assessment = date(
        2026,
        10,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
        interaction=clear_interaction(),
        safety="not_screened",
    )

    assert result[
        "decision"
    ] == "context_required"


def test_safety_concern_routes_out():
    dob = date(
        2026,
        1,
        1,
    )

    assessment = date(
        2026,
        10,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
        interaction=clear_interaction(),
        safety="screened_concern",
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_timely_first_standard_booster_nominally_at_4y():
    dob = date(
        2022,
        1,
        1,
    )

    first = date(
        2022,
        10,
        1,
    )

    assessment = date(
        2025,
        12,
        31,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
            events=[
                (
                    first,
                    S,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == date(
        2026,
        1,
        1,
    )


def test_booster_due_at_exact_4y():
    dob = date(
        2022,
        1,
        1,
    )

    first = date(
        2022,
        10,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
            events=[
                (
                    first,
                    S,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
        interaction=clear_interaction(),
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_late_first_standard_after_4y_waits_30_days():
    dob = date(
        2022,
        1,
        1,
    )

    first = date(
        2026,
        6,
        1,
    )

    assessment = date(
        2026,
        6,
        15,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
            events=[
                (
                    first,
                    S,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
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


def test_two_pre5_standard_doses_complete():
    dob = date(
        2022,
        1,
        1,
    )

    assessment = date(
        2026,
        12,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
            events=[
                (
                    date(
                        2022,
                        10,
                        1,
                    ),
                    S,
                ),
                (
                    date(
                        2026,
                        1,
                        1,
                    ),
                    S,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] is None


def test_age5_zero_history_needs_one_standard_dose():
    dob = date(
        2021,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
        interaction=clear_interaction(),
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_one_pre5_standard_booster_obligation_survives_age5():
    dob = date(
        2021,
        1,
        1,
    )

    prior = date(
        2025,
        12,
        20,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
            events=[
                (
                    prior,
                    S,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == date(
        2026,
        1,
        19,
    )


def test_one_pre5_standard_due_after_30_days_even_after_age5():
    dob = date(
        2021,
        1,
        1,
    )

    prior = date(
        2025,
        12,
        20,
    )

    assessment = date(
        2026,
        1,
        19,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
            events=[
                (
                    prior,
                    S,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
        interaction=clear_interaction(),
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_one_age5plus_standard_is_complete():
    dob = date(
        2020,
        1,
        1,
    )

    assessment = date(
        2026,
        6,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
            events=[
                (
                    date(
                        2025,
                        1,
                        1,
                    ),
                    S,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "not_due_now"


def test_age60_routes_to_special_pathway():
    dob = date(
        1966,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_fractional_only_regularization_precedes_ordinary_history():
    dob = date(
        2010,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
            events=[
                (
                    date(
                        2018,
                        2,
                        1,
                    ),
                    F,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
        interaction=clear_interaction(),
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_two_pre_fractional_standard_doses_still_require_regularization():
    dob = date(
        2010,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
            events=[
                (
                    date(
                        2011,
                        1,
                        1,
                    ),
                    S,
                ),
                (
                    date(
                        2012,
                        1,
                        1,
                    ),
                    S,
                ),
                (
                    date(
                        2018,
                        2,
                        1,
                    ),
                    F,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
        interaction=clear_interaction(),
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_later_standard_regularization_then_complete():
    dob = date(
        2010,
        1,
        1,
    )

    assessment = date(
        2026,
        6,
        1,
    )

    history = normalized(
        assessment=assessment,
        dob=dob,
        events=[
            (
                date(
                    2011,
                    1,
                    1,
                ),
                S,
            ),
            (
                date(
                    2012,
                    1,
                    1,
                ),
                S,
            ),
            (
                date(
                    2018,
                    2,
                    1,
                ),
                F,
            ),
            (
                date(
                    2026,
                    1,
                    1,
                ),
                S,
            ),
        ],
    )

    assert (
        history[
            "fractional_regularization_third_standard_allowed"
        ]
        is True
    )

    result = evaluate(
        history,
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "not_due_now"


def interaction(
    *,
    state=(
        "screened_relevant_live_vaccine_history"
    ),
    recent=None,
    planned=None,
    emergency="not_present",
    exceptional15=False,
):
    return schemas.PniYellowFeverInteractionContext(
        history_screen_state=state,
        recent_live_vaccine_events=[
            schemas.PniYellowFeverLiveVaccineEvent(
                vaccine_group=group,
                administration_date=event_date,
            )
            for group, event_date
            in (
                recent
                or []
            )
        ],
        planned_same_day_vaccine_groups=(
            planned
            or []
        ),
        epidemiologic_emergency_concomitant_circulation_state=(
            emergency
        ),
        exceptional_15_day_interval_authorized=(
            exceptional15
        ),
    )


def due_child_history(
    *,
    assessment,
    dob,
):
    return normalized(
        assessment=assessment,
        dob=dob,
    )


def test_under2_mmr_same_day_without_emergency_not_routine():
    dob = date(
        2025,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        due_child_history(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
        interaction=interaction(
            state=(
                "screened_no_relevant_recent_live_vaccine"
            ),
            planned=[
                "mmr",
            ],
            emergency="not_present",
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_under2_mmr_same_day_requires_emergency_assessment():
    dob = date(
        2025,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        due_child_history(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
        interaction=interaction(
            state=(
                "screened_no_relevant_recent_live_vaccine"
            ),
            planned=[
                "mmr",
            ],
            emergency="not_assessed",
        ),
    )

    assert result[
        "decision"
    ] == "context_required"


def test_under2_mmr_same_day_explicit_emergency_allowed():
    dob = date(
        2025,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        due_child_history(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
        interaction=interaction(
            state=(
                "screened_no_relevant_recent_live_vaccine"
            ),
            planned=[
                "mmr",
            ],
            emergency="present",
        ),
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_under2_varicella_same_day_allowed():
    dob = date(
        2025,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        due_child_history(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
        interaction=interaction(
            state=(
                "screened_no_relevant_recent_live_vaccine"
            ),
            planned=[
                "varicella",
            ],
        ),
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_exact_age2_mmr_same_day_allowed():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        due_child_history(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
        interaction=interaction(
            state=(
                "screened_no_relevant_recent_live_vaccine"
            ),
            planned=[
                "mmr",
            ],
        ),
    )

    assert result[
        "decision"
    ] == "recommend_now"


@pytest.mark.parametrize(
    "group",
    [
        "mmr",
        "mmrv",
        "varicella",
    ],
)
def test_live_vaccine_day29_block_day30_clear(
    group,
):
    dob = date(
        2020,
        1,
        1,
    )

    prior = date(
        2026,
        1,
        1,
    )

    day29 = (
        prior
        + timedelta(
            days=29,
        )
    )

    day30 = (
        prior
        + timedelta(
            days=30,
        )
    )

    result29 = evaluate(
        normalized(
            assessment=day29,
            dob=dob,
        ),
        assessment=day29,
        dob=dob,
        interaction=interaction(
            recent=[
                (
                    group,
                    prior,
                ),
            ],
        ),
    )

    result30 = evaluate(
        normalized(
            assessment=day30,
            dob=dob,
        ),
        assessment=day30,
        dob=dob,
        interaction=interaction(
            recent=[
                (
                    group,
                    prior,
                ),
            ],
        ),
    )

    assert result29[
        "decision"
    ] == "not_due_now"

    assert result29[
        "recommended_date"
    ] == day30

    assert result30[
        "decision"
    ] == "recommend_now"


@pytest.mark.parametrize(
    "group",
    [
        "mmr",
        "mmrv",
        "varicella",
    ],
)
def test_explicit_15_day_exception_for_supported_groups(
    group,
):
    dob = date(
        2020,
        1,
        1,
    )

    prior = date(
        2026,
        1,
        1,
    )

    day14 = (
        prior
        + timedelta(
            days=14,
        )
    )

    day15 = (
        prior
        + timedelta(
            days=15,
        )
    )

    result14 = evaluate(
        normalized(
            assessment=day14,
            dob=dob,
        ),
        assessment=day14,
        dob=dob,
        interaction=interaction(
            recent=[
                (
                    group,
                    prior,
                ),
            ],
            exceptional15=True,
        ),
    )

    result15 = evaluate(
        normalized(
            assessment=day15,
            dob=dob,
        ),
        assessment=day15,
        dob=dob,
        interaction=interaction(
            recent=[
                (
                    group,
                    prior,
                ),
            ],
            exceptional15=True,
        ),
    )

    assert result14[
        "decision"
    ] == "not_due_now"

    assert result14[
        "recommended_date"
    ] == day15

    assert result15[
        "decision"
    ] == "recommend_now"


def test_dengue_does_not_inherit_15_day_exception():
    dob = date(
        2020,
        1,
        1,
    )

    prior = date(
        2026,
        1,
        1,
    )

    assessment = (
        prior
        + timedelta(
            days=15,
        )
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
        interaction=interaction(
            recent=[
                (
                    "dengue",
                    prior,
                ),
            ],
            exceptional15=True,
        ),
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == (
        prior
        + timedelta(
            days=30,
        )
    )


def test_age2plus_dengue_same_day_allowed():
    dob = date(
        2020,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
        interaction=interaction(
            state=(
                "screened_no_relevant_recent_live_vaccine"
            ),
            planned=[
                "dengue",
            ],
        ),
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_under2_dengue_interaction_routes_review():
    dob = date(
        2025,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
        interaction=interaction(
            state=(
                "screened_no_relevant_recent_live_vaccine"
            ),
            planned=[
                "dengue",
            ],
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_not_due_vfa_does_not_require_interaction_context():
    dob = date(
        2022,
        1,
        1,
    )

    first = date(
        2022,
        10,
        1,
    )

    assessment = date(
        2025,
        1,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
            events=[
                (
                    first,
                    S,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
        routine_context="not_screened",
        interaction=None,
        safety="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"


def test_partial_history_requires_history():
    dob = date(
        2020,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
            state="unknown",
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "history_required"


def test_bilingual_language_neutral_result():
    dob = date(
        2020,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
        interaction=clear_interaction(),
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

    assert validated.decision == "recommend_now"

    assert (
        validated.special_condition_inferred
        is False
    )

    assert (
        validated.synthetic_score_applied
        is False
    )
