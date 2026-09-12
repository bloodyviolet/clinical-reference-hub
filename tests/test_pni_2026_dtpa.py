from datetime import date, timedelta

import pytest

import schemas

from clinical_tools import pni_2026

from clinical_tools.pni_history import (
    normalize_diphtheria_tetanus_toxoid_history,
)


ASSESSMENT_DATE = date(
    2026,
    9,
    11,
)


def dose(
    administration_date,
    *,
    gestational_week=None,
    episode=None,
    product_key=None,
):
    return schemas.PniDoseRecord(
        administration_date=administration_date,
        gestational_age_weeks_at_administration=gestational_week,
        pregnancy_episode_key=episode,
        product_key=product_key,
        documentation_source="official_registry",
    )


def history(
    vaccine_key,
    state,
    *,
    doses=None,
):
    return schemas.PniVaccineHistory(
        vaccine_key=vaccine_key,
        history_state=state,
        doses=doses or [],
    )


def normalised(
    histories=None,
    *,
    scope="complete",
):
    return (
        normalize_diphtheria_tetanus_toxoid_history(
            assessment_date=ASSESSMENT_DATE,
            histories=histories or [],
            history_scope=scope,
        )
    )


def evaluate(
    **overrides,
):
    values = {
        "assessment_date":
            ASSESSMENT_DATE,

        "pregnancy_status":
            "pregnant",

        "gestational_age_weeks":
            20,

        "pregnancy_episode_key":
            "P-CURRENT",

        "postpartum_days":
            None,

        "postpartum_pregnancy_episode_key":
            None,

        "antigen_history":
            normalised(),

        "administration_safety_screen_state":
            "screened_no_concern",

        "exceptional_minimum_interval_authorized":
            False,
    }

    values.update(
        overrides
    )

    result = (
        pni_2026
        .evaluate_pni_dtpa_maternal_routine(
            **values
        )
    )

    schemas.PniRuleResult.model_validate(
        result
    )

    assert (
        result[
            "interpretation_pt"
        ].strip()
    )

    assert (
        result[
            "interpretation_en"
        ].strip()
    )

    assert (
        result[
            "interpretation_pt"
        ]
        != result[
            "interpretation_en"
        ]
    )

    return result


def test_rule_id_is_stable():
    assert (
        pni_2026.DTPA_MATERNAL_RULE_ID
        == "PNI26-DTPA-MATERNAL-ROUTINE-001"
    )


def test_nonpregnant_nonpostpartum_is_not_applicable_bilingually():
    result = evaluate(
        pregnancy_status="not_pregnant",
        gestational_age_weeks=None,
        pregnancy_episode_key=None,
    )

    assert (
        result[
            "decision"
        ]
        == "not_applicable"
    )


def test_unknown_pregnancy_state_requires_context_bilingually():
    result = evaluate(
        pregnancy_status="unknown",
        gestational_age_weeks=None,
        pregnancy_episode_key=None,
    )

    assert (
        result[
            "decision"
        ]
        == "context_required"
    )

    assert result[
        "missing_context"
    ] == [
        "pregnancy_status",
    ]


def test_missing_gestational_age_requires_context():
    result = evaluate(
        gestational_age_weeks=None,
    )

    assert (
        result[
            "decision"
        ]
        == "context_required"
    )


def test_week_19_is_not_due_now():
    result = evaluate(
        gestational_age_weeks=19,
    )

    assert (
        result[
            "decision"
        ]
        == "not_due_now"
    )


def test_exact_week_20_zero_exposure_recommends_now():
    result = evaluate()

    assert (
        result[
            "decision"
        ]
        == "recommend_now"
    )

    assert (
        "duas doses de dT"
        in result[
            "interpretation_pt"
        ]
    )

    assert (
        "two dT doses"
        in result[
            "interpretation_en"
        ]
    )


def test_one_prior_dt_exposure_recommends_now_and_preserves_series_context():
    dt_date = (
        ASSESSMENT_DATE
        - timedelta(
            days=90,
        )
    )

    result = evaluate(
        antigen_history=normalised([
            history(
                "dt",
                "documented_doses",
                doses=[
                    dose(
                        dt_date,
                    ),
                ],
            ),
        ]),
    )

    assert (
        result[
            "decision"
        ]
        == "recommend_now"
    )

    assert (
        "resta uma dose de dT"
        in result[
            "interpretation_pt"
        ]
    )


def test_two_prior_exposures_allow_dtpa_to_compose_third():
    result = evaluate(
        antigen_history=normalised([
            history(
                "dt",
                "documented_doses",
                doses=[
                    dose(
                        ASSESSMENT_DATE
                        - timedelta(
                            days=180,
                        )
                    ),
                    dose(
                        ASSESSMENT_DATE
                        - timedelta(
                            days=90,
                        )
                    ),
                ],
            ),
        ]),
    )

    assert (
        result[
            "decision"
        ]
        == "recommend_now"
    )

    assert (
        "terceira dose"
        in result[
            "interpretation_pt"
        ]
    )


