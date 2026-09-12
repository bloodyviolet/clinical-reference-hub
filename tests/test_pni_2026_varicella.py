from datetime import date, timedelta

import pytest
from pydantic import ValidationError

import schemas

from clinical_tools.pni_2026 import (
    VARICELLA_CHILD_RULE_ID,
    evaluate_pni_varicella_child_routine,
)

from clinical_tools.pni_history import (
    normalize_mmr_history,
    normalize_varicella_child_history,
)


def vaccine_history(
    key,
    dates=None,
):
    dates = list(
        dates
        or []
    )

    return schemas.PniVaccineHistory(
        vaccine_key=key,
        history_state=(
            "documented_doses"
            if dates
            else "documented_zero_dose"
        ),
        doses=[
            schemas.PniDoseRecord(
                administration_date=value,
                product_key=key,
                documentation_source="official_registry",
            )
            for value in dates
        ],
    )


def normalized(
    *,
    dob,
    assessment,
    vz_dates=None,
):
    mmr = normalize_mmr_history(
        assessment_date=assessment,
        date_of_birth=dob,
        history=schemas.PniVaccineHistory(
            vaccine_key="mmr",
            history_state="documented_zero_dose",
        ),
        history_scope="complete",
    )

    return normalize_varicella_child_history(
        assessment_date=assessment,
        date_of_birth=dob,
        varicella_history=vaccine_history(
            "varicella",
            vz_dates,
        ),
        varicella_history_scope="complete",
        mmr_history=mmr,
    )


def clear_interaction(
    *,
    recent=None,
    planned=None,
    exceptional=False,
):
    recent = list(
        recent
        or []
    )

    return schemas.PniVaricellaInteractionContext(
        history_screen_state=(
            "screened_relevant_live_vaccine_history"
            if recent
            else "screened_no_relevant_recent_live_vaccine"
        ),
        recent_live_vaccine_events=[
            schemas.PniVaricellaLiveVaccineEvent(
                vaccine_group=group,
                administration_date=event_date,
            )
            for group, event_date
            in recent
        ],
        planned_same_day_vaccine_groups=(
            planned
            or []
        ),
        exceptional_15_day_interval_authorized=exceptional,
    )


def evaluate(
    history,
    *,
    assessment,
    dob,
    disease="screened_no_prior_varicella",
    pregnancy="not_applicable",
    special="screened_none",
    interaction=None,
    safety="screened_no_concern",
):
    if interaction is None:
        interaction = clear_interaction()

    result = evaluate_pni_varicella_child_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        varicella_history=history,
        disease_history_state=disease,
        pregnancy_status=pregnancy,
        special_condition_screen_state=special,
        interaction_context=interaction,
        administration_safety_screen_state=safety,
    )

    schemas.PniRuleResult.model_validate(
        result
    )

    return result


def test_rule_id():
    assert (
        VARICELLA_CHILD_RULE_ID
        == "PNI26-VARICELLA-CHILD-ROUTINE-001"
    )


def test_interaction_schema_has_only_mmr_and_yellow_fever():
    assert schemas.PniVaricellaExternalLiveVaccineGroup == (
        pytest.importorskip(
            "typing"
        ).Literal[
            "mmr",
            "yellow_fever",
        ]
    )


def test_screened_clear_interaction_cannot_contain_event():
    with pytest.raises(
        ValidationError,
    ):
        schemas.PniVaricellaInteractionContext(
            history_screen_state=(
                "screened_no_relevant_recent_live_vaccine"
            ),
            recent_live_vaccine_events=[
                schemas.PniVaricellaLiveVaccineEvent(
                    vaccine_group="mmr",
                    administration_date=date(
                        2026,
                        1,
                        1,
                    ),
                ),
            ],
        )


def test_relevant_history_state_requires_event():
    with pytest.raises(
        ValidationError,
    ):
        schemas.PniVaricellaInteractionContext(
            history_screen_state=(
                "screened_relevant_live_vaccine_history"
            ),
        )


def test_before_exact15m_not_due_without_extra_context():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        3,
        31,
    )

    result = evaluate_pni_varicella_child_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        varicella_history=normalized(
            dob=dob,
            assessment=assessment,
        ),
        disease_history_state="not_screened",
        pregnancy_status="not_screened",
        special_condition_screen_state="not_screened",
        interaction_context=None,
        administration_safety_screen_state="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == date(
        2025,
        4,
        1,
    )

    assert result[
        "missing_context"
    ] == []


