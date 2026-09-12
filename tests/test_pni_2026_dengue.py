from datetime import date, timedelta

import pytest
from pydantic import ValidationError

import schemas

from clinical_tools.pni_2026 import (
    DENGUE_TAKEDA_RULE_ID,
    evaluate_pni_dengue_takeda_routine,
)

from clinical_tools.pni_history import (
    DENGUE_PRODUCT_BUTANTAN,
    DENGUE_PRODUCT_SANOFI_LEGACY,
    DENGUE_PRODUCT_TAKEDA,
    normalize_dengue_takeda_history,
)


def vaccine_history(
    events=None,
):
    events = list(
        events
        or []
    )

    return schemas.PniVaccineHistory(
        vaccine_key="dengue",
        history_state=(
            "documented_doses"
            if events
            else "documented_zero_dose"
        ),
        doses=[
            schemas.PniDoseRecord(
                administration_date=event_date,
                product_key=product,
                documentation_source="official_registry",
            )
            for event_date, product
            in events
        ],
    )


def normalized(
    *,
    dob,
    assessment,
    events=None,
):
    return normalize_dengue_takeda_history(
        assessment_date=assessment,
        date_of_birth=dob,
        history=vaccine_history(
            events
        ),
        history_scope="complete",
    )


def clear_timing():
    return schemas.PniDengueClinicalTimingContext(
        dengue_history_screen_state=(
            "screened_no_relevant_dengue_history"
        ),
        other_arbovirus_screen_state=(
            "screened_no_relevant_other_arbovirus"
        ),
        blood_product_screen_state=(
            "screened_no_relevant_blood_product_exposure"
        ),
    )


def clear_live():
    return schemas.PniDengueLiveVaccineInteractionContext(
        history_screen_state=(
            "screened_no_relevant_recent_live_vaccine"
        ),
    )


def evaluate(
    history,
    *,
    assessment,
    dob,
    timing=None,
    live=None,
    pregnancy="not_applicable",
    breastfeeding="not_applicable",
    special="screened_none",
    safety="screened_no_concern",
):
    if timing is None:
        timing = clear_timing()

    if live is None:
        live = clear_live()

    result = evaluate_pni_dengue_takeda_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        dengue_history=history,
        clinical_timing_context=timing,
        live_vaccine_interaction_context=live,
        pregnancy_status=pregnancy,
        breastfeeding_status=breastfeeding,
        special_condition_screen_state=special,
        administration_safety_screen_state=safety,
    )

    schemas.PniRuleResult.model_validate(
        result
    )

    return result


def test_rule_id():
    assert (
        DENGUE_TAKEDA_RULE_ID
        == "PNI26-DNG4-TAKEDA-ROUTINE-001"
    )


def test_timing_schema_rejects_clear_dengue_state_with_dates():
    with pytest.raises(
        ValidationError,
    ):
        schemas.PniDengueClinicalTimingContext(
            dengue_history_screen_state=(
                "screened_no_relevant_dengue_history"
            ),
            dengue_onset_dates=[
                date(
                    2026,
                    1,
                    1,
                ),
            ],
            other_arbovirus_screen_state=(
                "screened_no_relevant_other_arbovirus"
            ),
            blood_product_screen_state=(
                "screened_no_relevant_blood_product_exposure"
            ),
        )


def test_blood_product_minimum_requires_relevant_exposure():
    with pytest.raises(
        ValidationError,
    ):
        schemas.PniDengueClinicalTimingContext(
            dengue_history_screen_state=(
                "screened_no_relevant_dengue_history"
            ),
            other_arbovirus_screen_state=(
                "screened_no_relevant_other_arbovirus"
            ),
            blood_product_screen_state=(
                "screened_no_relevant_blood_product_exposure"
            ),
            minimum_6_week_interval_authorized=True,
        )


