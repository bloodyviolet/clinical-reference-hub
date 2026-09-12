from datetime import date, timedelta

import pytest

import schemas

from clinical_tools.pni_2026 import (
    DT_ROUTINE_RULE_ID,
    evaluate_pni_dt_routine,
)

from clinical_tools.pni_history import (
    normalize_diphtheria_tetanus_toxoid_history,
)


DOB = date(
    2000,
    1,
    1,
)


def dose(
    administration_date,
    *,
    product_key=None,
):
    return schemas.PniDoseRecord(
        administration_date=administration_date,
        product_key=product_key,
        documentation_source="official_registry",
    )


def history(
    vaccine_key,
    dates,
):
    dates = list(
        dates
    )

    return schemas.PniVaccineHistory(
        vaccine_key=vaccine_key,
        history_state=(
            "documented_doses"
            if dates
            else "documented_zero_dose"
        ),
        doses=[
            dose(
                value,
                product_key=vaccine_key,
            )
            for value in dates
        ],
    )


def normalized(
    assessment,
    histories=None,
    *,
    scope="complete",
):
    return normalize_diphtheria_tetanus_toxoid_history(
        assessment_date=assessment,
        histories=list(
            histories
            or []
        ),
        history_scope=scope,
    )


def evaluate(
    assessment,
    antigen_history,
    *,
    dob=DOB,
    pregnancy="not_applicable",
    occupation="screened_no_dtpa_priority_occupation",
    exposure="screened_no_relevant_exposure",
    safety="screened_no_concern",
    exceptional=False,
):
    result = evaluate_pni_dt_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        antigen_history=antigen_history,
        pregnancy_status=pregnancy,
        dtpa_priority_occupation_state=occupation,
        exposure_risk_state=exposure,
        administration_safety_screen_state=safety,
        exceptional_minimum_interval_authorized=exceptional,
    )

    schemas.PniRuleResult.model_validate(
        result
    )

    return result


def test_rule_id():
    assert (
        DT_ROUTINE_RULE_ID
        == "PNI26-DT-ROUTINE-001"
    )


def test_under7_is_outside_dt_layer_without_due_context():
    dob = date(
        2020,
        1,
        1,
    )

    assessment = date(
        2026,
        12,
        31,
    )

    result = evaluate_pni_dt_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        antigen_history=normalized(
            assessment
        ),
        pregnancy_status="not_screened",
        dtpa_priority_occupation_state="not_screened",
        exposure_risk_state="not_screened",
        administration_safety_screen_state="not_screened",
        exceptional_minimum_interval_authorized=False,
    )

    assert result[
        "decision"
    ] == "not_applicable"

    assert result[
        "missing_context"
    ] == []


def test_exact7_zero_history_recommends_primary_D1():
    dob = date(
        2019,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        assessment,
        normalized(
            assessment
        ),
        dob=dob,
    )

    assert result[
        "decision"
    ] == "recommend_now"

    assert result[
        "vaccine_key"
    ] == "dt"


