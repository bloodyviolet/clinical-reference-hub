from datetime import date, timedelta

import pytest

import schemas

from clinical_tools.pni_history import (
    MMR_GENERAL_INTERVAL_EXCEPTION_AUTHORIZATION_KEY,
    MMR_PRODUCT_SCR,
    MMR_PRODUCT_SCRV,
    normalize_mmr_history,
)


SCR = MMR_PRODUCT_SCR
SCRV = MMR_PRODUCT_SCRV


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
        vaccine_key="mmr",
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
    exception_events=None,
):
    return normalize_mmr_history(
        assessment_date=assessment,
        date_of_birth=dob,
        history=history(
            events,
            state=state,
            undated=undated,
        ),
        history_scope=scope,
        registration_role_events=role_events,
        historical_interval_exception_events=(
            exception_events
        ),
    )


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
        "routine_component_event_count"
    ] == 0

    assert result[
        "general_valid_component_dose_count"
    ] == 0

    assert result[
        "occupational_valid_component_dose_count"
    ] == 0

    assert result[
        "safe_for_routine_evaluation"
    ] is True


@pytest.mark.parametrize(
    "product",
    [
        SCR,
        SCRV,
    ],
)
def test_supported_product_identity(
    product,
):
    assessment = date(
        2026,
        1,
        1,
    )

    result = normalize(
        assessment=assessment,
        dob=date(
            2025,
            1,
            1,
        ),
        events=[
            (
                assessment,
                product,
            ),
        ],
    )

    assert result[
        "unsupported_product_keys"
    ] == []


def test_input_order_does_not_define_chronology():
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

    second = date(
        2026,
        1,
        31,
    )

    result = normalize(
        assessment=second,
        dob=dob,
        events=[
            (
                second,
                SCR,
            ),
            (
                first,
                SCR,
            ),
        ],
    )

    assert [
        event[
            "administration_date"
        ]
        for event
        in result[
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
        for event
        in result[
            "events"
        ]
    ] == [
        1,
        2,
    ]


def test_day_before_6m_is_retained_but_unsafe():
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
                SCR,
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
        == "before_scr_minimum_history_age"
    )

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_exact_6m_scr_is_dose_zero():
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
                SCR,
            ),
        ],
    )

    assert result[
        "dose_zero_count"
    ] == 1

    assert result[
        "routine_component_event_count"
    ] == 0

    assert (
        result[
            "events"
        ][
            0
        ][
            "clinical_role"
        ]
        == "dose_zero_history"
    )


def test_day_before_12m_scr_is_still_dose_zero():
    dob = date(
        2025,
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
                SCR,
            ),
        ],
    )

    assert result[
        "dose_zero_count"
    ] == 1

    assert result[
        "routine_component_event_count"
    ] == 0


def test_exact_12m_scr_is_routine_component():
    dob = date(
        2025,
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
                SCR,
            ),
        ],
    )

    assert result[
        "dose_zero_count"
    ] == 0

    assert result[
        "routine_component_event_count"
    ] == 1

    assert result[
        "general_valid_component_dose_count"
    ] == 1

    assert result[
        "occupational_valid_component_dose_count"
    ] == 1


def test_pre12_scrv_fails_closed():
    dob = date(
        2025,
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
                SCRV,
            ),
        ],
    )

    assert result[
        "unsupported_age_product_event_count"
    ] == 1

    assert (
        result[
            "events"
        ][
            0
        ][
            "clinical_role"
        ]
        == "unsupported_pre12_mmrv"
    )

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_exact_12m_scrv_counts_as_one_mmr_component():
    dob = date(
        2025,
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
                SCRV,
            ),
        ],
    )

    event = result[
        "events"
    ][
        0
    ]

    assert event[
        "contains_measles"
    ] is True

    assert event[
        "contains_mumps"
    ] is True

    assert event[
        "contains_rubella"
    ] is True

    assert event[
        "contains_varicella"
    ] is True

    assert result[
        "routine_component_event_count"
    ] == 1

    assert result[
        "mmrv_scrv_routine_event_count"
    ] == 1