def test_live_schema_relevant_state_requires_event():
    with pytest.raises(
        ValidationError,
    ):
        schemas.PniDengueLiveVaccineInteractionContext(
            history_screen_state=(
                "screened_relevant_live_vaccine_history"
            ),
        )


def test_before_exact10_not_due_without_context():
    dob = date(
        2017,
        1,
        1,
    )

    assessment = date(
        2026,
        12,
        31,
    )

    result = evaluate_pni_dengue_takeda_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        dengue_history=normalized(
            dob=dob,
            assessment=assessment,
        ),
        clinical_timing_context=None,
        live_vaccine_interaction_context=None,
        pregnancy_status="not_screened",
        breastfeeding_status="not_screened",
        special_condition_screen_state="not_screened",
        administration_safety_screen_state="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == date(
        2027,
        1,
        1,
    )

    assert result[
        "missing_context"
    ] == []


def test_exact10_recommends_D1_when_all_gates_clear():
    dob = date(
        2016,
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


def test_zero_dose_exact15_closes_new_takeda_initiation():
    dob = date(
        2011,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate_pni_dengue_takeda_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        dengue_history=normalized(
            dob=dob,
            assessment=assessment,
        ),
        clinical_timing_context=None,
        live_vaccine_interaction_context=None,
        pregnancy_status="not_screened",
        breastfeeding_status="not_screened",
        special_condition_screen_state="not_screened",
        administration_safety_screen_state="not_screened",
    )

    assert result[
        "decision"
    ] == "not_applicable"

    assert result[
        "missing_context"
    ] == []


def test_valid_pre10_D1_waits_for_public_age10_floor():
    dob = date(
        2016,
        1,
        1,
    )

    d1 = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        1,
        1,
    )

    result = evaluate_pni_dengue_takeda_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        dengue_history=normalized(
            dob=dob,
            assessment=assessment,
            events=[
                (
                    d1,
                    DENGUE_PRODUCT_TAKEDA,
                ),
            ],
        ),
        clinical_timing_context=None,
        live_vaccine_interaction_context=None,
        pregnancy_status="not_screened",
        breastfeeding_status="not_screened",
        special_condition_screen_state="not_screened",
        administration_safety_screen_state="not_screened",
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

    assert result[
        "missing_context"
    ] == []