def test_exact15m_recommends_D1_when_gates_clear():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        4,
        1,
    )

    result = evaluate(
        normalized(
            dob=dob,
            assessment=assessment,
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "recommend_now"

    assert result[
        "recommended_date"
    ] == assessment


def test_due_D1_requires_disease_history_context():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        4,
        1,
    )

    result = evaluate(
        normalized(
            dob=dob,
            assessment=assessment,
        ),
        assessment=assessment,
        dob=dob,
        disease="not_screened",
    )

    assert result[
        "decision"
    ] == "context_required"

    assert (
        "varicella_disease_history_state"
        in result[
            "missing_context"
        ]
    )


def test_confirmed_prior_disease_suppresses_general_routine_dose():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        4,
        1,
    )

    result = evaluate(
        normalized(
            dob=dob,
            assessment=assessment,
        ),
        assessment=assessment,
        dob=dob,
        disease="screened_confirmed_prior_varicella",
        pregnancy="not_screened",
        special="not_screened",
        interaction=None,
        safety="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "missing_context"
    ] == []


def test_uncertain_prior_disease_allows_routine_vaccination():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        4,
        1,
    )

    result = evaluate(
        normalized(
            dob=dob,
            assessment=assessment,
        ),
        assessment=assessment,
        dob=dob,
        disease=(
            "screened_prior_varicella_history_uncertain"
        ),
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_timely_D1_preserves_age4_D2_agenda():
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
        normalized(
            dob=dob,
            assessment=assessment,
            vz_dates=[
                date(
                    2025,
                    4,
                    1,
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
        2028,
        1,
        1,
    )


def test_timely_D1_exact4y_recommends_D2():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2028,
        1,
        1,
    )

    result = evaluate(
        normalized(
            dob=dob,
            assessment=assessment,
            vz_dates=[
                date(
                    2025,
                    4,
                    1,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_delayed_D1_uses_three_month_catchup_not_age4():
    dob = date(
        2024,
        1,
        1,
    )

    d1 = date(
        2026,
        1,
        1,
    )

    before = date(
        2026,
        3,
        31,
    )

    due = date(
        2026,
        4,
        1,
    )

    waiting = evaluate(
        normalized(
            dob=dob,
            assessment=before,
            vz_dates=[
                d1,
            ],
        ),
        assessment=before,
        dob=dob,
    )

    assert waiting[
        "decision"
    ] == "not_due_now"

    assert waiting[
        "recommended_date"
    ] == due

    ready = evaluate(
        normalized(
            dob=dob,
            assessment=due,
            vz_dates=[
                d1,
            ],
        ),
        assessment=due,
        dob=dob,
    )

    assert ready[
        "decision"
    ] == "recommend_now"

    assert due < date(
        2028,
        1,
        1,
    )


def test_late_D1_can_close_D2_before_age7_without_compression():
    dob = date(
        2020,
        1,
        1,
    )

    assessment = date(
        2026,
        11,
        1,
    )

    result = evaluate_pni_varicella_child_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        varicella_history=normalized(
            dob=dob,
            assessment=assessment,
            vz_dates=[
                assessment,
            ],
        ),
        disease_history_state="not_screened",
        pregnancy_status="not_screened",
        special_condition_screen_state="not_screened",
        interaction_context=None,
        administration_safety_screen_state="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] is None

    assert result[
        "missing_context"
    ] == []


def test_exact7y_closes_general_child_layer():
    dob = date(
        2020,
        1,
        1,
    )

    assessment = date(
        2027,
        1,
        1,
    )

    result = evaluate_pni_varicella_child_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        varicella_history=normalized(
            dob=dob,
            assessment=assessment,
        ),
        disease_history_state="not_screened",
        pregnancy_status="not_screened",
        special_condition_screen_state="not_screened",
        interaction_context=None,
        administration_safety_screen_state="not_screened",
    )

    assert result[
        "decision"
    ] == "not_applicable"

    assert result[
        "missing_context"
    ] == []


def test_complete_series_requests_no_extra_context():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2028,
        1,
        1,
    )

    result = evaluate_pni_varicella_child_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        varicella_history=normalized(
            dob=dob,
            assessment=assessment,
            vz_dates=[
                date(
                    2025,
                    4,
                    1,
                ),
                date(
                    2028,
                    1,
                    1,
                ),
            ],
        ),
        disease_history_state="not_screened",
        pregnancy_status="not_screened",
        special_condition_screen_state="not_screened",
        interaction_context=None,
        administration_safety_screen_state="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "missing_context"
    ] == []


def test_due_path_pregnancy_missing_requires_context():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        4,
        1,
    )

    result = evaluate(
        normalized(
            dob=dob,
            assessment=assessment,
        ),
        assessment=assessment,
        dob=dob,
        pregnancy="not_screened",
    )

    assert result[
        "decision"
    ] == "context_required"

    assert (
        "pregnancy_status"
        in result[
            "missing_context"
        ]
    )


def test_due_path_pregnancy_routes_to_review():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        4,
        1,
    )

    result = evaluate(
        normalized(
            dob=dob,
            assessment=assessment,
        ),
        assessment=assessment,
        dob=dob,
        pregnancy="pregnant",
    )

    assert result[
        "decision"
    ] == "special_pathway_review"


def test_due_path_special_condition_and_safety_gates():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        4,
        1,
    )

    history = normalized(
        dob=dob,
        assessment=assessment,
    )

    missing_special = evaluate(
        history,
        assessment=assessment,
        dob=dob,
        special="not_screened",
    )

    assert missing_special[
        "decision"
    ] == "context_required"

    special = evaluate(
        history,
        assessment=assessment,
        dob=dob,
        special="screened_special_condition_present",
    )

    assert special[
        "decision"
    ] == "special_pathway_review"

    safety_missing = evaluate(
        history,
        assessment=assessment,
        dob=dob,
        safety="not_screened",
    )

    assert safety_missing[
        "decision"
    ] == "context_required"

    safety_concern = evaluate(
        history,
        assessment=assessment,
        dob=dob,
        safety="screened_concern",
    )

    assert safety_concern[
        "decision"
    ] == "special_pathway_review"