def test_complete_basic_series_still_gets_pregnancy_dtpa():
    result = evaluate(
        antigen_history=normalised([
            history(
                "dt",
                "documented_doses",
                doses=[
                    dose(
                        date(
                            2010,
                            1,
                            1,
                        )
                    ),
                    dose(
                        date(
                            2010,
                            3,
                            2,
                        )
                    ),
                    dose(
                        date(
                            2010,
                            5,
                            1,
                        )
                    ),
                ],
            ),
        ]),
    )

    assert (
        result[
            "decision"
        ]
        == "recommend_now"
    )


def test_current_pregnancy_dtpa_at_week_20_suppresses_repeat():
    result = evaluate(
        gestational_age_weeks=30,
        antigen_history=normalised([
            history(
                "dtpa",
                "documented_doses",
                doses=[
                    dose(
                        ASSESSMENT_DATE
                        - timedelta(
                            days=60,
                        ),
                        gestational_week=21,
                        episode="P-CURRENT",
                        product_key="dtpa",
                    ),
                ],
            ),
        ]),
    )

    assert (
        result[
            "decision"
        ]
        == "not_due_now"
    )


def test_current_pregnancy_dtpa_before_week_20_routes_special_review():
    result = evaluate(
        gestational_age_weeks=30,
        antigen_history=normalised([
            history(
                "dtpa",
                "documented_doses",
                doses=[
                    dose(
                        ASSESSMENT_DATE
                        - timedelta(
                            days=90,
                        ),
                        gestational_week=18,
                        episode="P-CURRENT",
                        product_key="dtpa",
                    ),
                ],
            ),
        ]),
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_current_pregnancy_dtpa_without_timing_requires_context():
    result = evaluate(
        gestational_age_weeks=30,
        antigen_history=normalised([
            history(
                "dtpa",
                "documented_doses",
                doses=[
                    dose(
                        ASSESSMENT_DATE
                        - timedelta(
                            days=90,
                        ),
                        gestational_week=None,
                        episode="P-CURRENT",
                        product_key="dtpa",
                    ),
                ],
            ),
        ]),
    )

    assert (
        result[
            "decision"
        ]
        == "context_required"
    )


def test_previous_pregnancy_dtpa_does_not_satisfy_current_pregnancy():
    result = evaluate(
        gestational_age_weeks=30,
        antigen_history=normalised([
            history(
                "dtpa",
                "documented_doses",
                doses=[
                    dose(
                        date(
                            2025,
                            1,
                            1,
                        ),
                        gestational_week=24,
                        episode="P-PREVIOUS",
                        product_key="dtpa",
                    ),
                ],
            ),
        ]),
    )

    assert (
        result[
            "decision"
        ]
        == "recommend_now"
    )


def test_unassigned_dtpa_episode_fails_closed():
    result = evaluate(
        gestational_age_weeks=30,
        antigen_history=normalised([
            history(
                "dtpa",
                "documented_doses",
                doses=[
                    dose(
                        date(
                            2025,
                            1,
                            1,
                        ),
                        gestational_week=24,
                        episode=None,
                        product_key="dtpa",
                    ),
                ],
            ),
        ]),
    )

    assert (
        result[
            "decision"
        ]
        == "context_required"
    )


def test_partial_toxoid_history_requires_history_reconciliation():
    result = evaluate(
        antigen_history=normalised(
            [
                history(
                    "dt",
                    "documented_doses",
                    doses=[
                        dose(
                            date(
                                2020,
                                1,
                                1,
                            )
                        ),
                    ],
                ),
            ],
            scope="partial",
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "history_required"
    )

    assert (
        result[
            "history_required"
        ]
        is True
    )


def test_59_days_without_exception_is_future_recommendation():
    last = (
        ASSESSMENT_DATE
        - timedelta(
            days=59,
        )
    )

    result = evaluate(
        antigen_history=normalised([
            history(
                "dt",
                "documented_doses",
                doses=[
                    dose(
                        last,
                    ),
                ],
            ),
        ]),
    )

    assert (
        result[
            "decision"
        ]
        == "future_recommendation"
    )

    assert (
        result[
            "recommended_date"
        ]
        == (
            last
            + timedelta(
                days=60,
            )
        )
    )

    assert (
        result[
            "minimum_interval_applied"
        ]
        is False
    )


def test_30_days_with_explicit_exception_recommends_now():
    last = (
        ASSESSMENT_DATE
        - timedelta(
            days=30,
        )
    )

    result = evaluate(
        antigen_history=normalised([
            history(
                "dt",
                "documented_doses",
                doses=[
                    dose(
                        last,
                    ),
                ],
            ),
        ]),
        exceptional_minimum_interval_authorized=True,
    )

    assert (
        result[
            "decision"
        ]
        == "recommend_now"
    )

    assert (
        result[
            "minimum_interval_applied"
        ]
        is True
    )

    assert (
        result[
            "minimum_interval_days"
        ]
        == 30
    )

    assert (
        result[
            "recommended_interval_days"
        ]
        == 60
    )


def test_29_days_with_exception_waits_until_day_30():
    last = (
        ASSESSMENT_DATE
        - timedelta(
            days=29,
        )
    )

    result = evaluate(
        antigen_history=normalised([
            history(
                "dt",
                "documented_doses",
                doses=[
                    dose(
                        last,
                    ),
                ],
            ),
        ]),
        exceptional_minimum_interval_authorized=True,
    )

    assert (
        result[
            "decision"
        ]
        == "future_recommendation"
    )

    assert (
        result[
            "recommended_date"
        ]
        == (
            last
            + timedelta(
                days=30,
            )
        )
    )

    assert (
        result[
            "minimum_interval_applied"
        ]
        is True
    )


def test_29_days_without_exception_waits_until_day_60():
    last = (
        ASSESSMENT_DATE
        - timedelta(
            days=29,
        )
    )

    result = evaluate(
        antigen_history=normalised([
            history(
                "dt",
                "documented_doses",
                doses=[
                    dose(
                        last,
                    ),
                ],
            ),
        ]),
    )

    assert (
        result[
            "recommended_date"
        ]
        == (
            last
            + timedelta(
                days=60,
            )
        )
    )

    assert (
        result[
            "minimum_interval_applied"
        ]
        is False
    )


def test_exception_is_never_inferred_from_pregnancy():
    last = (
        ASSESSMENT_DATE
        - timedelta(
            days=45,
        )
    )

    result = evaluate(
        gestational_age_weeks=38,
        antigen_history=normalised([
            history(
                "dt",
                "documented_doses",
                doses=[
                    dose(
                        last,
                    ),
                ],
            ),
        ]),
        exceptional_minimum_interval_authorized=False,
    )

    assert (
        result[
            "decision"
        ]
        == "future_recommendation"
    )

    assert (
        result[
            "minimum_interval_applied"
        ]
        is False
    )


def test_unscreened_calendar_due_does_not_auto_recommend():
    result = evaluate(
        administration_safety_screen_state="not_screened",
    )

    assert (
        result[
            "decision"
        ]
        == "context_required"
    )

    assert result[
        "missing_context"
    ] == [
        "administration_safety_screen_state",
    ]


def test_safety_concern_routes_special_review():
    result = evaluate(
        administration_safety_screen_state="screened_concern",
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_postpartum_day_45_missed_dose_recommends_now():
    result = evaluate(
        pregnancy_status="not_pregnant",
        gestational_age_weeks=None,
        pregnancy_episode_key=None,
        postpartum_days=45,
        postpartum_pregnancy_episode_key="P-RECENT",
    )

    assert (
        result[
            "decision"
        ]
        == "recommend_now"
    )

    assert (
        "45"
        in result[
            "interpretation_pt"
        ]
    )


def test_postpartum_day_46_is_not_applicable():
    result = evaluate(
        pregnancy_status="not_pregnant",
        gestational_age_weeks=None,
        pregnancy_episode_key=None,
        postpartum_days=46,
        postpartum_pregnancy_episode_key="P-RECENT",
    )

    assert (
        result[
            "decision"
        ]
        == "not_applicable"
    )


def test_postpartum_requires_recent_pregnancy_identity():
    result = evaluate(
        pregnancy_status="not_pregnant",
        gestational_age_weeks=None,
        pregnancy_episode_key=None,
        postpartum_days=10,
        postpartum_pregnancy_episode_key=None,
    )

    assert (
        result[
            "decision"
        ]
        == "context_required"
    )


def test_dtpa_given_after_delivery_suppresses_postpartum_repeat():
    delivery = (
        ASSESSMENT_DATE
        - timedelta(
            days=10,
        )
    )

    result = evaluate(
        pregnancy_status="not_pregnant",
        gestational_age_weeks=None,
        pregnancy_episode_key=None,
        postpartum_days=10,
        postpartum_pregnancy_episode_key="P-RECENT",
        antigen_history=normalised([
            history(
                "dtpa",
                "documented_doses",
                doses=[
                    dose(
                        delivery
                        + timedelta(
                            days=2,
                        ),
                        product_key="dtpa",
                    ),
                ],
            ),
        ]),
    )

    assert (
        result[
            "decision"
        ]
        == "not_due_now"
    )


def test_recent_pregnancy_qualifying_dtpa_suppresses_postpartum_dose():
    result = evaluate(
        pregnancy_status="not_pregnant",
        gestational_age_weeks=None,
        pregnancy_episode_key=None,
        postpartum_days=10,
        postpartum_pregnancy_episode_key="P-RECENT",
        antigen_history=normalised([
            history(
                "dtpa",
                "documented_doses",
                doses=[
                    dose(
                        ASSESSMENT_DATE
                        - timedelta(
                            days=60,
                        ),
                        gestational_week=24,
                        episode="P-RECENT",
                        product_key="dtpa",
                    ),
                ],
            ),
        ]),
    )

    assert (
        result[
            "decision"
        ]
        == "not_due_now"
    )


def test_recent_pregnancy_early_dtpa_routes_postpartum_special_review():
    result = evaluate(
        pregnancy_status="not_pregnant",
        gestational_age_weeks=None,
        pregnancy_episode_key=None,
        postpartum_days=10,
        postpartum_pregnancy_episode_key="P-RECENT",
        antigen_history=normalised([
            history(
                "dtpa",
                "documented_doses",
                doses=[
                    dose(
                        ASSESSMENT_DATE
                        - timedelta(
                            days=100,
                        ),
                        gestational_week=18,
                        episode="P-RECENT",
                        product_key="dtpa",
                    ),
                ],
            ),
        ]),
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_postpartum_interval_beyond_day_45_routes_special_review():
    # Assessment on postpartum day 40.
    # A dT dose 20 days ago means:
    # - standard 60-day interval -> postpartum day 80;
    # - exceptional 30-day interval -> postpartum day 50.
    # Neither fits within the maternal <=45-day window.
    result = evaluate(
        pregnancy_status="not_pregnant",
        gestational_age_weeks=None,
        pregnancy_episode_key=None,
        postpartum_days=40,
        postpartum_pregnancy_episode_key="P-RECENT",
        antigen_history=normalised([
            history(
                "dt",
                "documented_doses",
                doses=[
                    dose(
                        ASSESSMENT_DATE
                        - timedelta(
                            days=20,
                        )
                    ),
                ],
            ),
        ]),
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_future_recommendation_can_precede_postpartum_day_45():
    # Assessment on postpartum day 10.
    # Last dT was 40 days ago; standard day-60 date is in 20 days,
    # i.e. postpartum day 30.
    last = (
        ASSESSMENT_DATE
        - timedelta(
            days=40,
        )
    )

    result = evaluate(
        pregnancy_status="not_pregnant",
        gestational_age_weeks=None,
        pregnancy_episode_key=None,
        postpartum_days=10,
        postpartum_pregnancy_episode_key="P-RECENT",
        antigen_history=normalised([
            history(
                "dt",
                "documented_doses",
                doses=[
                    dose(
                        last,
                    ),
                ],
            ),
        ]),
    )

    assert (
        result[
            "decision"
        ]
        == "future_recommendation"
    )

    assert (
        result[
            "recommended_date"
        ]
        == (
            last
            + timedelta(
                days=60,
            )
        )
    )


def test_no_special_condition_inference_or_synthetic_score():
    result = evaluate()

    assert (
        result[
            "special_condition_inferred"
        ]
        is False
    )

    assert (
        result[
            "synthetic_score_applied"
        ]
        is False
    )


def test_provenance_is_national_and_current_snapshot():
    result = evaluate()

    provenance = result[
        "provenance"
    ]

    assert (
        provenance[
            "rule_id"
        ]
        == "PNI26-DTPA-MATERNAL-ROUTINE-001"
    )

    assert (
        provenance[
            "authority"
        ]
        == "Ministério da Saúde / SVSA / DPNI"
    )

    assert (
        provenance[
            "source_snapshot_date"
        ]
        == date(
            2026,
            9,
            11,
        )
    )


@pytest.mark.parametrize(
    "scenario",
    [
        {
            "gestational_age_weeks":
                19,
        },
        {
            "administration_safety_screen_state":
                "not_screened",
        },
        {
            "administration_safety_screen_state":
                "screened_concern",
        },
        {
            "pregnancy_status":
                "not_pregnant",
            "gestational_age_weeks":
                None,
            "pregnancy_episode_key":
                None,
            "postpartum_days":
                46,
            "postpartum_pregnancy_episode_key":
                "P-RECENT",
        },
    ],
)
def test_representative_decisions_are_always_pt_br_and_en_gb(
    scenario,
):
    result = evaluate(
        **scenario
    )

    assert (
        len(
            result[
                "interpretation_pt"
            ]
        )
        > 20
    )

    assert (
        len(
            result[
                "interpretation_en"
            ]
        )
        > 20
    )

    assert (
        result[
            "interpretation_pt"
        ]
        != result[
            "interpretation_en"
        ]
    )