def test_pre15_D1_can_be_completed_after15():
    dob = date(
        2011,
        1,
        1,
    )

    d1 = date(
        2025,
        12,
        15,
    )

    assessment = (
        d1
        + timedelta(
            days=90,
        )
    )

    assert assessment > date(
        2026,
        1,
        1,
    )

    result = evaluate(
        normalized(
            dob=dob,
            assessment=assessment,
            events=[
                (
                    d1,
                    DENGUE_PRODUCT_TAKEDA,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_complete_series_requests_no_context():
    dob = date(
        2014,
        1,
        1,
    )

    d1 = date(
        2026,
        1,
        1,
    )

    d2 = (
        d1
        + timedelta(
            days=90,
        )
    )

    result = evaluate_pni_dengue_takeda_routine(
        assessment_date=d2,
        date_of_birth=dob,
        dengue_history=normalized(
            dob=dob,
            assessment=d2,
            events=[
                (
                    d1,
                    DENGUE_PRODUCT_TAKEDA,
                ),
                (
                    d2,
                    DENGUE_PRODUCT_TAKEDA,
                ),
            ],
        ),
        clinical_timing_context=None,
        live_vaccine_interaction_context=None,
        pregnancy_status="not_screened",
        breastfeeding_status="not_screened",
        special_condition_screen_state="not_screened",
        administration_safety_screen_state="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "missing_context"
    ] == []


def test_error_managed_takeda_butantan_completion_requests_no_context():
    dob = date(
        2014,
        1,
        1,
    )

    d1 = date(
        2026,
        1,
        1,
    )

    second = (
        d1
        + timedelta(
            days=30,
        )
    )

    result = evaluate_pni_dengue_takeda_routine(
        assessment_date=second,
        date_of_birth=dob,
        dengue_history=normalized(
            dob=dob,
            assessment=second,
            events=[
                (
                    d1,
                    DENGUE_PRODUCT_TAKEDA,
                ),
                (
                    second,
                    DENGUE_PRODUCT_BUTANTAN,
                ),
            ],
        ),
        clinical_timing_context=None,
        live_vaccine_interaction_context=None,
        pregnancy_status="not_screened",
        breastfeeding_status="not_screened",
        special_condition_screen_state="not_screened",
        administration_safety_screen_state="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "missing_context"
    ] == []


def test_unsafe_sanofi_history_routes_to_review_before_context():
    dob = date(
        2014,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate_pni_dengue_takeda_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        dengue_history=normalized(
            dob=dob,
            assessment=assessment,
            events=[
                (
                    assessment,
                    DENGUE_PRODUCT_SANOFI_LEGACY,
                ),
            ],
        ),
        clinical_timing_context=None,
        live_vaccine_interaction_context=None,
        pregnancy_status="not_screened",
        breastfeeding_status="not_screened",
        special_condition_screen_state="not_screened",
        administration_safety_screen_state="not_screened",
    )

    assert result[
        "decision"
    ] == "special_pathway_review"

    assert result[
        "missing_context"
    ] == []


def test_pure_D2_series_timing_stops_context_requests():
    dob = date(
        2014,
        1,
        1,
    )

    d1 = date(
        2026,
        1,
        1,
    )

    assessment = (
        d1
        + timedelta(
            days=89,
        )
    )

    result = evaluate_pni_dengue_takeda_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        dengue_history=normalized(
            dob=dob,
            assessment=assessment,
            events=[
                (
                    d1,
                    DENGUE_PRODUCT_TAKEDA,
                ),
            ],
        ),
        clinical_timing_context=None,
        live_vaccine_interaction_context=None,
        pregnancy_status="not_screened",
        breastfeeding_status="not_screened",
        special_condition_screen_state="not_screened",
        administration_safety_screen_state="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == (
        d1
        + timedelta(
            days=90,
        )
    )

    assert result[
        "missing_context"
    ] == []


def test_prior_dengue_D1_waits_six_calendar_months():
    dob = date(
        2014,
        1,
        1,
    )

    onset = date(
        2026,
        1,
        31,
    )

    assessment = date(
        2026,
        7,
        30,
    )

    timing = schemas.PniDengueClinicalTimingContext(
        dengue_history_screen_state=(
            "screened_dengue_history"
        ),
        dengue_onset_dates=[
            onset,
        ],
        other_arbovirus_screen_state=(
            "screened_no_relevant_other_arbovirus"
        ),
        blood_product_screen_state=(
            "screened_no_relevant_blood_product_exposure"
        ),
    )

    result = evaluate_pni_dengue_takeda_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        dengue_history=normalized(
            dob=dob,
            assessment=assessment,
        ),
        clinical_timing_context=timing,
        live_vaccine_interaction_context=None,
        pregnancy_status="not_screened",
        breastfeeding_status="not_screened",
        special_condition_screen_state="not_screened",
        administration_safety_screen_state="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == date(
        2026,
        7,
        31,
    )

    assert result[
        "missing_context"
    ] == []


def test_prior_dengue_threshold_reaching15_closes_D1():
    dob = date(
        2011,
        6,
        1,
    )

    assessment = date(
        2025,
        12,
        1,
    )

    onset = date(
        2025,
        12,
        1,
    )

    timing = schemas.PniDengueClinicalTimingContext(
        dengue_history_screen_state=(
            "screened_dengue_history"
        ),
        dengue_onset_dates=[
            onset,
        ],
        other_arbovirus_screen_state=(
            "screened_no_relevant_other_arbovirus"
        ),
        blood_product_screen_state=(
            "screened_no_relevant_blood_product_exposure"
        ),
    )

    result = evaluate_pni_dengue_takeda_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        dengue_history=normalized(
            dob=dob,
            assessment=assessment,
        ),
        clinical_timing_context=timing,
        live_vaccine_interaction_context=None,
        pregnancy_status="not_screened",
        breastfeeding_status="not_screened",
        special_condition_screen_state="not_screened",
        administration_safety_screen_state="not_screened",
    )

    assert result[
        "decision"
    ] == "not_applicable"

    assert result[
        "missing_context"
    ] == []


def test_post_D1_dengue_uses_30_day_floor_not_six_months():
    dob = date(
        2014,
        1,
        1,
    )

    d1 = date(
        2026,
        1,
        1,
    )

    onset = date(
        2026,
        3,
        20,
    )

    assessment = date(
        2026,
        4,
        18,
    )

    timing = schemas.PniDengueClinicalTimingContext(
        dengue_history_screen_state=(
            "screened_dengue_history"
        ),
        dengue_onset_dates=[
            onset,
        ],
        other_arbovirus_screen_state=(
            "screened_no_relevant_other_arbovirus"
        ),
        blood_product_screen_state=(
            "screened_no_relevant_blood_product_exposure"
        ),
    )

    result = evaluate_pni_dengue_takeda_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        dengue_history=normalized(
            dob=dob,
            assessment=assessment,
            events=[
                (
                    d1,
                    DENGUE_PRODUCT_TAKEDA,
                ),
            ],
        ),
        clinical_timing_context=timing,
        live_vaccine_interaction_context=None,
        pregnancy_status="not_screened",
        breastfeeding_status="not_screened",
        special_condition_screen_state="not_screened",
        administration_safety_screen_state="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == date(
        2026,
        4,
        19,
    )


