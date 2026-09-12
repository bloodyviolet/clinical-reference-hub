from datetime import date, timedelta

import pytest

import schemas

from clinical_tools.pni_history import (
    YELLOW_FEVER_PRODUCT_FRACTIONAL_2018,
    YELLOW_FEVER_PRODUCT_STANDARD,
    normalize_yellow_fever_history,
)


STANDARD = YELLOW_FEVER_PRODUCT_STANDARD
FRACTIONAL = YELLOW_FEVER_PRODUCT_FRACTIONAL_2018


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
        vaccine_key="yellow_fever",
        history_state=state,
        doses=[
            schemas.PniDoseRecord(
                administration_date=event_date,
                product_key=product_key,
                documentation_source="official_registry",
            )
            for event_date, product_key
            in events
        ],
        reported_prior_doses_without_exact_dates=undated,
    )


def normalize(
    *,
    assessment,
    dob,
    events=None,
    state=None,
    scope="complete",
    undated=0,
    role_events=None,
):
    return normalize_yellow_fever_history(
        assessment_date=assessment,
        date_of_birth=dob,
        history=history(
            events,
            state=state,
            undated=undated,
        ),
        history_scope=scope,
        registration_role_events=role_events,
    )


def test_documented_zero_history_is_safe():
    result = normalize(
        assessment=date(
            2026,
            1,
            1,
        ),
        dob=date(
            2025,
            1,
            1,
        ),
    )

    assert result[
        "standard_dose_count"
    ] == 0

    assert result[
        "dose_zero_count"
    ] == 0

    assert result[
        "fractional_2018_count"
    ] == 0

    assert result[
        "safe_for_routine_evaluation"
    ] is True


def test_input_order_does_not_define_chronology():
    dob = date(
        2025,
        1,
        1,
    )

    first = date(
        2025,
        10,
        1,
    )

    second = date(
        2025,
        10,
        31,
    )

    result = normalize(
        assessment=second,
        dob=dob,
        events=[
            (
                second,
                STANDARD,
            ),
            (
                first,
                STANDARD,
            ),
        ],
    )

    assert [
        event[
            "administration_date"
        ]
        for event in result[
            "events"
        ]
    ] == [
        first,
        second,
    ]

    assert [
        event[
            "lifetime_chronology_ordinal"
        ]
        for event in result[
            "events"
        ]
    ] == [
        1,
        2,
    ]


def test_day_before_exact_6m_is_retained_but_unsafe():
    dob = date(
        2025,
        1,
        1,
    )

    event_date = date(
        2025,
        6,
        30,
    )

    result = normalize(
        assessment=event_date,
        dob=dob,
        events=[
            (
                event_date,
                STANDARD,
            ),
        ],
    )

    assert result[
        "before_6m_event_count"
    ] == 1

    assert (
        result[
            "events"
        ][
            0
        ][
            "clinical_role"
        ]
        == "before_vfa_minimum_age"
    )

    assert result[
        "standard_dose_count"
    ] == 0

    assert (
        result[
            "safe_for_routine_evaluation"
        ]
        is False
    )


def test_exact_6m_standard_is_dose_zero():
    dob = date(
        2025,
        1,
        1,
    )

    event_date = date(
        2025,
        7,
        1,
    )

    result = normalize(
        assessment=event_date,
        dob=dob,
        events=[
            (
                event_date,
                STANDARD,
            ),
        ],
    )

    assert result[
        "dose_zero_count"
    ] == 1

    assert result[
        "standard_dose_count"
    ] == 0

    assert (
        result[
            "events"
        ][
            0
        ][
            "clinical_role"
        ]
        == "exceptional_dose_zero"
    )


def test_day_before_9m_is_still_dose_zero():
    dob = date(
        2025,
        1,
        1,
    )

    result = normalize(
        assessment=date(
            2025,
            9,
            30,
        ),
        dob=dob,
        events=[
            (
                date(
                    2025,
                    9,
                    30,
                ),
                STANDARD,
            ),
        ],
    )

    assert result[
        "dose_zero_count"
    ] == 1

    assert result[
        "standard_dose_count"
    ] == 0


