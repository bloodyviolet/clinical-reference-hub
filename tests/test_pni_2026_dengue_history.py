from datetime import date, timedelta

import pytest

import schemas

from clinical_tools.pni_history import (
    DENGUE_PRODUCT_BUTANTAN,
    DENGUE_PRODUCT_SANOFI_LEGACY,
    DENGUE_PRODUCT_TAKEDA,
    DENGUE_SUPPORTED_PRODUCTS,
    DENGUE_TAKEDA_HISTORY_MODEL_ID,
    normalize_dengue_takeda_history,
)


def history(
    events=None,
    *,
    state=None,
    undated=0,
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

    return schemas.PniVaccineHistory(
        vaccine_key="dengue",
        history_state=state,
        doses=[
            schemas.PniDoseRecord(
                administration_date=event_date,
                product_key=product,
                documentation_source="official_registry",
            )
            for event_date, product
            in events
        ],
        reported_prior_doses_without_exact_dates=undated,
    )


def normalize(
    *,
    dob,
    assessment,
    events=None,
    state=None,
    undated=0,
    scope="complete",
):
    return normalize_dengue_takeda_history(
        assessment_date=assessment,
        date_of_birth=dob,
        history=history(
            events,
            state=state,
            undated=undated,
        ),
        history_scope=scope,
    )


def test_canonical_product_keys():
    assert DENGUE_PRODUCT_TAKEDA == "dengue_takeda"
    assert DENGUE_PRODUCT_BUTANTAN == "dengue_butantan"

    assert (
        DENGUE_PRODUCT_SANOFI_LEGACY
        == "dengue_sanofi_legacy"
    )

    assert DENGUE_SUPPORTED_PRODUCTS == frozenset({
        "dengue_takeda",
        "dengue_butantan",
        "dengue_sanofi_legacy",
    })


def test_documented_zero_history_is_safe():
    result = normalize(
        dob=date(
            2014,
            1,
            1,
        ),
        assessment=date(
            2026,
            1,
            1,
        ),
    )

    assert (
        result[
            "model_id"
        ]
        == DENGUE_TAKEDA_HISTORY_MODEL_ID
    )

    assert result[
        "lifetime_dengue_vaccine_event_count"
    ] == 0

    assert result[
        "valid_takeda_dose_count"
    ] == 0

    assert result[
        "position20_series_complete"
    ] is False

    assert result[
        "safe_for_routine_evaluation"
    ] is True


def test_takeda_D1_counts_as_product_series_D1():
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

    result = normalize(
        dob=dob,
        assessment=d1,
        events=[
            (
                d1,
                DENGUE_PRODUCT_TAKEDA,
            ),
        ],
    )

    assert result[
        "valid_takeda_d1_date"
    ] == d1

    assert result[
        "valid_takeda_dose_count"
    ] == 1

    assert result[
        "next_corrective_takeda_date"
    ] == (
        d1
        + timedelta(
            days=90,
        )
    )

    assert result[
        "safe_for_routine_evaluation"
    ] is True


def test_exact_90_day_takeda_D2_completes_series():
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

    result = normalize(
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
    )

    assert result[
        "valid_takeda_dose_count"
    ] == 2

    assert result[
        "valid_takeda_d2_date"
    ] == d2

    assert result[
        "takeda_series_complete"
    ] is True

    assert result[
        "position20_series_complete"
    ] is True


def test_day89_is_early_and_does_not_count_D2():
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

    early = (
        d1
        + timedelta(
            days=89,
        )
    )

    result = normalize(
        dob=dob,
        assessment=early,
        events=[
            (
                d1,
                DENGUE_PRODUCT_TAKEDA,
            ),
            (
                early,
                DENGUE_PRODUCT_TAKEDA,
            ),
        ],
    )

    assert result[
        "valid_takeda_dose_count"
    ] == 1

    assert result[
        "early_takeda_d2_event_count"
    ] == 1

    assert result[
        "takeda_series_complete"
    ] is False

    assert result[
        "safe_for_routine_evaluation"
    ] is True


def test_calendar_month_clamping_is_not_used():
    dob = date(
        2014,
        1,
        31,
    )

    d1 = date(
        2026,
        1,
        31,
    )

    april30 = date(
        2026,
        4,
        30,
    )

    result = normalize(
        dob=dob,
        assessment=april30,
        events=[
            (
                d1,
                DENGUE_PRODUCT_TAKEDA,
            ),
            (
                april30,
                DENGUE_PRODUCT_TAKEDA,
            ),
        ],
    )

    assert result[
        "valid_takeda_dose_count"
    ] == 1

    assert result[
        "early_takeda_d2_event_count"
    ] == 1

    assert result[
        "calendar_month_interval_used"
    ] is False

    assert result[
        "next_corrective_takeda_date"
    ] == date(
        2026,
        5,
        30,
    )


def test_early_D2_corrective_threshold_uses_both_floors():
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

    early = date(
        2026,
        3,
        15,
    )

    expected = date(
        2026,
        4,
        14,
    )

    result = normalize(
        dob=dob,
        assessment=early,
        events=[
            (
                d1,
                DENGUE_PRODUCT_TAKEDA,
            ),
            (
                early,
                DENGUE_PRODUCT_TAKEDA,
            ),
        ],
    )

    assert result[
        "next_corrective_takeda_date"
    ] == expected


def test_corrective_takeda_event_can_complete_after_early_extra():
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

    early = date(
        2026,
        3,
        15,
    )

    corrective = date(
        2026,
        4,
        14,
    )

    result = normalize(
        dob=dob,
        assessment=corrective,
        events=[
            (
                d1,
                DENGUE_PRODUCT_TAKEDA,
            ),
            (
                early,
                DENGUE_PRODUCT_TAKEDA,
            ),
            (
                corrective,
                DENGUE_PRODUCT_TAKEDA,
            ),
        ],
    )

    assert result[
        "valid_takeda_dose_count"
    ] == 2

    assert result[
        "early_takeda_d2_event_count"
    ] == 1

    assert result[
        "valid_takeda_d2_date"
    ] == corrective

    assert result[
        "takeda_series_complete"
    ] is True


def test_valid_D1_before_age10_is_preserved_as_series_history():
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
        2026,
        1,
        1,
    )

    result = normalize(
        dob=dob,
        assessment=assessment,
        events=[
            (
                d1,
                DENGUE_PRODUCT_TAKEDA,
            ),
        ],
    )

    assert result[
        "valid_takeda_d1_date"
    ] == d1

    assert result[
        "valid_takeda_dose_count"
    ] == 1

    assert result[
        "events"
    ][0][
        "pni_takeda_initiation_age_event"
    ] is False

    assert (
        result[
            "events"
        ][0][
            "product_series_role"
        ]
        == "takeda_valid_D1_before_pni_target_age"
    )

    assert result[
        "safe_for_routine_evaluation"
    ] is True