def test_pre_D1_dengue_does_not_create_six_month_D2_delay():
    dob = date(
        2014,
        1,
        1,
    )

    d1 = date(
        2026,
        1,
        1,
    )

    assessment = (
        d1
        + timedelta(
            days=90,
        )
    )

    timing = schemas.PniDengueClinicalTimingContext(
        dengue_history_screen_state=(
            "screened_dengue_history"
        ),
        dengue_onset_dates=[
            date(
                2025,
                12,
                1,
            ),
        ],
        other_arbovirus_screen_state=(
            "screened_no_relevant_other_arbovirus"
        ),
        blood_product_screen_state=(
            "screened_no_relevant_blood_product_exposure"
        ),
    )

    result = evaluate(
        normalized(
            dob=dob,
            assessment=assessment,
            events=[
                (
                    d1,
                    DENGUE_PRODUCT_TAKEDA,
                ),
            ],
        ),
        assessment=assessment,
        dob=dob,
        timing=timing,
    )

    assert result[
        "decision"
    ] == "recommend_now"


@pytest.mark.parametrize(
    "disease",
    [
        "yellow_fever",
        "chikungunya",
        "zika",
    ],
)
def test_other_arbovirus_recovery_plus30_days(
    disease,
):
    dob = date(
        2014,
        1,
        1,
    )

    recovery = date(
        2026,
        1,
        1,
    )

    assessment = (
        recovery
        + timedelta(
            days=29,
        )
    )

    timing = schemas.PniDengueClinicalTimingContext(
        dengue_history_screen_state=(
            "screened_no_relevant_dengue_history"
        ),
        other_arbovirus_screen_state=(
            "screened_relevant_other_arbovirus_history"
        ),
        other_arbovirus_events=[
            schemas.PniDengueOtherArbovirusEvent(
                disease=disease,
                recovery_date=recovery,
            ),
        ],
        blood_product_screen_state=(
            "screened_no_relevant_blood_product_exposure"
        ),
    )

    result = evaluate_pni_dengue_takeda_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        dengue_history=normalized(
            dob=dob,
            assessment=assessment,
        ),
        clinical_timing_context=timing,
        live_vaccine_interaction_context=None,
        pregnancy_status="not_screened",
        breastfeeding_status="not_screened",
        special_condition_screen_state="not_screened",
        administration_safety_screen_state="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == (
        recovery
        + timedelta(
            days=30,
        )
    )