def test_exact_9m_standard_is_pre5_series_dose():
    dob = date(
        2025,
        1,
        1,
    )

    event_date = date(
        2025,
        10,
        1,
    )

    result = normalize(
        assessment=event_date,
        dob=dob,
        events=[
            (
                event_date,
                STANDARD,
            ),
        ],
    )

    assert result[
        "dose_zero_count"
    ] == 0

    assert result[
        "standard_dose_count"
    ] == 1

    assert result[
        "standard_dose_before5_count"
    ] == 1

    assert (
        result[
            "events"
        ][
            0
        ][
            "clinical_role"
        ]
        == "standard_series_dose_before5"
    )

    assert (
        result[
            "events"
        ][
            0
        ][
            "standard_series_ordinal"
        ]
        == 1
    )


def test_day_before_age5_is_pre5_standard():
    dob = date(
        2021,
        1,
        1,
    )

    event_date = date(
        2025,
        12,
        31,
    )

    result = normalize(
        assessment=event_date,
        dob=dob,
        events=[
            (
                event_date,
                STANDARD,
            ),
        ],
    )

    assert result[
        "standard_dose_before5_count"
    ] == 1

    assert result[
        "standard_dose_at_or_after5_count"
    ] == 0


def test_exact_age5_is_age5plus_standard():
    dob = date(
        2021,
        1,
        1,
    )

    event_date = date(
        2026,
        1,
        1,
    )

    result = normalize(
        assessment=event_date,
        dob=dob,
        events=[
            (
                event_date,
                STANDARD,
            ),
        ],
    )

    assert result[
        "standard_dose_before5_count"
    ] == 0

    assert result[
        "standard_dose_at_or_after5_count"
    ] == 1

    assert (
        result[
            "events"
        ][
            0
        ][
            "clinical_role"
        ]
        == "standard_series_dose_age5_to59"
    )


def test_exact_age60_is_exception_layer_standard():
    dob = date(
        1966,
        1,
        1,
    )

    event_date = date(
        2026,
        1,
        1,
    )

    result = normalize(
        assessment=event_date,
        dob=dob,
        events=[
            (
                event_date,
                STANDARD,
            ),
        ],
    )

    assert result[
        "standard_dose_age60plus_count"
    ] == 1

    assert (
        result[
            "events"
        ][
            0
        ][
            "clinical_role"
        ]
        == "standard_dose_age60plus_exception_layer"
    )


def test_dose_zero_plus_29_day_standard_invalid():
    dob = date(
        2025,
        1,
        1,
    )

    d0 = date(
        2025,
        9,
        15,
    )

    standard = (
        d0
        + timedelta(
            days=29,
        )
    )

    result = normalize(
        assessment=standard,
        dob=dob,
        events=[
            (
                d0,
                STANDARD,
            ),
            (
                standard,
                STANDARD,
            ),
        ],
    )

    assert result[
        "dose_zero_count"
    ] == 1

    assert result[
        "standard_dose_count"
    ] == 1

    assert result[
        "intervals_valid"
    ] is False

    assert (
        result[
            "safe_for_routine_evaluation"
        ]
        is False
    )


def test_dose_zero_plus_30_day_standard_valid():
    dob = date(
        2025,
        1,
        1,
    )

    d0 = date(
        2025,
        9,
        15,
    )

    standard = (
        d0
        + timedelta(
            days=30,
        )
    )

    result = normalize(
        assessment=standard,
        dob=dob,
        events=[
            (
                d0,
                STANDARD,
            ),
            (
                standard,
                STANDARD,
            ),
        ],
    )

    assert result[
        "intervals_valid"
    ] is True

    assert result[
        "internal_interval_checks"
    ][
        0
    ][
        "actual_days"
    ] == 30

    assert (
        result[
            "internal_interval_checks"
        ][
            0
        ][
            "interval_type"
        ]
        == "dose_zero_to_standard"
    )