def test_scr_product_does_not_contain_varicella():
    dob = date(
        2025,
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
                SCR,
            ),
        ],
    )

    event = result[
        "events"
    ][
        0
    ]

    assert event[
        "contains_varicella"
    ] is False


def test_d0_plus_29_day_routine_is_unsafe():
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

    routine = (
        d0
        + timedelta(
            days=29,
        )
    )

    result = normalize(
        assessment=routine,
        dob=dob,
        events=[
            (
                d0,
                SCR,
            ),
            (
                routine,
                SCR,
            ),
        ],
    )

    assert result[
        "d0_to_routine_interval_checks"
    ][
        0
    ][
        "valid"
    ] is False

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_d0_plus_30_day_routine_is_valid():
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

    routine = (
        d0
        + timedelta(
            days=30,
        )
    )

    result = normalize(
        assessment=routine,
        dob=dob,
        events=[
            (
                d0,
                SCR,
            ),
            (
                routine,
                SCR,
            ),
        ],
    )

    assert result[
        "d0_to_routine_interval_checks"
    ][
        0
    ][
        "actual_days"
    ] == 30

    assert result[
        "d0_to_routine_interval_checks"
    ][
        0
    ][
        "valid"
    ] is True

    assert result[
        "safe_for_routine_evaluation"
    ] is True


def test_routine_14_day_interval_is_unsafe_even_with_metadata():
    dob = date(
        2020,
        1,
        1,
    )

    first = date(
        2026,
        1,
        1,
    )

    second = (
        first
        + timedelta(
            days=14,
        )
    )

    result = normalize(
        assessment=second,
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
        exception_events=[
            exception(
                first,
                second,
            ),
        ],
    )

    check = result[
        "interval_checks"
    ][
        0
    ]

    assert check[
        "below_absolute_15d_minimum"
    ] is True

    assert check[
        "general_series_interval_valid"
    ] is False

    assert check[
        "health_worker_interval_valid"
    ] is False

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_15_day_without_exception_evidence_is_unsafe():
    dob = date(
        2020,
        1,
        1,
    )

    first = date(
        2026,
        1,
        1,
    )

    second = (
        first
        + timedelta(
            days=15,
        )
    )

    result = normalize(
        assessment=second,
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
    )

    check = result[
        "interval_checks"
    ][
        0
    ]

    assert check[
        "requires_exception_evidence"
    ] is True

    assert result[
        "unresolved_short_interval_evidence"
    ] is True

    assert result[
        "safe_for_routine_evaluation"
    ] is False


@pytest.mark.parametrize(
    "days",
    [
        15,
        20,
        29,
    ],
)
def test_authorized_short_interval_counts_for_general_not_occupational(
    days,
):
    dob = date(
        2020,
        1,
        1,
    )

    first = date(
        2026,
        1,
        1,
    )

    second = (
        first
        + timedelta(
            days=days,
        )
    )

    result = normalize(
        assessment=second,
        dob=dob,
        events=[
            (
                first,
                SCR,
            ),
            (
                second,
                SCRV,
            ),
        ],
        exception_events=[
            exception(
                first,
                second,
            ),
        ],
    )

    check = result[
        "interval_checks"
    ][
        0
    ]

    assert check[
        "general_15d_exception_documented"
    ] is True

    assert check[
        "general_series_interval_valid"
    ] is True

    assert check[
        "health_worker_interval_valid"
    ] is False

    assert result[
        "general_valid_component_dose_count"
    ] == 2

    assert result[
        "occupational_valid_component_dose_count"
    ] == 1

    assert result[
        "safe_for_routine_evaluation"
    ] is True