def test_blood_product_ordinary_wait_is_three_calendar_months():
    dob = date(
        2014,
        1,
        1,
    )

    treatment_end = date(
        2026,
        1,
        31,
    )

    assessment = date(
        2026,
        4,
        29,
    )

    timing = schemas.PniDengueClinicalTimingContext(
        dengue_history_screen_state=(
            "screened_no_relevant_dengue_history"
        ),
        other_arbovirus_screen_state=(
            "screened_no_relevant_other_arbovirus"
        ),
        blood_product_screen_state=(
            "screened_relevant_blood_product_exposure"
        ),
        latest_relevant_blood_product_treatment_end_date=(
            treatment_end
        ),
    )

    result = evaluate_pni_dengue_takeda_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        dengue_history=normalized(
            dob=dob,
            assessment=assessment,
        ),
        clinical_timing_context=timing,
        live_vaccine_interaction_context=None,
        pregnancy_status="not_screened",
        breastfeeding_status="not_screened",
        special_condition_screen_state="not_screened",
        administration_safety_screen_state="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == date(
        2026,
        4,
        30,
    )


def test_authorized_blood_product_six_week_minimum():
    dob = date(
        2014,
        1,
        1,
    )

    treatment_end = date(
        2026,
        1,
        31,
    )

    assessment = date(
        2026,
        3,
        14,
    )

    timing = schemas.PniDengueClinicalTimingContext(
        dengue_history_screen_state=(
            "screened_no_relevant_dengue_history"
        ),
        other_arbovirus_screen_state=(
            "screened_no_relevant_other_arbovirus"
        ),
        blood_product_screen_state=(
            "screened_relevant_blood_product_exposure"
        ),
        latest_relevant_blood_product_treatment_end_date=(
            treatment_end
        ),
        minimum_6_week_interval_authorized=True,
    )

    result = evaluate(
        normalized(
            dob=dob,
            assessment=assessment,
        ),
        assessment=assessment,
        dob=dob,
        timing=timing,
    )

    assert result[
        "decision"
    ] == "recommend_now"

    assert result[
        "minimum_interval_days"
    ] == 42

    assert result[
        "minimum_interval_applied"
    ] is True