def test_standard_plus_29_day_standard_invalid():
    dob = date(
        2020,
        1,
        1,
    )

    first = date(
        2021,
        1,
        1,
    )

    second = (
        first
        + timedelta(
            days=29,
        )
    )

    result = normalize(
        assessment=second,
        dob=dob,
        events=[
            (
                first,
                STANDARD,
            ),
            (
                second,
                STANDARD,
            ),
        ],
    )

    assert result[
        "intervals_valid"
    ] is False

    assert (
        result[
            "internal_interval_checks"
        ][
            0
        ][
            "interval_type"
        ]
        == "standard_to_standard"
    )


def test_standard_plus_30_day_standard_valid():
    dob = date(
        2020,
        1,
        1,
    )

    first = date(
        2021,
        1,
        1,
    )

    second = (
        first
        + timedelta(
            days=30,
        )
    )

    result = normalize(
        assessment=second,
        dob=dob,
        events=[
            (
                first,
                STANDARD,
            ),
            (
                second,
                STANDARD,
            ),
        ],
    )

    assert result[
        "intervals_valid"
    ] is True


def test_fractional_only_requires_regularization():
    dob = date(
        2010,
        1,
        1,
    )

    event_date = date(
        2018,
        2,
        1,
    )

    result = normalize(
        assessment=date(
            2026,
            1,
            1,
        ),
        dob=dob,
        events=[
            (
                event_date,
                FRACTIONAL,
            ),
        ],
    )

    assert result[
        "fractional_2018_count"
    ] == 1

    assert result[
        "standard_dose_count"
    ] == 0

    assert (
        result[
            "fractional_regularization_required"
        ]
        is True
    )

    assert (
        result[
            "events"
        ][
            0
        ][
            "clinical_role"
        ]
        == "fractional_2018_nonstandard"
    )


def test_fractional_then_standard_resolves_regularization():
    dob = date(
        2010,
        1,
        1,
    )

    fractional = date(
        2018,
        2,
        1,
    )

    standard = date(
        2026,
        1,
        1,
    )

    result = normalize(
        assessment=standard,
        dob=dob,
        events=[
            (
                fractional,
                FRACTIONAL,
            ),
            (
                standard,
                STANDARD,
            ),
        ],
    )

    assert (
        result[
            "fractional_regularization_required"
        ]
        is False
    )

    assert (
        result[
            "standard_after_latest_fractional_count"
        ]
        == 1
    )

    standard_event = result[
        "events"
    ][
        1
    ]

    assert standard_event[
        "fractional_regularization_event"
    ] is True

    assert (
        standard_event[
            "clinical_role"
        ]
        == "standard_series_dose_age5_to59"
    )


def test_standard_before_fractional_does_not_resolve_overlay():
    dob = date(
        2010,
        1,
        1,
    )

    result = normalize(
        assessment=date(
            2026,
            1,
            1,
        ),
        dob=dob,
        events=[
            (
                date(
                    2017,
                    1,
                    1,
                ),
                STANDARD,
            ),
            (
                date(
                    2018,
                    2,
                    1,
                ),
                FRACTIONAL,
            ),
        ],
    )

    assert (
        result[
            "fractional_regularization_required"
        ]
        is True
    )

    assert (
        result[
            "standard_after_latest_fractional_count"
        ]
        == 0
    )


def test_fractional_to_later_standard_has_no_invented_30_day_gate():
    dob = date(
        2010,
        1,
        1,
    )

    result = normalize(
        assessment=date(
            2018,
            2,
            15,
        ),
        dob=dob,
        events=[
            (
                date(
                    2018,
                    2,
                    1,
                ),
                FRACTIONAL,
            ),
            (
                date(
                    2018,
                    2,
                    15,
                ),
                STANDARD,
            ),
        ],
    )

    assert result[
        "intervals_valid"
    ] is True

    assert result[
        "internal_interval_checks"
    ] == []


def test_fractional_product_outside_2018_rejected():
    with pytest.raises(
        ValueError,
        match="must have a 2018 administration date",
    ):
        normalize(
            assessment=date(
                2019,
                2,
                1,
            ),
            dob=date(
                2010,
                1,
                1,
            ),
            events=[
                (
                    date(
                        2019,
                        2,
                        1,
                    ),
                    FRACTIONAL,
                ),
            ],
        )


