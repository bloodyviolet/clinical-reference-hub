from datetime import date, timedelta

import pytest

import schemas

from clinical_tools.pni_2026 import (
    MMR_RULE_ID,
    evaluate_pni_mmr_routine,
)

from clinical_tools.pni_history import (
    MMR_GENERAL_INTERVAL_EXCEPTION_AUTHORIZATION_KEY,
    MMR_PRODUCT_SCR,
    MMR_PRODUCT_SCRV,
    normalize_mmr_history,
)


SCR = MMR_PRODUCT_SCR
SCRV = MMR_PRODUCT_SCRV


def exception(
    from_date,
    to_date,
):
    return {
        "from_administration_date":
            from_date,

        "to_administration_date":
            to_date,

        "authorization_key":
            MMR_GENERAL_INTERVAL_EXCEPTION_AUTHORIZATION_KEY,
    }


def normalized(
    *,
    assessment,
    dob,
    events=None,
    state=None,
    scope="complete",
    exceptions=None,
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

    return normalize_mmr_history(
        assessment_date=assessment,
        date_of_birth=dob,
        history=schemas.PniVaccineHistory(
            vaccine_key="mmr",
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
        historical_interval_exception_events=(
            exceptions
            or []
        ),
    )


def clear_interaction():
    return schemas.PniMmrInteractionContext(
        history_screen_state=(
            "screened_no_relevant_recent_live_vaccine"
        ),
    )


def evaluate(
    history,
    *,
    assessment,
    dob,
    occupation="not_screened",
    pregnancy="not_applicable",
    special="screened_none",
    interaction=None,
    safety="screened_no_concern",
    exceptional=False,
):
    return evaluate_pni_mmr_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        mmr_history=history,
        occupation_context_state=occupation,
        pregnancy_status=pregnancy,
        special_condition_screen_state=special,
        interaction_context=interaction,
        administration_safety_screen_state=safety,
        exceptional_minimum_interval_authorized=exceptional,
    )


def test_rule_id():
    assert (
        MMR_RULE_ID
        == "PNI26-MMR-ROUTINE-001"
    )


def test_dedicated_interaction_model_exists():
    assert hasattr(
        schemas,
        "PniMmrInteractionContext",
    )

    assert not any(
        "mmr_interaction"
        in field.lower()
        for field
        in schemas.PniVaccineHistory.model_fields
    )


def test_before_12m_not_due():
    dob = date(
        2025,
        1,
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
        ),
        assessment=assessment,
        dob=dob,
        pregnancy="not_screened",
        special="not_screened",
        safety="not_screened",
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


def test_d0_can_delay_exact_12m_d1():
    dob = date(
        2025,
        1,
        1,
    )

    d0 = date(
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
                    d0,
                    SCR,
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


def test_exact_12m_zero_history_first_dose_due():
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
        interaction=clear_interaction(),
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_timely_d1_second_dose_nominally_at_15m():
    dob = date(
        2025,
        1,
        1,
    )

    first = date(
        2026,
        1,
        1,
    )

    assessment = date(
        2026,
        3,
        31,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
            events=[
                (
                    first,
                    SCR,
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
        4,
        1,
    )


def test_exact_15m_second_dose_due():
    dob = date(
        2025,
        1,
        1,
    )

    first = date(
        2026,
        1,
        1,
    )

    assessment = date(
        2026,
        4,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
            events=[
                (
                    first,
                    SCR,
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


def test_delayed_d1_day29_not_due_without_exception():
    dob = date(
        2025,
        1,
        1,
    )

    first = date(
        2026,
        6,
        1,
    )

    assessment = (
        first
        + timedelta(
            days=29,
        )
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
            events=[
                (
                    first,
                    SCR,
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
    ] == (
        first
        + timedelta(
            days=30,
        )
    )


def test_delayed_d1_day30_due():
    dob = date(
        2025,
        1,
        1,
    )

    first = date(
        2026,
        6,
        1,
    )

    assessment = (
        first
        + timedelta(
            days=30,
        )
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
            events=[
                (
                    first,
                    SCR,
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


def test_general_exception_day15_requires_occupation_when_unknown():
    dob = date(
        2025,
        1,
        1,
    )

    first = date(
        2026,
        6,
        1,
    )

    assessment = (
        first
        + timedelta(
            days=15,
        )
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
            events=[
                (
                    first,
                    SCR,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
        occupation="not_screened",
        exceptional=True,
    )

    assert result[
        "decision"
    ] == "context_required"


def test_general_exception_day15_non_health_worker_due():
    dob = date(
        2025,
        1,
        1,
    )

    first = date(
        2026,
        6,
        1,
    )

    assessment = (
        first
        + timedelta(
            days=15,
        )
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
            events=[
                (
                    first,
                    SCR,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
        occupation="not_health_worker",
        exceptional=True,
        interaction=clear_interaction(),
    )

    assert result[
        "decision"
    ] == "recommend_now"

    assert result[
        "minimum_interval_days"
    ] == 15

    assert result[
        "minimum_interval_applied"
    ] is True


def test_general_exception_does_not_shorten_health_worker_minimum():
    dob = date(
        2025,
        1,
        1,
    )

    first = date(
        2026,
        6,
        1,
    )

    assessment = (
        first
        + timedelta(
            days=15,
        )
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
            events=[
                (
                    first,
                    SCR,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
        occupation="health_worker",
        exceptional=True,
        interaction=clear_interaction(),
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == (
        first
        + timedelta(
            days=30,
        )
    )


def test_exact_age30_one_general_dose_needs_occupation_context():
    dob = date(
        1996,
        1,
        1,
    )

    first = date(
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
            events=[
                (
                    first,
                    SCR,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
        occupation="not_screened",
    )

    assert result[
        "decision"
    ] == "context_required"


def test_exact_age30_one_dose_non_health_worker_complete():
    dob = date(
        1996,
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
                        2025,
                        1,
                        1,
                    ),
                    SCR,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
        occupation="not_health_worker",
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] is None


def test_age30_zero_history_does_not_require_occupation_for_first_dose():
    dob = date(
        1996,
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
        occupation="not_screened",
        interaction=clear_interaction(),
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_age30_health_worker_one_dose_second_due_after_30d():
    dob = date(
        1996,
        1,
        1,
    )

    first = date(
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
            events=[
                (
                    first,
                    SCR,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
        occupation="health_worker",
        interaction=clear_interaction(),
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_two_occupational_valid_doses_complete_without_occupation_context():
    dob = date(
        1996,
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
                        2024,
                        1,
                        1,
                    ),
                    SCR,
                ),
                (
                    date(
                        2024,
                        2,
                        1,
                    ),
                    SCRV,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
        occupation="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"


def test_historical_general_short_series_requires_occupation_if_not_occupationally_complete():
    dob = date(
        2000,
        1,
        1,
    )

    first = date(
        2025,
        1,
        1,
    )

    second = (
        first
        + timedelta(
            days=20,
        )
    )

    assessment = date(
        2026,
        1,
        1,
    )

    history = normalized(
        assessment=assessment,
        dob=dob,
        events=[
            (
                first,
                SCR,
            ),
            (
                second,
                SCR,
            ),
        ],
        exceptions=[
            exception(
                first,
                second,
            ),
        ],
    )

    assert history[
        "general_valid_component_dose_count"
    ] == 2

    assert history[
        "occupational_valid_component_dose_count"
    ] == 1

    result = evaluate(
        history,
        assessment=assessment,
        dob=dob,
        occupation="not_screened",
    )

    assert result[
        "decision"
    ] == "context_required"


def test_historical_short_general_series_health_worker_needs_another_dose():
    dob = date(
        2000,
        1,
        1,
    )

    first = date(
        2025,
        1,
        1,
    )

    second = (
        first
        + timedelta(
            days=20,
        )
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
                    SCR,
                ),
                (
                    second,
                    SCR,
                ),
            ],
            exceptions=[
                exception(
                    first,
                    second,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
        occupation="health_worker",
        interaction=clear_interaction(),
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_pregnancy_not_requested_when_mmr_not_due():
    dob = date(
        2025,
        1,
        1,
    )

    assessment = date(
        2025,
        12,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
        pregnancy="not_screened",
        special="not_screened",
        interaction=None,
        safety="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"


def test_due_mmr_requires_pregnancy_context():
    dob = date(
        2000,
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
        pregnancy="not_screened",
        interaction=clear_interaction(),
    )

    assert result[
        "decision"
    ] == "context_required"


def test_pregnancy_routes_out_when_dose_due():
    dob = date(
        2000,
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
        pregnancy="pregnant",
        interaction=clear_interaction(),
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_due_mmr_requires_special_condition_screen():
    dob = date(
        2000,
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
        special="not_screened",
        interaction=clear_interaction(),
    )

    assert result[
        "decision"
    ] == "context_required"


def test_special_condition_routes_out():
    dob = date(
        2000,
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
        special="screened_special_condition_present",
        interaction=clear_interaction(),
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_due_mmr_requires_live_vaccine_context():
    dob = date(
        2000,
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
        interaction=None,
    )

    assert result[
        "decision"
    ] == "context_required"


def test_due_mmr_requires_administration_safety():
    dob = date(
        2000,
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
        safety="not_screened",
    )

    assert result[
        "decision"
    ] == "context_required"


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
    return schemas.PniMmrInteractionContext(
        history_screen_state=state,
        recent_live_vaccine_events=[
            schemas.PniMmrLiveVaccineEvent(
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


def test_under2_yellow_fever_same_day_requires_emergency_assessment():
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
                "yellow_fever",
            ],
            emergency="not_assessed",
        ),
    )

    assert result[
        "decision"
    ] == "context_required"


def test_under2_yellow_fever_same_day_routine_not_auto_recommended():
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
                "yellow_fever",
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


def test_under2_yellow_fever_same_day_explicit_emergency_allowed():
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
                "yellow_fever",
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
                "varicella",
            ],
        ),
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_under2_dengue_routes_review():
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


@pytest.mark.parametrize(
    "group",
    [
        "yellow_fever",
        "varicella",
        "dengue",
    ],
)
def test_age2plus_same_day_supported(
    group,
):
    dob = date(
        2000,
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
                group,
            ],
        ),
    )

    assert result[
        "decision"
    ] == "recommend_now"


@pytest.mark.parametrize(
    "group",
    [
        "yellow_fever",
        "varicella",
    ],
)
def test_external_15_day_exception_supported_groups(
    group,
):
    dob = date(
        2000,
        1,
        1,
    )

    prior = date(
        2025,
        12,
        1,
    )

    day15 = (
        prior
        + timedelta(
            days=15,
        )
    )

    result = evaluate(
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

    assert result[
        "decision"
    ] == "recommend_now"


def test_dengue_does_not_inherit_external_15_day_exception():
    dob = date(
        2000,
        1,
        1,
    )

    prior = date(
        2025,
        12,
        1,
    )

    day15 = (
        prior
        + timedelta(
            days=15,
        )
    )

    result = evaluate(
        normalized(
            assessment=day15,
            dob=dob,
        ),
        assessment=day15,
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


def test_age60_non_health_worker_no_routine_dose():
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
        occupation="not_health_worker",
        pregnancy="not_screened",
        special="not_screened",
        interaction=None,
        safety="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"


def test_age60_unknown_occupation_requires_context():
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
        occupation="not_screened",
    )

    assert result[
        "decision"
    ] == "context_required"


def test_age60_incomplete_health_worker_routes_risk_benefit_review():
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
            events=[
                (
                    date(
                        2020,
                        1,
                        1,
                    ),
                    SCR,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
        occupation="health_worker",
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_age60_complete_health_worker_no_additional_dose():
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
            events=[
                (
                    date(
                        2020,
                        1,
                        1,
                    ),
                    SCR,
                ),
                (
                    date(
                        2020,
                        2,
                        1,
                    ),
                    SCR,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
        occupation="health_worker",
    )

    assert result[
        "decision"
    ] == "not_due_now"


def test_partial_history_requires_history():
    dob = date(
        2000,
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
        2000,
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