def test_30_day_interval_counts_for_both_series():
    dob = date(
        2020,
        1,
        1,
    )

    first = date(
        2026,
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
                SCR,
            ),
            (
                second,
                SCRV,
            ),
        ],
    )

    assert result[
        "general_valid_component_dose_count"
    ] == 2

    assert result[
        "occupational_valid_component_dose_count"
    ] == 2

    assert result[
        "safe_for_routine_evaluation"
    ] is True


def test_extra_doses_are_retained_not_blanket_rejected():
    dob = date(
        2020,
        1,
        1,
    )

    events = [
        (
            date(
                2021,
                1,
                1,
            ),
            SCR,
        ),
        (
            date(
                2022,
                1,
                1,
            ),
            SCRV,
        ),
        (
            date(
                2023,
                1,
                1,
            ),
            SCR,
        ),
    ]

    result = normalize(
        assessment=date(
            2023,
            1,
            1,
        ),
        dob=dob,
        events=events,
    )

    assert result[
        "routine_component_event_count"
    ] == 3

    assert result[
        "general_valid_component_dose_count"
    ] == 3

    assert result[
        "occupational_valid_component_dose_count"
    ] == 3

    assert result[
        "safe_for_routine_evaluation"
    ] is True


def test_occupational_count_can_skip_short_general_exception_event():
    dob = date(
        2020,
        1,
        1,
    )

    first = date(
        2026,
        1,
        1,
    )

    middle = (
        first
        + timedelta(
            days=20,
        )
    )

    third = (
        first
        + timedelta(
            days=40,
        )
    )

    result = normalize(
        assessment=third,
        dob=dob,
        events=[
            (
                first,
                SCR,
            ),
            (
                middle,
                SCR,
            ),
            (
                third,
                SCR,
            ),
        ],
        exception_events=[
            exception(
                first,
                middle,
            ),
            exception(
                middle,
                third,
            ),
        ],
    )

    assert result[
        "general_valid_component_dose_count"
    ] == 3

    assert result[
        "occupational_valid_component_dose_count"
    ] == 2

    assert result[
        "safe_for_routine_evaluation"
    ] is True


@pytest.mark.parametrize(
    "product",
    [
        "mmr",
        "mr_legacy",
        "sr_legacy",
        "measles_monovalent",
        "unknown_mmr_product",
    ],
)
def test_unsupported_product_fails_closed(
    product,
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
        events=[
            (
                date(
                    2025,
                    1,
                    1,
                ),
                product,
            ),
        ],
    )

    assert product in result[
        "unsupported_product_keys"
    ]

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_source_registration_role_remains_provenance():
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
                SCR,
            ),
        ],
        role_events=[
            {
                "administration_date":
                    event_date,

                "source_registration_role":
                    "D1",
            },
        ],
    )

    event = result[
        "events"
    ][
        0
    ]

    assert event[
        "source_registration_role"
    ] == "D1"

    assert event[
        "clinical_role"
    ] == "dose_zero_history"

    assert result[
        "registration_role_defines_clinical_role"
    ] is False


def test_registration_metadata_must_reconcile():
    event_date = date(
        2026,
        1,
        1,
    )

    with pytest.raises(
        ValueError,
        match="must reconcile",
    ):
        normalize(
            assessment=event_date,
            dob=date(
                2020,
                1,
                1,
            ),
            events=[
                (
                    event_date,
                    SCR,
                ),
            ],
            role_events=[
                {
                    "administration_date":
                        date(
                            2025,
                            12,
                            31,
                        ),

                    "source_registration_role":
                        "D1",
                },
            ],
        )


def test_duplicate_registration_metadata_rejected():
    event_date = date(
        2026,
        1,
        1,
    )

    with pytest.raises(
        ValueError,
        match="duplicate MMR registration metadata date",
    ):
        normalize(
            assessment=event_date,
            dob=date(
                2020,
                1,
                1,
            ),
            events=[
                (
                    event_date,
                    SCR,
                ),
            ],
            role_events=[
                {
                    "administration_date":
                        event_date,

                    "source_registration_role":
                        "D1",
                },
                {
                    "administration_date":
                        event_date,

                    "source_registration_role":
                        "D2",
                },
            ],
        )