def test_source_ref_registration_does_not_define_clinical_booster():
    dob = date(
        2010,
        1,
        1,
    )

    fractional = date(
        2018,
        2,
        1,
    )

    standard = date(
        2026,
        1,
        1,
    )

    result = normalize(
        assessment=standard,
        dob=dob,
        events=[
            (
                fractional,
                FRACTIONAL,
            ),
            (
                standard,
                STANDARD,
            ),
        ],
        role_events=[
            {
                "administration_date":
                    standard,

                "source_registration_role":
                    "REF",
            },
        ],
    )

    standard_event = result[
        "events"
    ][
        1
    ]

    assert (
        standard_event[
            "source_registration_role"
        ]
        == "REF"
    )

    assert (
        standard_event[
            "clinical_role"
        ]
        == "standard_series_dose_age5_to59"
    )

    assert standard_event[
        "fractional_regularization_event"
    ] is True

    assert (
        result[
            "registration_role_defines_clinical_role"
        ]
        is False
    )


def test_generic_family_key_as_dose_product_fails_closed():
    result = normalize(
        assessment=date(
            2026,
            1,
            1,
        ),
        dob=date(
            2020,
            1,
            1,
        ),
        events=[
            (
                date(
                    2025,
                    1,
                    1,
                ),
                "yellow_fever",
            ),
        ],
    )

    assert result[
        "unsupported_product_keys"
    ] == [
        "yellow_fever",
    ]

    assert (
        result[
            "safe_for_routine_evaluation"
        ]
        is False
    )


def test_unknown_product_fails_closed():
    result = normalize(
        assessment=date(
            2026,
            1,
            1,
        ),
        dob=date(
            2020,
            1,
            1,
        ),
        events=[
            (
                date(
                    2025,
                    1,
                    1,
                ),
                "yellow_fever_unknown",
            ),
        ],
    )

    assert result[
        "unsupported_product_keys"
    ] == [
        "yellow_fever_unknown",
    ]

    assert (
        result[
            "safe_for_routine_evaluation"
        ]
        is False
    )


@pytest.mark.parametrize(
    "scope",
    [
        "partial",
        "unknown",
    ],
)
def test_incomplete_history_scope_fails_closed(
    scope,
):
    result = normalize(
        assessment=date(
            2026,
            1,
            1,
        ),
        dob=date(
            2020,
            1,
            1,
        ),
        scope=scope,
    )

    assert result[
        "source_history_incomplete"
    ] is True

    assert (
        result[
            "safe_for_routine_evaluation"
        ]
        is False
    )


def test_unknown_history_state_fails_closed():
    result = normalize(
        assessment=date(
            2026,
            1,
            1,
        ),
        dob=date(
            2020,
            1,
            1,
        ),
        state="unknown",
    )

    assert result[
        "source_history_incomplete"
    ] is True

    assert (
        result[
            "safe_for_routine_evaluation"
        ]
        is False
    )


def test_undated_partial_history_fails_closed():
    result = normalize(
        assessment=date(
            2026,
            1,
            1,
        ),
        dob=date(
            2020,
            1,
            1,
        ),
        state="partial_record",
        undated=1,
    )

    assert result[
        "reported_undated_event_count"
    ] == 1

    assert result[
        "source_history_incomplete"
    ] is True

    assert (
        result[
            "safe_for_routine_evaluation"
        ]
        is False
    )


def test_future_event_rejected():
    assessment = date(
        2026,
        1,
        1,
    )

    with pytest.raises(
        ValueError,
        match="cannot follow assessment_date",
    ):
        normalize(
            assessment=assessment,
            dob=date(
                2020,
                1,
                1,
            ),
            events=[
                (
                    assessment
                    + timedelta(
                        days=1,
                    ),
                    STANDARD,
                ),
            ],
        )


def test_pre_birth_event_rejected():
    with pytest.raises(
        ValueError,
        match="cannot precede date_of_birth",
    ):
        normalize(
            assessment=date(
                2026,
                1,
                1,
            ),
            dob=date(
                2020,
                1,
                1,
            ),
            events=[
                (
                    date(
                        2019,
                        12,
                        31,
                    ),
                    STANDARD,
                ),
            ],
        )