@pytest.mark.parametrize(
    "group",
    [
        "mmr",
        "yellow_fever",
    ],
)
def test_different_day_live_vaccine_ordinary_30_day_spacing(
    group,
):
    dob = date(
        2024,
        1,
        1,
    )

    prior = date(
        2025,
        4,
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

    wait = evaluate(
        normalized(
            dob=dob,
            assessment=day29,
        ),
        assessment=day29,
        dob=dob,
        interaction=clear_interaction(
            recent=[
                (
                    group,
                    prior,
                ),
            ],
        ),
    )

    assert wait[
        "decision"
    ] == "not_due_now"

    assert wait[
        "recommended_date"
    ] == day30

    ready = evaluate(
        normalized(
            dob=dob,
            assessment=day30,
        ),
        assessment=day30,
        dob=dob,
        interaction=clear_interaction(
            recent=[
                (
                    group,
                    prior,
                ),
            ],
        ),
    )

    assert ready[
        "decision"
    ] == "recommend_now"


@pytest.mark.parametrize(
    "group",
    [
        "mmr",
        "yellow_fever",
    ],
)
def test_explicit_15_day_live_vaccine_exception(
    group,
):
    dob = date(
        2024,
        1,
        1,
    )

    prior = date(
        2025,
        4,
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

    wait = evaluate(
        normalized(
            dob=dob,
            assessment=day14,
        ),
        assessment=day14,
        dob=dob,
        interaction=clear_interaction(
            recent=[
                (
                    group,
                    prior,
                ),
            ],
            exceptional=True,
        ),
    )

    assert wait[
        "decision"
    ] == "not_due_now"

    assert wait[
        "recommended_date"
    ] == day15

    ready = evaluate(
        normalized(
            dob=dob,
            assessment=day15,
        ),
        assessment=day15,
        dob=dob,
        interaction=clear_interaction(
            recent=[
                (
                    group,
                    prior,
                ),
            ],
            exceptional=True,
        ),
    )

    assert ready[
        "decision"
    ] == "recommend_now"


def test_same_day_yellow_fever_is_allowed_without_under2_emergency_gate():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        4,
        1,
    )

    result = evaluate(
        normalized(
            dob=dob,
            assessment=assessment,
        ),
        assessment=assessment,
        dob=dob,
        interaction=clear_interaction(
            planned=[
                "yellow_fever",
            ],
        ),
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_same_day_mmr_is_allowed():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        4,
        1,
    )

    result = evaluate(
        normalized(
            dob=dob,
            assessment=assessment,
        ),
        assessment=assessment,
        dob=dob,
        interaction=clear_interaction(
            planned=[
                "mmr",
            ],
        ),
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_due_path_missing_interaction_requires_context():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        4,
        1,
    )

    result = evaluate_pni_varicella_child_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        varicella_history=normalized(
            dob=dob,
            assessment=assessment,
        ),
        disease_history_state="screened_no_prior_varicella",
        pregnancy_status="not_applicable",
        special_condition_screen_state="screened_none",
        interaction_context=None,
        administration_safety_screen_state="screened_no_concern",
    )

    assert result[
        "decision"
    ] == "context_required"

    assert (
        "varicella_interaction_context"
        in result[
            "missing_context"
        ]
    )


def test_unsafe_history_routes_to_review_before_context_gates():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        3,
        31,
    )

    history = normalized(
        dob=dob,
        assessment=assessment,
        vz_dates=[
            assessment,
        ],
    )

    assert history[
        "safe_for_routine_evaluation"
    ] is False

    result = evaluate_pni_varicella_child_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        varicella_history=history,
        disease_history_state="not_screened",
        pregnancy_status="not_screened",
        special_condition_screen_state="not_screened",
        interaction_context=None,
        administration_safety_screen_state="not_screened",
    )

    assert result[
        "decision"
    ] == "special_pathway_review"

    assert result[
        "missing_context"
    ] == []


def test_result_is_bilingual_and_language_neutral():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        4,
        1,
    )

    result = evaluate(
        normalized(
            dob=dob,
            assessment=assessment,
        ),
        assessment=assessment,
        dob=dob,
    )

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
