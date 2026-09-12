from datetime import date

import pytest

import schemas

from clinical_tools.pni_history import (
    DTP_HISTORY_MODEL_ID,
    normalize_dtp_child_history,
)


def history(
    key,
    dates=None,
    *,
    state=None,
    product_key=None,
    undated=0,
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
                product_key=(
                    product_key
                    if product_key is not None
                    else key
                ),
                documentation_source="official_registry",
            )
            for value in dates
        ],
        reported_prior_doses_without_exact_dates=undated,
    )


def normalize(
    *,
    dob,
    assessment,
    penta=None,
    dtp=None,
    scope="complete",
):
    if penta is None:
        penta = history(
            "pentavalent"
        )

    if dtp is None:
        dtp = history(
            "dtp"
        )

    return normalize_dtp_child_history(
        assessment_date=assessment,
        date_of_birth=dob,
        pentavalent_history=penta,
        dtp_history=dtp,
        history_scope=scope,
    )


def standard_penta_2024():
    return history(
        "pentavalent",
        [
            date(
                2024,
                3,
                1,
            ),
            date(
                2024,
                5,
                1,
            ),
            date(
                2024,
                7,
                1,
            ),
        ],
    )


def test_zero_history_is_structurally_safe():
    result = normalize(
        dob=date(
            2024,
            1,
            1,
        ),
        assessment=date(
            2025,
            4,
            1,
        ),
    )

    assert result[
        "model_id"
    ] == DTP_HISTORY_MODEL_ID

    assert result[
        "pentavalent_basic_series_complete"
    ] is False

    assert result[
        "dtp_r1_history_valid"
    ] is False

    assert result[
        "safe_for_routine_evaluation"
    ] is True


def test_valid_three_dose_penta_establishes_primary_series():
    result = normalize(
        dob=date(
            2024,
            1,
            1,
        ),
        assessment=date(
            2025,
            4,
            1,
        ),
        penta=standard_penta_2024(),
    )

    assert result[
        "pentavalent_basic_series_complete"
    ] is True

    assert result[
        "qualifying_pentavalent_d3_date"
    ] == date(
        2024,
        7,
        1,
    )

    assert result[
        "safe_for_routine_evaluation"
    ] is True


def test_valid_r1_is_preserved():
    result = normalize(
        dob=date(
            2024,
            1,
            1,
        ),
        assessment=date(
            2025,
            4,
            1,
        ),
        penta=standard_penta_2024(),
        dtp=history(
            "dtp",
            [
                date(
                    2025,
                    4,
                    1,
                ),
            ],
        ),
    )

    assert result[
        "dtp_r1_history_valid"
    ] is True

    assert result[
        "dtp_r1_event_date"
    ] == date(
        2025,
        4,
        1,
    )

    assert result[
        "safe_for_routine_evaluation"
    ] is True