def test_same_day_duplicate_rejected():
    event_date = date(
        2025,
        1,
        1,
    )

    with pytest.raises(
        ValueError,
        match="same-day yellow-fever lifetime event ambiguity",
    ):
        normalize(
            assessment=date(
                2026,
                1,
                1,
            ),
            dob=date(
                2020,
                1,
                1,
            ),
            events=[
                (
                    event_date,
                    STANDARD,
                ),
                (
                    event_date,
                    STANDARD,
                ),
            ],
        )


def test_registration_metadata_must_reconcile():
    event_date = date(
        2025,
        1,
        1,
    )

    with pytest.raises(
        ValueError,
        match="must reconcile",
    ):
        normalize(
            assessment=date(
                2026,
                1,
                1,
            ),
            dob=date(
                2020,
                1,
                1,
            ),
            events=[
                (
                    event_date,
                    STANDARD,
                ),
            ],
            role_events=[
                {
                    "administration_date":
                        date(
                            2025,
                            1,
                            2,
                        ),

                    "source_registration_role":
                        "D",
                },
            ],
        )


def test_duplicate_registration_metadata_date_rejected():
    event_date = date(
        2025,
        1,
        1,
    )

    with pytest.raises(
        ValueError,
        match="duplicate yellow-fever registration metadata date",
    ):
        normalize(
            assessment=date(
                2026,
                1,
                1,
            ),
            dob=date(
                2020,
                1,
                1,
            ),
            events=[
                (
                    event_date,
                    STANDARD,
                ),
            ],
            role_events=[
                {
                    "administration_date":
                        event_date,

                    "source_registration_role":
                        "D",
                },
                {
                    "administration_date":
                        event_date,

                    "source_registration_role":
                        "REF",
                },
            ],
        )


def test_three_standard_doses_fail_closed_for_automatic_routine_use():
    dob = date(
        2020,
        1,
        1,
    )

    first = date(
        2021,
        1,
        1,
    )

    second = date(
        2022,
        1,
        1,
    )

    third = date(
        2023,
        1,
        1,
    )

    result = normalize(
        assessment=third,
        dob=dob,
        events=[
            (
                first,
                STANDARD,
            ),
            (
                second,
                STANDARD,
            ),
            (
                third,
                STANDARD,
            ),
        ],
    )

    assert (
        result[
            "excessive_standard_dose_evidence"
        ]
        is True
    )

    assert (
        result[
            "safe_for_routine_evaluation"
        ]
        is False
    )


def test_two_dose_zero_events_fail_closed():
    dob = date(
        2025,
        1,
        1,
    )

    result = normalize(
        assessment=date(
            2025,
            9,
            15,
        ),
        dob=dob,
        events=[
            (
                date(
                    2025,
                    7,
                    1,
                ),
                STANDARD,
            ),
            (
                date(
                    2025,
                    9,
                    15,
                ),
                STANDARD,
            ),
        ],
    )

    assert result[
        "dose_zero_count"
    ] == 2

    assert (
        result[
            "excessive_dose_zero_evidence"
        ]
        is True
    )

    assert (
        result[
            "safe_for_routine_evaluation"
        ]
        is False
    )


def test_normalizer_never_assigns_due_or_context():
    result = normalize(
        assessment=date(
            2026,
            1,
            1,
        ),
        dob=date(
            2020,
            1,
            1,
        ),
    )

    assert (
        result[
            "normalizer_assigns_due_decision"
        ]
        is False
    )

    assert (
        result[
            "epidemiologic_context_inferred"
        ]
        is False
    )

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


def test_dose_zero_after_fractional_does_not_resolve_regularization():
    dob = date(
        2018,
        1,
        1,
    )

    fractional = date(
        2018,
        7,
        1,
    )

    dose_zero = date(
        2018,
        8,
        1,
    )

    result = normalize(
        assessment=dose_zero,
        dob=dob,
        events=[
            (
                fractional,
                FRACTIONAL,
            ),
            (
                dose_zero,
                STANDARD,
            ),
        ],
    )

    assert result[
        "dose_zero_count"
    ] == 1

    assert result[
        "standard_dose_count"
    ] == 0

    assert (
        result[
            "standard_after_latest_fractional_count"
        ]
        == 0
    )

    assert (
        result[
            "fractional_regularization_required"
        ]
        is True
    )

    assert (
        result[
            "events"
        ][
            1
        ][
            "fractional_regularization_event"
        ]
        is False
    )