def test_one_primary_exposure_waits_60_days_without_exception():
    d1 = date(
        2026,
        1,
        1,
    )

    assessment = (
        d1
        + timedelta(
            days=59,
        )
    )

    result = evaluate(
        assessment,
        normalized(
            assessment,
            [
                history(
                    "dt",
                    [
                        d1,
                    ],
                ),
            ],
        ),
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == (
        d1
        + timedelta(
            days=60,
        )
    )

    assert result[
        "recommended_interval_days"
    ] == 60

    assert result[
        "minimum_interval_applied"
    ] is False


def test_explicit_exception_allows_primary_dose_at_day30():
    d1 = date(
        2026,
        1,
        1,
    )

    assessment = (
        d1
        + timedelta(
            days=30,
        )
    )

    result = evaluate(
        assessment,
        normalized(
            assessment,
            [
                history(
                    "dt",
                    [
                        d1,
                    ],
                ),
            ],
        ),
        exceptional=True,
    )

    assert result[
        "decision"
    ] == "recommend_now"

    assert result[
        "recommended_interval_days"
    ] == 60

    assert result[
        "minimum_interval_days"
    ] == 30

    assert result[
        "minimum_interval_applied"
    ] is True


def test_day30_without_exception_still_waits_for_day60():
    d1 = date(
        2026,
        1,
        1,
    )

    assessment = (
        d1
        + timedelta(
            days=30,
        )
    )

    result = evaluate(
        assessment,
        normalized(
            assessment,
            [
                history(
                    "dt",
                    [
                        d1,
                    ],
                ),
            ],
        ),
        exceptional=False,
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == (
        d1
        + timedelta(
            days=60,
        )
    )


def test_historical_45_day_interval_is_review_when_series_position_changes():
    d1 = date(
        2025,
        1,
        1,
    )

    d2 = (
        d1
        + timedelta(
            days=45,
        )
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        assessment,
        normalized(
            assessment,
            [
                history(
                    "dt",
                    [
                        d1,
                        d2,
                    ],
                ),
            ],
        ),
    )

    assert result[
        "decision"
    ] == "special_pathway_review"


def test_sub30_extra_can_be_skipped_when_later_ordinary_event_exists():
    d1 = date(
        2025,
        1,
        1,
    )

    extra = (
        d1
        + timedelta(
            days=20,
        )
    )

    d2 = (
        d1
        + timedelta(
            days=60,
        )
    )

    assessment = (
        d2
        + timedelta(
            days=60,
        )
    )

    result = evaluate(
        assessment,
        normalized(
            assessment,
            [
                history(
                    "dt",
                    [
                        d1,
                        extra,
                        d2,
                    ],
                ),
            ],
        ),
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_recent_sub30_extra_enforces_absolute_30_day_floor():
    d1 = date(
        2026,
        1,
        1,
    )

    extra = date(
        2026,
        1,
        21,
    )

    assessment = date(
        2026,
        3,
        2,
    )

    # d1+60d is Mar02 and the sub30 extra does not become
    # the next primary-series position. The latest physical
    # exposure is nevertheless protected by an absolute 30d
    # floor; here that floor was already met on Feb20.
    result = evaluate(
        assessment,
        normalized(
            assessment,
            [
                history(
                    "dt",
                    [
                        d1,
                        extra,
                    ],
                ),
            ],
        ),
        exceptional=False,
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_exceptional_path_respects_latest_physical_sub30_extra():
    d1 = date(
        2026,
        1,
        1,
    )

    extra = date(
        2026,
        1,
        21,
    )

    assessment = date(
        2026,
        2,
        19,
    )

    result = evaluate(
        assessment,
        normalized(
            assessment,
            [
                history(
                    "dt",
                    [
                        d1,
                        extra,
                    ],
                ),
            ],
        ),
        exceptional=True,
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == date(
        2026,
        2,
        20,
    )

    assert result[
        "minimum_interval_days"
    ] == 30

    assert result[
        "minimum_interval_applied"
    ] is True


def test_three_ordinary_spaced_exposures_prove_basic_completion_even_with_45d_extra():
    d1 = date(
        2010,
        1,
        1,
    )

    extra45 = (
        d1
        + timedelta(
            days=45,
        )
    )

    ordinary2 = (
        d1
        + timedelta(
            days=120,
        )
    )

    ordinary3 = (
        d1
        + timedelta(
            days=180,
        )
    )

    assessment = date(
        2011,
        1,
        1,
    )

    result = evaluate(
        assessment,
        normalized(
            assessment,
            [
                history(
                    "dt",
                    [
                        d1,
                        extra45,
                        ordinary2,
                        ordinary3,
                    ],
                ),
            ],
        ),
    )

    # Completion is independently proven by >=60d chronology.
    # Latest physical dose is recent, so booster is not due.
    assert result[
        "decision"
    ] == "not_due_now"


def test_latest_physical_dtpa_resets_booster_anchor():
    assessment = date(
        2029,
        1,
        1,
    )

    result = evaluate(
        assessment,
        normalized(
            assessment,
            [
                history(
                    "dt",
                    [
                        date(
                            2010,
                            1,
                            1,
                        ),
                        date(
                            2010,
                            3,
                            2,
                        ),
                        date(
                            2010,
                            5,
                            1,
                        ),
                    ],
                ),
                history(
                    "dtpa",
                    [
                        date(
                            2022,
                            6,
                            15,
                        ),
                    ],
                ),
            ],
        ),
        exposure="screened_no_relevant_exposure",
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == date(
        2032,
        6,
        15,
    )


def test_before5_years_exposure_context_not_requested():
    anchor = date(
        2022,
        1,
        1,
    )

    assessment = date(
        2026,
        12,
        31,
    )

    result = evaluate_pni_dt_routine(
        assessment_date=assessment,
        date_of_birth=DOB,
        antigen_history=normalized(
            assessment,
            [
                history(
                    "dt",
                    [
                        date(
                            2010,
                            1,
                            1,
                        ),
                        date(
                            2010,
                            3,
                            2,
                        ),
                        date(
                            2010,
                            5,
                            1,
                        ),
                        anchor,
                    ],
                ),
            ],
        ),
        pregnancy_status="not_screened",
        dtpa_priority_occupation_state="not_screened",
        exposure_risk_state="not_screened",
        administration_safety_screen_state="not_screened",
        exceptional_minimum_interval_authorized=False,
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "missing_context"
    ] == []


def test_5_to10_year_window_requires_exposure_screening():
    anchor = date(
        2020,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    hist = normalized(
        assessment,
        [
            history(
                "dt",
                [
                    date(
                        2010,
                        1,
                        1,
                    ),
                    date(
                        2010,
                        3,
                        2,
                    ),
                    date(
                        2010,
                        5,
                        1,
                    ),
                    anchor,
                ],
            ),
        ],
    )

    result = evaluate_pni_dt_routine(
        assessment_date=assessment,
        date_of_birth=DOB,
        antigen_history=hist,
        pregnancy_status="not_applicable",
        dtpa_priority_occupation_state=(
            "screened_no_dtpa_priority_occupation"
        ),
        exposure_risk_state="not_screened",
        administration_safety_screen_state="screened_no_concern",
        exceptional_minimum_interval_authorized=False,
    )

    assert result[
        "decision"
    ] == "context_required"

    assert result[
        "missing_context"
    ] == [
        "exposure_risk_state",
    ]


def test_5_year_relevant_exposure_activates_booster():
    anchor = date(
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
        assessment,
        normalized(
            assessment,
            [
                history(
                    "dt",
                    [
                        date(
                            2010,
                            1,
                            1,
                        ),
                        date(
                            2010,
                            3,
                            2,
                        ),
                        date(
                            2010,
                            5,
                            1,
                        ),
                        anchor,
                    ],
                ),
            ],
        ),
        exposure=(
            "screened_relevant_diphtheria_or_tetanus_exposure"
        ),
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_5_to10_year_no_exposure_waits_until10_years():
    anchor = date(
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
        assessment,
        normalized(
            assessment,
            [
                history(
                    "dt",
                    [
                        date(
                            2010,
                            1,
                            1,
                        ),
                        date(
                            2010,
                            3,
                            2,
                        ),
                        date(
                            2010,
                            5,
                            1,
                        ),
                        anchor,
                    ],
                ),
            ],
        ),
        exposure="screened_no_relevant_exposure",
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == date(
        2030,
        1,
        1,
    )


def test_10_year_booster_does_not_require_exposure_screening():
    anchor = date(
        2016,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate_pni_dt_routine(
        assessment_date=assessment,
        date_of_birth=DOB,
        antigen_history=normalized(
            assessment,
            [
                history(
                    "dt",
                    [
                        date(
                            2000,
                            3,
                            1,
                        ),
                        date(
                            2000,
                            5,
                            1,
                        ),
                        date(
                            2000,
                            7,
                            1,
                        ),
                        anchor,
                    ],
                ),
            ],
        ),
        pregnancy_status="not_applicable",
        dtpa_priority_occupation_state=(
            "screened_no_dtpa_priority_occupation"
        ),
        exposure_risk_state="not_screened",
        administration_safety_screen_state="screened_no_concern",
        exceptional_minimum_interval_authorized=False,
    )

    assert result[
        "decision"
    ] == "recommend_now"

    assert (
        "exposure_risk_state"
        not in result[
            "missing_context"
        ]
    )


def test_pregnancy_due_routes_to_review_not_contraindication_claim():
    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        assessment,
        normalized(
            assessment
        ),
        pregnancy="pregnant",
    )

    assert result[
        "decision"
    ] == "special_pathway_review"

    assert (
        "not treated here as contraindicated"
        in result[
            "interpretation_en"
        ].lower()
    )

    assert (
        "não é tratada aqui como contraindicada"
        in result[
            "interpretation_pt"
        ].lower()
    )


def test_unknown_pregnancy_requires_context_only_when_due():
    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        assessment,
        normalized(
            assessment
        ),
        pregnancy="unknown",
    )

    assert result[
        "decision"
    ] == "context_required"

    assert result[
        "missing_context"
    ] == [
        "pregnancy_status",
    ]


def test_dtpa_priority_occupation_routes_due_dose_to_review():
    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        assessment,
        normalized(
            assessment
        ),
        occupation="screened_dtpa_priority_occupation",
    )

    assert result[
        "decision"
    ] == "special_pathway_review"


def test_unscreened_dtpa_priority_occupation_requires_context():
    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        assessment,
        normalized(
            assessment
        ),
        occupation="not_screened",
    )

    assert result[
        "decision"
    ] == "context_required"

    assert result[
        "missing_context"
    ] == [
        "dtpa_priority_occupation_state",
    ]


def test_safety_concern_routes_to_review():
    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        assessment,
        normalized(
            assessment
        ),
        safety="screened_concern",
    )

    assert result[
        "decision"
    ] == "special_pathway_review"


def test_partial_toxoid_history_requires_history():
    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        assessment,
        normalized(
            assessment,
            [
                history(
                    "dt",
                    [
                        date(
                            2025,
                            1,
                            1,
                        ),
                    ],
                ),
            ],
            scope="partial",
        ),
    )

    assert result[
        "decision"
    ] == "history_required"

    assert result[
        "history_required"
    ] is True


def test_same_day_ambiguity_requires_history():
    assessment = date(
        2026,
        1,
        1,
    )

    same = date(
        2025,
        1,
        1,
    )

    result = evaluate(
        assessment,
        normalized(
            assessment,
            [
                history(
                    "dt",
                    [
                        same,
                    ],
                ),
                history(
                    "dtpa",
                    [
                        same,
                    ],
                ),
            ],
        ),
    )

    assert result[
        "decision"
    ] == "history_required"


def test_special_pathway_toxoid_product_routes_to_review():
    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        assessment,
        normalized(
            assessment,
            [
                history(
                    "hexa_acellular_rie",
                    [
                        date(
                            2025,
                            1,
                            1,
                        ),
                    ],
                ),
            ],
        ),
    )

    assert result[
        "decision"
    ] == "special_pathway_review"


def test_bilingual_language_neutral_output():
    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        assessment,
        normalized(
            assessment
        ),
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