def test_exact_interval_exception_pair_reconciles():
    dob = date(
        2020,
        1,
        1,
    )

    first = date(
        2026,
        1,
        1,
    )

    second = date(
        2026,
        1,
        16,
    )

    result = normalize(
        assessment=second,
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
        exception_events=[
            exception(
                first,
                second,
            ),
        ],
    )

    assert result[
        "historical_interval_exception_pair_count"
    ] == 1

    assert result[
        "general_valid_component_dose_count"
    ] == 2


def test_duplicate_interval_exception_pair_rejected():
    dob = date(
        2020,
        1,
        1,
    )

    first = date(
        2026,
        1,
        1,
    )

    second = date(
        2026,
        1,
        16,
    )

    pair = exception(
        first,
        second,
    )

    with pytest.raises(
        ValueError,
        match="duplicate MMR historical interval exception pair",
    ):
        normalize(
            assessment=second,
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
            exception_events=[
                pair,
                pair,
            ],
        )


def test_reversed_interval_exception_pair_rejected():
    dob = date(
        2020,
        1,
        1,
    )

    first = date(
        2026,
        1,
        1,
    )

    second = date(
        2026,
        1,
        16,
    )

    with pytest.raises(
        ValueError,
        match="must be chronological",
    ):
        normalize(
            assessment=second,
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
            exception_events=[
                exception(
                    second,
                    first,
                ),
            ],
        )


def test_unreconciled_interval_exception_pair_rejected():
    dob = date(
        2020,
        1,
        1,
    )

    event_date = date(
        2026,
        1,
        1,
    )

    with pytest.raises(
        ValueError,
        match="must reconcile",
    ):
        normalize(
            assessment=event_date,
            dob=dob,
            events=[
                (
                    event_date,
                    SCR,
                ),
            ],
            exception_events=[
                exception(
                    event_date,
                    date(
                        2026,
                        1,
                        16,
                    ),
                ),
            ],
        )


@pytest.mark.parametrize(
    "scope",
    [
        "partial",
        "unknown",
    ],
)
def test_incomplete_scope_fails_closed(
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

    assert result[
        "safe_for_routine_evaluation"
    ] is False


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

    assert result[
        "safe_for_routine_evaluation"
    ] is False


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

    assert result[
        "safe_for_routine_evaluation"
    ] is False


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
                    SCR,
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
                    SCR,
                ),
            ],
        )


def test_same_day_duplicate_rejected():
    event_date = date(
        2026,
        1,
        1,
    )

    with pytest.raises(
        ValueError,
        match="same-day MMR lifetime event ambiguity",
    ):
        normalize(
            assessment=event_date,
            dob=date(
                2020,
                1,
                1,
            ),
            events=[
                (
                    event_date,
                    SCR,
                ),
                (
                    event_date,
                    SCRV,
                ),
            ],
        )


def test_exact_age30_role_preserved():
    dob = date(
        1996,
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
                SCR,
            ),
        ],
    )

    assert (
        result[
            "events"
        ][
            0
        ][
            "clinical_role"
        ]
        == "routine_component_dose_age30_to59"
    )


def test_exact_age60_role_preserved():
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
                SCR,
            ),
        ],
    )

    assert (
        result[
            "events"
        ][
            0
        ][
            "clinical_role"
        ]
        == "age60plus_component_evidence"
    )


def test_normalizer_does_not_assign_context_or_decision():
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

    assert result[
        "normalizer_assigns_due_decision"
    ] is False

    assert result[
        "occupation_inferred"
    ] is False

    assert result[
        "pregnancy_inferred"
    ] is False

    assert result[
        "epidemiologic_context_inferred"
    ] is False

    assert result[
        "special_condition_inferred"
    ] is False

    assert result[
        "synthetic_score_applied"
    ] is False