def test_valid_D1_before15_can_complete_after15():
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

    d2 = (
        d1
        + timedelta(
            days=90,
        )
    )

    assert d1 < date(
        2026,
        1,
        1,
    )

    assert d2 > date(
        2026,
        1,
        1,
    )

    result = normalize(
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
    )

    assert result[
        "takeda_series_complete"
    ] is True

    assert result[
        "valid_takeda_d2_date"
    ] == d2


def test_first_takeda_event_at_or_after15_fails_closed():
    dob = date(
        2011,
        1,
        1,
    )

    event = date(
        2026,
        1,
        1,
    )

    result = normalize(
        dob=dob,
        assessment=event,
        events=[
            (
                event,
                DENGUE_PRODUCT_TAKEDA,
            ),
        ],
    )

    assert result[
        "valid_takeda_dose_count"
    ] == 0

    assert result[
        "safe_for_routine_evaluation"
    ] is False

    assert (
        "first_takeda_event_at_or_after_exact15y"
        in result[
            "invalid_history_reasons"
        ]
    )


def test_takeda_event_before_age4_fails_closed():
    dob = date(
        2020,
        1,
        1,
    )

    event = date(
        2023,
        12,
        31,
    )

    result = normalize(
        dob=dob,
        assessment=event,
        events=[
            (
                event,
                DENGUE_PRODUCT_TAKEDA,
            ),
        ],
    )

    assert result[
        "safe_for_routine_evaluation"
    ] is False

    assert (
        "takeda_event_outside_supported_label_age"
        in result[
            "invalid_history_reasons"
        ]
    )


def test_takeda_D1_then_butantan_day30_closes_by_error_management():
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

    butantan = (
        d1
        + timedelta(
            days=30,
        )
    )

    result = normalize(
        dob=dob,
        assessment=butantan,
        events=[
            (
                d1,
                DENGUE_PRODUCT_TAKEDA,
            ),
            (
                butantan,
                DENGUE_PRODUCT_BUTANTAN,
            ),
        ],
    )

    assert result[
        "valid_takeda_dose_count"
    ] == 1

    assert result[
        "takeda_series_complete"
    ] is False

    assert result[
        "cross_product_error_completion"
    ] is True

    assert result[
        "error_managed_series_complete"
    ] is True

    assert result[
        "position20_series_complete"
    ] is True

    assert result[
        "cross_product_completion_date"
    ] == butantan

    assert result[
        "safe_for_routine_evaluation"
    ] is True