def test_live_vaccine_day29_waits_and_day30_is_ready():
    dob = date(
        2014,
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

    wait = evaluate_pni_dengue_takeda_routine(
        assessment_date=day29,
        date_of_birth=dob,
        dengue_history=normalized(
            dob=dob,
            assessment=day29,
        ),
        clinical_timing_context=clear_timing(),
        live_vaccine_interaction_context=(
            schemas.PniDengueLiveVaccineInteractionContext(
                history_screen_state=(
                    "screened_relevant_live_vaccine_history"
                ),
                recent_live_vaccine_events=[
                    schemas.PniDengueExternalLiveVaccineEvent(
                        administration_date=prior,
                    ),
                ],
            )
        ),
        pregnancy_status="not_applicable",
        breastfeeding_status="not_applicable",
        special_condition_screen_state="screened_none",
        administration_safety_screen_state="screened_no_concern",
    )

    assert wait[
        "decision"
    ] == "not_due_now"

    assert wait[
        "recommended_date"
    ] == (
        prior
        + timedelta(
            days=30,
        )
    )

    day30 = (
        prior
        + timedelta(
            days=30,
        )
    )

    ready = evaluate(
        normalized(
            dob=dob,
            assessment=day30,
        ),
        assessment=day30,
        dob=dob,
        live=(
            schemas.PniDengueLiveVaccineInteractionContext(
                history_screen_state=(
                    "screened_relevant_live_vaccine_history"
                ),
                recent_live_vaccine_events=[
                    schemas.PniDengueExternalLiveVaccineEvent(
                        administration_date=prior,
                    ),
                ],
            )
        ),
    )

    assert ready[
        "decision"
    ] == "recommend_now"


def test_same_day_live_vaccine_is_allowed():
    dob = date(
        2014,
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
        ),
        assessment=assessment,
        dob=dob,
        live=(
            schemas.PniDengueLiveVaccineInteractionContext(
                history_screen_state=(
                    "screened_relevant_live_vaccine_history"
                ),
                recent_live_vaccine_events=[
                    schemas.PniDengueExternalLiveVaccineEvent(
                        administration_date=assessment,
                    ),
                ],
                planned_same_day_live_vaccine=True,
            )
        ),
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_timing_deferral_stops_reproductive_and_safety_requests():
    dob = date(
        2014,
        1,
        1,
    )

    onset = date(
        2026,
        1,
        1,
    )

    assessment = date(
        2026,
        2,
        1,
    )

    timing = schemas.PniDengueClinicalTimingContext(
        dengue_history_screen_state=(
            "screened_dengue_history"
        ),
        dengue_onset_dates=[
            onset,
        ],
        other_arbovirus_screen_state=(
            "not_screened"
        ),
        blood_product_screen_state=(
            "not_screened"
        ),
    )

    result = evaluate_pni_dengue_takeda_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        dengue_history=normalized(
            dob=dob,
            assessment=assessment,
        ),
        clinical_timing_context=timing,
        live_vaccine_interaction_context=None,
        pregnancy_status="not_screened",
        breastfeeding_status="not_screened",
        special_condition_screen_state="not_screened",
        administration_safety_screen_state="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "missing_context"
    ] == []


def test_pregnancy_and_breastfeeding_are_distinct_gates():
    dob = date(
        2014,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    hist = normalized(
        dob=dob,
        assessment=assessment,
    )

    pregnancy = evaluate(
        hist,
        assessment=assessment,
        dob=dob,
        pregnancy="pregnant",
        breastfeeding="not_breastfeeding",
    )

    breastfeeding = evaluate(
        hist,
        assessment=assessment,
        dob=dob,
        pregnancy="not_pregnant",
        breastfeeding="breastfeeding",
    )

    assert pregnancy[
        "decision"
    ] == "special_pathway_review"

    assert breastfeeding[
        "decision"
    ] == "special_pathway_review"


def test_unknown_pregnancy_and_breastfeeding_require_context_separately():
    dob = date(
        2014,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    hist = normalized(
        dob=dob,
        assessment=assessment,
    )

    pregnancy_missing = evaluate(
        hist,
        assessment=assessment,
        dob=dob,
        pregnancy="unknown",
        breastfeeding="not_breastfeeding",
    )

    breastfeeding_missing = evaluate(
        hist,
        assessment=assessment,
        dob=dob,
        pregnancy="not_pregnant",
        breastfeeding="unknown",
    )

    assert pregnancy_missing[
        "decision"
    ] == "context_required"

    assert pregnancy_missing[
        "missing_context"
    ] == [
        "pregnancy_status",
    ]

    assert breastfeeding_missing[
        "decision"
    ] == "context_required"

    assert breastfeeding_missing[
        "missing_context"
    ] == [
        "breastfeeding_status",
    ]


def test_special_condition_and_safety_gates():
    dob = date(
        2014,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    hist = normalized(
        dob=dob,
        assessment=assessment,
    )

    special = evaluate(
        hist,
        assessment=assessment,
        dob=dob,
        special="screened_special_condition_present",
    )

    safety = evaluate(
        hist,
        assessment=assessment,
        dob=dob,
        safety="screened_concern",
    )

    assert special[
        "decision"
    ] == "special_pathway_review"

    assert safety[
        "decision"
    ] == "special_pathway_review"


def test_output_is_bilingual_and_language_neutral():
    dob = date(
        2014,
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