def test_two_standard_before_fractional_plus_regularization_is_safe():
    dob = date(
        2010,
        1,
        1,
    )

    first = date(
        2011,
        1,
        1,
    )

    second = date(
        2012,
        1,
        1,
    )

    fractional = date(
        2018,
        2,
        1,
    )

    regularization = date(
        2026,
        1,
        1,
    )

    result = normalize(
        assessment=regularization,
        dob=dob,
        events=[
            (
                first,
                STANDARD,
            ),
            (
                second,
                STANDARD,
            ),
            (
                fractional,
                FRACTIONAL,
            ),
            (
                regularization,
                STANDARD,
            ),
        ],
        role_events=[
            {
                "administration_date":
                    regularization,

                "source_registration_role":
                    "REF",
            },
        ],
    )

    assert result[
        "standard_dose_count"
    ] == 3

    assert (
        result[
            "standard_before_latest_fractional_count"
        ]
        == 2
    )

    assert (
        result[
            "standard_after_latest_fractional_count"
        ]
        == 1
    )

    assert (
        result[
            "fractional_regularization_required"
        ]
        is False
    )

    assert (
        result[
            "fractional_regularization_third_standard_allowed"
        ]
        is True
    )

    assert (
        result[
            "excessive_standard_dose_evidence"
        ]
        is False
    )

    assert (
        result[
            "safe_for_routine_evaluation"
        ]
        is True
    )

    assert (
        result[
            "events"
        ][
            3
        ][
            "source_registration_role"
        ]
        == "REF"
    )

    assert (
        result[
            "events"
        ][
            3
        ][
            "fractional_regularization_event"
        ]
        is True
    )

    assert (
        result[
            "events"
        ][
            3
        ][
            "clinical_role"
        ]
        == "standard_series_dose_age5_to59"
    )


def test_three_standard_without_fractional_still_fails_closed():
    dob = date(
        2020,
        1,
        1,
    )

    result = normalize(
        assessment=date(
            2023,
            1,
            1,
        ),
        dob=dob,
        events=[
            (
                date(
                    2021,
                    1,
                    1,
                ),
                STANDARD,
            ),
            (
                date(
                    2022,
                    1,
                    1,
                ),
                STANDARD,
            ),
            (
                date(
                    2023,
                    1,
                    1,
                ),
                STANDARD,
            ),
        ],
    )

    assert (
        result[
            "fractional_regularization_third_standard_allowed"
        ]
        is False
    )

    assert (
        result[
            "excessive_standard_dose_evidence"
        ]
        is True
    )

    assert (
        result[
            "safe_for_routine_evaluation"
        ]
        is False
    )


def test_one_pre_fractional_plus_two_later_standard_is_not_whitelisted():
    dob = date(
        2010,
        1,
        1,
    )

    result = normalize(
        assessment=date(
            2026,
            6,
            1,
        ),
        dob=dob,
        events=[
            (
                date(
                    2011,
                    1,
                    1,
                ),
                STANDARD,
            ),
            (
                date(
                    2018,
                    2,
                    1,
                ),
                FRACTIONAL,
            ),
            (
                date(
                    2025,
                    1,
                    1,
                ),
                STANDARD,
            ),
            (
                date(
                    2026,
                    6,
                    1,
                ),
                STANDARD,
            ),
        ],
    )

    assert result[
        "standard_dose_count"
    ] == 3

    assert (
        result[
            "standard_before_latest_fractional_count"
        ]
        == 1
    )

    assert (
        result[
            "standard_after_latest_fractional_count"
        ]
        == 2
    )

    assert (
        result[
            "fractional_regularization_third_standard_allowed"
        ]
        is False
    )

    assert (
        result[
            "excessive_standard_dose_evidence"
        ]
        is True
    )

    assert (
        result[
            "safe_for_routine_evaluation"
        ]
        is False
    )