def test_takeda_D1_then_butantan_day29_fails_closed():
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

    butantan = (
        d1
        + timedelta(
            days=29,
        )
    )

    result = normalize(
        dob=dob,
        assessment=butantan,
        events=[
            (
                d1,
                DENGUE_PRODUCT_TAKEDA,
            ),
            (
                butantan,
                DENGUE_PRODUCT_BUTANTAN,
            ),
        ],
    )

    assert result[
        "cross_product_error_completion"
    ] is False

    assert result[
        "cross_product_ambiguous"
    ] is True

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_butantan_without_prior_takeda_D1_fails_closed_for_position20():
    dob = date(
        2014,
        1,
        1,
    )

    event = date(
        2026,
        1,
        1,
    )

    result = normalize(
        dob=dob,
        assessment=event,
        events=[
            (
                event,
                DENGUE_PRODUCT_BUTANTAN,
            ),
        ],
    )

    assert result[
        "cross_product_ambiguous"
    ] is True

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_butantan_before_takeda_fails_closed():
    dob = date(
        2014,
        1,
        1,
    )

    butantan = date(
        2026,
        1,
        1,
    )

    takeda = date(
        2026,
        2,
        15,
    )

    result = normalize(
        dob=dob,
        assessment=takeda,
        events=[
            (
                butantan,
                DENGUE_PRODUCT_BUTANTAN,
            ),
            (
                takeda,
                DENGUE_PRODUCT_TAKEDA,
            ),
        ],
    )

    assert result[
        "cross_product_ambiguous"
    ] is True

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_sanofi_history_is_preserved_and_fails_closed():
    dob = date(
        2014,
        1,
        1,
    )

    event = date(
        2025,
        1,
        1,
    )

    result = normalize(
        dob=dob,
        assessment=event,
        events=[
            (
                event,
                DENGUE_PRODUCT_SANOFI_LEGACY,
            ),
        ],
    )

    assert result[
        "sanofi_history_present"
    ] is True

    assert len(
        result[
            "sanofi_legacy_events"
        ]
    ) == 1

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_same_day_multiple_dengue_events_fail_closed():
    dob = date(
        2014,
        1,
        1,
    )

    event = date(
        2026,
        1,
        1,
    )

    result = normalize(
        dob=dob,
        assessment=event,
        events=[
            (
                event,
                DENGUE_PRODUCT_TAKEDA,
            ),
            (
                event,
                DENGUE_PRODUCT_BUTANTAN,
            ),
        ],
    )

    assert result[
        "same_day_product_conflict"
    ] is True

    assert result[
        "same_day_ambiguous_dates"
    ] == [
        event,
    ]

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_unsupported_product_identity_fails_closed():
    dob = date(
        2014,
        1,
        1,
    )

    event = date(
        2026,
        1,
        1,
    )

    result = normalize(
        dob=dob,
        assessment=event,
        events=[
            (
                event,
                "dengue_unknown_product",
            ),
        ],
    )

    assert (
        "dengue_unknown_product"
        in result[
            "unsupported_product_keys"
        ]
    )

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_partial_unknown_and_undated_history_fail_closed():
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

    partial = normalize(
        dob=dob,
        assessment=assessment,
        state="partial_record",
        undated=1,
        scope="partial",
    )

    unknown = normalize(
        dob=dob,
        assessment=assessment,
        state="unknown",
        scope="unknown",
    )

    for result in (
        partial,
        unknown,
    ):
        assert result[
            "source_history_incomplete"
        ] is True

        assert result[
            "safe_for_routine_evaluation"
        ] is False


def test_future_event_is_rejected():
    dob = date(
        2014,
        1,
        1,
    )

    with pytest.raises(
        ValueError,
        match="cannot follow assessment_date",
    ):
        normalize(
            dob=dob,
            assessment=date(
                2026,
                1,
                1,
            ),
            events=[
                (
                    date(
                        2026,
                        1,
                        2,
                    ),
                    DENGUE_PRODUCT_TAKEDA,
                ),
            ],
        )


def test_normalizer_does_not_infer_disease_or_clinical_context():
    result = normalize(
        dob=date(
            2014,
            1,
            1,
        ),
        assessment=date(
            2026,
            1,
            1,
        ),
    )

    assert result[
        "generic_cross_manufacturer_counting_applied"
    ] is False

    assert result[
        "dengue_disease_history_inferred"
    ] is False

    assert result[
        "pregnancy_inferred"
    ] is False

    assert result[
        "breastfeeding_inferred"
    ] is False

    assert result[
        "immune_status_inferred"
    ] is False

    assert result[
        "geographic_eligibility_inferred"
    ] is False

    assert result[
        "normalizer_assigns_due_decision"
    ] is False

    assert result[
        "synthetic_score_applied"
    ] is False