def test_valid_r2_is_preserved():
    result = normalize(
        dob=date(
            2024,
            1,
            1,
        ),
        assessment=date(
            2028,
            1,
            1,
        ),
        penta=standard_penta_2024(),
        dtp=history(
            "dtp",
            [
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
    )

    assert result[
        "dtp_r1_history_valid"
    ] is True

    assert result[
        "dtp_r2_history_valid"
    ] is True

    assert result[
        "dtp_r2_event_date"
    ] == date(
        2028,
        1,
        1,
    )

    assert result[
        "safe_for_routine_evaluation"
    ] is True


def test_r1_before_exact_15_months_fails_closed():
    result = normalize(
        dob=date(
            2024,
            1,
            1,
        ),
        assessment=date(
            2025,
            3,
            31,
        ),
        penta=standard_penta_2024(),
        dtp=history(
            "dtp",
            [
                date(
                    2025,
                    3,
                    31,
                ),
            ],
        ),
    )

    assert result[
        "dtp_r1_history_valid"
    ] is False

    assert result[
        "safe_for_routine_evaluation"
    ] is False

    assert (
        "dtp_r1_before_exact_15_months"
        in result[
            "invalid_history_reasons"
        ]
    )


def test_exact_d3_plus_six_months_can_validate_r1():
    result = normalize(
        dob=date(
            2024,
            1,
            1,
        ),
        assessment=date(
            2025,
            4,
            1,
        ),
        penta=history(
            "pentavalent",
            [
                date(
                    2024,
                    6,
                    1,
                ),
                date(
                    2024,
                    8,
                    1,
                ),
                date(
                    2024,
                    10,
                    1,
                ),
            ],
        ),
        dtp=history(
            "dtp",
            [
                date(
                    2025,
                    4,
                    1,
                ),
            ],
        ),
    )

    assert result[
        "pentavalent_basic_series_complete"
    ] is True

    assert result[
        "dtp_r1_history_valid"
    ] is True


def test_d3_to_r1_under_six_calendar_months_fails_closed():
    # Isolate the interval firewall from the age firewall.
    #
    # DOB 2024-01-01 -> exact15m = 2025-04-01.
    # Penta D3 2024-11-01 -> +6 calendar months = 2025-05-01.
    #
    # Therefore DTP on 2025-04-01 satisfies the age requirement
    # but remains one calendar month short of the D3->R1 minimum.
    result = normalize(
        dob=date(
            2024,
            1,
            1,
        ),
        assessment=date(
            2025,
            4,
            1,
        ),
        penta=history(
            "pentavalent",
            [
                date(
                    2024,
                    7,
                    1,
                ),
                date(
                    2024,
                    9,
                    1,
                ),
                date(
                    2024,
                    11,
                    1,
                ),
            ],
        ),
        dtp=history(
            "dtp",
            [
                date(
                    2025,
                    4,
                    1,
                ),
            ],
        ),
    )

    assert result[
        "dtp_r1_history_valid"
    ] is False

    assert (
        "dtp_r1_before_exact_15_months"
        not in result[
            "invalid_history_reasons"
        ]
    )

    assert (
        "d3_to_r1_under_6_calendar_months"
        in result[
            "invalid_history_reasons"
        ]
    )


def test_r2_before_exact_four_years_fails_closed():
    result = normalize(
        dob=date(
            2024,
            1,
            1,
        ),
        assessment=date(
            2027,
            12,
            31,
        ),
        penta=standard_penta_2024(),
        dtp=history(
            "dtp",
            [
                date(
                    2025,
                    4,
                    1,
                ),
                date(
                    2027,
                    12,
                    31,
                ),
            ],
        ),
    )

    assert result[
        "dtp_r1_history_valid"
    ] is True

    assert result[
        "dtp_r2_history_valid"
    ] is False

    assert (
        "dtp_r2_before_exact_4_years"
        in result[
            "invalid_history_reasons"
        ]
    )


def test_r1_to_r2_under_six_calendar_months_fails_closed():
    result = normalize(
        dob=date(
            2024,
            1,
            1,
        ),
        assessment=date(
            2028,
            6,
            30,
        ),
        penta=standard_penta_2024(),
        dtp=history(
            "dtp",
            [
                date(
                    2028,
                    1,
                    1,
                ),
                date(
                    2028,
                    6,
                    30,
                ),
            ],
        ),
    )

    assert result[
        "dtp_r1_history_valid"
    ] is True

    assert result[
        "dtp_r2_history_valid"
    ] is False

    assert (
        "r1_to_r2_under_6_calendar_months"
        in result[
            "invalid_history_reasons"
        ]
    )


def test_exact_r1_plus_six_months_can_validate_r2():
    result = normalize(
        dob=date(
            2024,
            1,
            1,
        ),
        assessment=date(
            2028,
            7,
            1,
        ),
        penta=standard_penta_2024(),
        dtp=history(
            "dtp",
            [
                date(
                    2028,
                    1,
                    1,
                ),
                date(
                    2028,
                    7,
                    1,
                ),
            ],
        ),
    )

    assert result[
        "dtp_r1_history_valid"
    ] is True

    assert result[
        "dtp_r2_history_valid"
    ] is True


def test_dtp_at_exact_age7_fails_closed():
    result = normalize(
        dob=date(
            2020,
            1,
            1,
        ),
        assessment=date(
            2027,
            1,
            1,
        ),
        penta=history(
            "pentavalent",
            [
                date(
                    2020,
                    3,
                    1,
                ),
                date(
                    2020,
                    5,
                    1,
                ),
                date(
                    2020,
                    7,
                    1,
                ),
            ],
        ),
        dtp=history(
            "dtp",
            [
                date(
                    2027,
                    1,
                    1,
                ),
            ],
        ),
    )

    assert result[
        "dtp_r1_history_valid"
    ] is False

    assert result[
        "safe_for_routine_evaluation"
    ] is False

    assert (
        "dtp_at_or_after_exact_7_years"
        in result[
            "invalid_history_reasons"
        ]
    )


def test_late_r1_can_close_r2_opportunity():
    result = normalize(
        dob=date(
            2020,
            1,
            1,
        ),
        assessment=date(
            2026,
            8,
            1,
        ),
        penta=history(
            "pentavalent",
            [
                date(
                    2020,
                    3,
                    1,
                ),
                date(
                    2020,
                    5,
                    1,
                ),
                date(
                    2020,
                    7,
                    1,
                ),
            ],
        ),
        dtp=history(
            "dtp",
            [
                date(
                    2026,
                    8,
                    1,
                ),
            ],
        ),
    )

    assert result[
        "dtp_r1_history_valid"
    ] is True

    assert result[
        "r2_earliest_date"
    ] == date(
        2027,
        2,
        1,
    )

    assert result[
        "late_r1_closes_r2_before_age7"
    ] is True

    assert result[
        "safe_for_routine_evaluation"
    ] is True


def test_age6_r1_can_still_leave_r2_opportunity():
    result = normalize(
        dob=date(
            2020,
            1,
            1,
        ),
        assessment=date(
            2026,
            6,
            1,
        ),
        penta=history(
            "pentavalent",
            [
                date(
                    2020,
                    3,
                    1,
                ),
                date(
                    2020,
                    5,
                    1,
                ),
                date(
                    2020,
                    7,
                    1,
                ),
            ],
        ),
        dtp=history(
            "dtp",
            [
                date(
                    2026,
                    6,
                    1,
                ),
            ],
        ),
    )

    assert result[
        "dtp_r1_history_valid"
    ] is True

    assert result[
        "r2_earliest_date"
    ] == date(
        2026,
        12,
        1,
    )

    assert result[
        "late_r1_closes_r2_before_age7"
    ] is False


def test_partial_history_fails_closed():
    result = normalize(
        dob=date(
            2024,
            1,
            1,
        ),
        assessment=date(
            2025,
            4,
            1,
        ),
        penta=history(
            "pentavalent",
            state="partial_record",
            undated=1,
        ),
    )

    assert result[
        "source_history_incomplete"
    ] is True

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_30_to_59_day_penta_interval_needs_historical_exception_evidence():
    result = normalize(
        dob=date(
            2024,
            1,
            1,
        ),
        assessment=date(
            2025,
            4,
            1,
        ),
        penta=history(
            "pentavalent",
            [
                date(
                    2024,
                    3,
                    1,
                ),
                date(
                    2024,
                    4,
                    15,
                ),
                date(
                    2024,
                    7,
                    1,
                ),
            ],
        ),
    )

    assert result[
        "unresolved_pentavalent_exception_evidence"
    ] is True

    assert result[
        "pentavalent_basic_series_complete"
    ] is False

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_early_penta_d1_without_exception_evidence_fails_closed():
    result = normalize(
        dob=date(
            2024,
            1,
            1,
        ),
        assessment=date(
            2025,
            4,
            1,
        ),
        penta=history(
            "pentavalent",
            [
                date(
                    2024,
                    2,
                    16,
                ),
                date(
                    2024,
                    4,
                    16,
                ),
                date(
                    2024,
                    6,
                    16,
                ),
            ],
        ),
    )

    assert result[
        "unresolved_pentavalent_exception_evidence"
    ] is True

    assert result[
        "pentavalent_basic_series_complete"
    ] is False


def test_excess_pentavalent_evidence_fails_closed():
    result = normalize(
        dob=date(
            2024,
            1,
            1,
        ),
        assessment=date(
            2025,
            4,
            1,
        ),
        penta=history(
            "pentavalent",
            [
                date(
                    2024,
                    3,
                    1,
                ),
                date(
                    2024,
                    5,
                    1,
                ),
                date(
                    2024,
                    7,
                    1,
                ),
                date(
                    2024,
                    9,
                    1,
                ),
            ],
        ),
    )

    assert result[
        "excessive_pentavalent_evidence"
    ] is True

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_excess_dtp_evidence_fails_closed():
    result = normalize(
        dob=date(
            2020,
            1,
            1,
        ),
        assessment=date(
            2026,
            1,
            1,
        ),
        penta=history(
            "pentavalent",
            [
                date(
                    2020,
                    3,
                    1,
                ),
                date(
                    2020,
                    5,
                    1,
                ),
                date(
                    2020,
                    7,
                    1,
                ),
            ],
        ),
        dtp=history(
            "dtp",
            [
                date(
                    2021,
                    4,
                    1,
                ),
                date(
                    2024,
                    1,
                    1,
                ),
                date(
                    2025,
                    1,
                    1,
                ),
            ],
        ),
    )

    assert result[
        "excessive_dtp_evidence"
    ] is True

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_wrong_history_family_is_rejected():
    with pytest.raises(
        ValueError,
        match="expected vaccine_key pentavalent",
    ):
        normalize(
            dob=date(
                2024,
                1,
                1,
            ),
            assessment=date(
                2025,
                4,
                1,
            ),
            penta=history(
                "dtp"
            ),
        )


def test_unsupported_product_identity_fails_closed():
    result = normalize(
        dob=date(
            2024,
            1,
            1,
        ),
        assessment=date(
            2025,
            4,
            1,
        ),
        penta=history(
            "pentavalent",
            [
                date(
                    2024,
                    3,
                    1,
                ),
            ],
            product_key="dtp",
        ),
    )

    assert (
        "dtp"
        in result[
            "unsupported_product_keys"
        ]
    )

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_same_day_conflicting_history_fails_closed():
    result = normalize(
        dob=date(
            2024,
            1,
            1,
        ),
        assessment=date(
            2025,
            4,
            1,
        ),
        penta=history(
            "pentavalent",
            [
                date(
                    2024,
                    3,
                    1,
                ),
            ],
        ),
        dtp=history(
            "dtp",
            [
                date(
                    2024,
                    3,
                    1,
                ),
            ],
        ),
    )

    assert result[
        "chronology_ambiguous"
    ] is True

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_normalizer_never_assigns_context_or_due_decision():
    result = normalize(
        dob=date(
            2024,
            1,
            1,
        ),
        assessment=date(
            2025,
            4,
            1,
        ),
        penta=standard_penta_2024(),
    )

    assert result[
        "aggregate_toxoid_history_defines_dtp_completion"
    ] is False

    assert result[
        "normalizer_assigns_due_decision"
    ] is False

    assert result[
        "special_condition_inferred"
    ] is False

    assert result[
        "crie_eligibility_inferred"
    ] is False

    assert result[
        "outbreak_contact_context_inferred"
    ] is False

    assert result[
        "pentavalent_booster_substitution_inferred"
    ] is False

    assert result[
        "future_dt_schedule_inferred"
    ] is False

    assert result[
        "synthetic_score_applied"
    ] is False
