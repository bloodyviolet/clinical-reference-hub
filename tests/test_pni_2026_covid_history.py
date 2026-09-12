from datetime import date, timedelta

import pytest

import schemas

from clinical_tools.pni_history import (
    COVID_CHILD_PRODUCT_CORONAVAC,
    COVID_CHILD_PRODUCT_MODERNA,
    COVID_CHILD_PRODUCT_PFIZER,
    normalize_covid_child_history,
)


ASSESSMENT = date(
    2026,
    9,
    11,
)

DOB = date(
    2021,
    9,
    11,
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
            if events or undated
            else "documented_zero_dose"
        )

    return schemas.PniVaccineHistory(
        vaccine_key="covid_19",
        history_state=state,
        doses=[
            schemas.PniDoseRecord(
                administration_date=event[
                    0
                ],
                product_key=event[
                    1
                ],
                documentation_source="official_registry",
            )
            for event in events
        ],
        reported_prior_doses_without_exact_dates=undated,
    )


def normalize(
    events=None,
    *,
    role_events=None,
    scope="complete",
    state=None,
    undated=0,
    assessment=ASSESSMENT,
    dob=DOB,
):
    return normalize_covid_child_history(
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


def under5_date(
    month,
    day=11,
):
    return date(
        2026,
        month,
        day,
    )


def test_zero_history_is_safe_documented_zero_exposure():
    result = normalize()

    assert (
        result[
            "product_sequence_state"
        ]
        == "documented_zero_exposure"
    )

    assert result[
        "valid_under5_exposure_count"
    ] == 0

    assert result[
        "safe_for_under5_series_evaluation"
    ] is True


def test_pfizer_single_is_authorized_prefix():
    result = normalize(
        [
            (
                under5_date(
                    3
                ),
                COVID_CHILD_PRODUCT_PFIZER,
            ),
        ]
    )

    assert (
        result[
            "clinical_product_sequence"
        ]
        == [
            COVID_CHILD_PRODUCT_PFIZER,
        ]
    )

    assert (
        result[
            "product_sequence_state"
        ]
        == "source_authorized_incomplete_prefix"
    )

    assert result[
        "safe_for_under5_series_evaluation"
    ] is True


def test_pfizer_three_dose_sequence_complete():
    d1 = under5_date(
        1
    )

    d2 = (
        d1
        + timedelta(
            days=28,
        )
    )

    d3 = (
        d2
        + timedelta(
            days=56,
        )
    )

    result = normalize(
        [
            (
                d1,
                COVID_CHILD_PRODUCT_PFIZER,
            ),
            (
                d2,
                COVID_CHILD_PRODUCT_PFIZER,
            ),
            (
                d3,
                COVID_CHILD_PRODUCT_PFIZER,
            ),
        ]
    )

    assert (
        result[
            "product_sequence_state"
        ]
        == "source_authorized_complete"
    )

    assert result[
        "intervals_valid"
    ] is True


def test_moderna_two_dose_sequence_complete():
    d1 = under5_date(
        1
    )

    d2 = (
        d1
        + timedelta(
            days=28,
        )
    )

    result = normalize(
        [
            (
                d1,
                COVID_CHILD_PRODUCT_MODERNA,
            ),
            (
                d2,
                COVID_CHILD_PRODUCT_MODERNA,
            ),
        ]
    )

    assert (
        result[
            "product_sequence_state"
        ]
        == "source_authorized_complete"
    )

    assert result[
        "valid_under5_exposure_count"
    ] == 2


@pytest.mark.parametrize(
    "products",
    [
        (
            COVID_CHILD_PRODUCT_PFIZER,
            COVID_CHILD_PRODUCT_MODERNA,
            COVID_CHILD_PRODUCT_MODERNA,
        ),
        (
            COVID_CHILD_PRODUCT_PFIZER,
            COVID_CHILD_PRODUCT_MODERNA,
            COVID_CHILD_PRODUCT_PFIZER,
        ),
        (
            COVID_CHILD_PRODUCT_MODERNA,
            COVID_CHILD_PRODUCT_PFIZER,
            COVID_CHILD_PRODUCT_MODERNA,
        ),
        (
            COVID_CHILD_PRODUCT_CORONAVAC,
            COVID_CHILD_PRODUCT_PFIZER,
            COVID_CHILD_PRODUCT_MODERNA,
        ),
        (
            COVID_CHILD_PRODUCT_CORONAVAC,
            COVID_CHILD_PRODUCT_MODERNA,
            COVID_CHILD_PRODUCT_PFIZER,
        ),
        (
            COVID_CHILD_PRODUCT_CORONAVAC,
            COVID_CHILD_PRODUCT_CORONAVAC,
            COVID_CHILD_PRODUCT_PFIZER,
        ),
    ],
)
def test_source_authorized_mixed_sequences_complete(
    products,
):
    d1 = under5_date(
        1
    )

    d2 = (
        d1
        + timedelta(
            days=28,
        )
    )

    d3 = (
        d2
        + timedelta(
            days=56,
        )
    )

    result = normalize(
        [
            (
                d1,
                products[
                    0
                ],
            ),
            (
                d2,
                products[
                    1
                ],
            ),
            (
                d3,
                products[
                    2
                ],
            ),
        ]
    )

    assert (
        result[
            "product_sequence_state"
        ]
        == "source_authorized_complete"
    )

    assert result[
        "safe_for_under5_series_evaluation"
    ] is True


def test_registration_role_is_preserved_but_not_clinical_ordinal():
    d1 = under5_date(
        1
    )

    d2 = (
        d1
        + timedelta(
            days=28,
        )
    )

    result = normalize(
        [
            (
                d1,
                COVID_CHILD_PRODUCT_PFIZER,
            ),
            (
                d2,
                COVID_CHILD_PRODUCT_MODERNA,
            ),
        ],
        role_events=[
            {
                "administration_date":
                    d1,
                "source_registration_role":
                    "D1",
            },
            {
                "administration_date":
                    d2,
                "source_registration_role":
                    "D1",
            },
        ],
    )

    events = result[
        "events"
    ]

    assert events[
        0
    ][
        "source_registration_role"
    ] == "D1"

    assert events[
        1
    ][
        "source_registration_role"
    ] == "D1"

    assert events[
        0
    ][
        "clinical_exposure_ordinal"
    ] == 1

    assert events[
        1
    ][
        "clinical_exposure_ordinal"
    ] == 2

    assert (
        result[
            "registration_role_defines_clinical_ordinal"
        ]
        is False
    )


def test_chronology_not_input_order_defines_ordinal():
    early = under5_date(
        1
    )

    late = (
        early
        + timedelta(
            days=28,
        )
    )

    result = normalize(
        [
            (
                late,
                COVID_CHILD_PRODUCT_MODERNA,
            ),
            (
                early,
                COVID_CHILD_PRODUCT_PFIZER,
            ),
        ]
    )

    events = [
        event
        for event in result[
            "events"
        ]
        if event[
            "age_scope_at_exposure"
        ]
        == "under5_series_age"
    ]

    assert events[
        0
    ][
        "administration_date"
    ] == early

    assert events[
        0
    ][
        "clinical_exposure_ordinal"
    ] == 1

    assert events[
        1
    ][
        "administration_date"
    ] == late

    assert events[
        1
    ][
        "clinical_exposure_ordinal"
    ] == 2


def test_first_interval_exactly_28_days_is_valid():
    d1 = under5_date(
        1
    )

    d2 = (
        d1
        + timedelta(
            days=28,
        )
    )

    result = normalize(
        [
            (
                d1,
                COVID_CHILD_PRODUCT_MODERNA,
            ),
            (
                d2,
                COVID_CHILD_PRODUCT_MODERNA,
            ),
        ]
    )

    assert result[
        "interval_checks"
    ][
        0
    ][
        "actual_days"
    ] == 28

    assert result[
        "intervals_valid"
    ] is True


def test_first_interval_27_days_fails_closed():
    d1 = under5_date(
        1
    )

    d2 = (
        d1
        + timedelta(
            days=27,
        )
    )

    result = normalize(
        [
            (
                d1,
                COVID_CHILD_PRODUCT_MODERNA,
            ),
            (
                d2,
                COVID_CHILD_PRODUCT_MODERNA,
            ),
        ]
    )

    assert result[
        "intervals_valid"
    ] is False

    assert result[
        "safe_for_under5_series_evaluation"
    ] is False


def test_second_interval_exactly_56_days_is_valid():
    d1 = under5_date(
        1
    )

    d2 = (
        d1
        + timedelta(
            days=28,
        )
    )

    d3 = (
        d2
        + timedelta(
            days=56,
        )
    )

    result = normalize(
        [
            (
                d1,
                COVID_CHILD_PRODUCT_PFIZER,
            ),
            (
                d2,
                COVID_CHILD_PRODUCT_PFIZER,
            ),
            (
                d3,
                COVID_CHILD_PRODUCT_PFIZER,
            ),
        ]
    )

    assert result[
        "interval_checks"
    ][
        1
    ][
        "actual_days"
    ] == 56

    assert result[
        "intervals_valid"
    ] is True


def test_second_interval_55_days_fails_closed():
    d1 = under5_date(
        1
    )

    d2 = (
        d1
        + timedelta(
            days=28,
        )
    )

    d3 = (
        d2
        + timedelta(
            days=55,
        )
    )

    result = normalize(
        [
            (
                d1,
                COVID_CHILD_PRODUCT_PFIZER,
            ),
            (
                d2,
                COVID_CHILD_PRODUCT_PFIZER,
            ),
            (
                d3,
                COVID_CHILD_PRODUCT_PFIZER,
            ),
        ]
    )

    assert result[
        "intervals_valid"
    ] is False

    assert result[
        "safe_for_under5_series_evaluation"
    ] is False


def test_unsupported_sequence_fails_closed():
    d1 = under5_date(
        1
    )

    d2 = (
        d1
        + timedelta(
            days=28,
        )
    )

    result = normalize(
        [
            (
                d1,
                COVID_CHILD_PRODUCT_PFIZER,
            ),
            (
                d2,
                COVID_CHILD_PRODUCT_CORONAVAC,
            ),
        ]
    )

    assert (
        result[
            "product_sequence_state"
        ]
        == "unsupported_sequence"
    )

    assert result[
        "safe_for_under5_series_evaluation"
    ] is False


def test_generic_covid_product_key_fails_closed():
    result = normalize(
        [
            (
                under5_date(
                    1
                ),
                "covid_19",
            ),
        ]
    )

    assert result[
        "unsupported_product_keys"
    ] == [
        "covid_19",
    ]

    assert result[
        "safe_for_under5_series_evaluation"
    ] is False


def test_unknown_product_fails_closed():
    result = normalize(
        [
            (
                under5_date(
                    1
                ),
                "covid_unknown_product",
            ),
        ]
    )

    assert result[
        "unsupported_product_keys"
    ] == [
        "covid_unknown_product",
    ]

    assert result[
        "safe_for_under5_series_evaluation"
    ] is False


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
        scope=scope,
    )

    assert result[
        "source_history_incomplete"
    ] is True

    assert result[
        "safe_for_under5_series_evaluation"
    ] is False


@pytest.mark.parametrize(
    "state",
    [
        "partial_record",
        "unknown",
    ],
)
def test_incomplete_history_state_fails_closed(
    state,
):
    undated = (
        1
        if state == "partial_record"
        else 0
    )

    result = normalize(
        state=state,
        undated=undated,
    )

    assert result[
        "source_history_incomplete"
    ] is True

    assert result[
        "safe_for_under5_series_evaluation"
    ] is False


def test_undated_prior_dose_evidence_fails_closed():
    result = normalize(
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
        "safe_for_under5_series_evaluation"
    ] is False


def test_future_event_rejected():
    future = (
        ASSESSMENT
        + timedelta(
            days=1,
        )
    )

    with pytest.raises(
        ValueError,
        match="cannot follow assessment_date",
    ):
        normalize(
            [
                (
                    future,
                    COVID_CHILD_PRODUCT_PFIZER,
                ),
            ]
        )


def test_event_before_birth_rejected():
    with pytest.raises(
        ValueError,
        match="cannot precede date_of_birth",
    ):
        normalize(
            [
                (
                    date(
                        2021,
                        9,
                        10,
                    ),
                    COVID_CHILD_PRODUCT_PFIZER,
                ),
            ]
        )


def test_same_day_duplicate_rejected():
    event_date = under5_date(
        1
    )

    with pytest.raises(
        ValueError,
        match="same-day COVID lifetime event ambiguity",
    ):
        normalize(
            [
                (
                    event_date,
                    COVID_CHILD_PRODUCT_PFIZER,
                ),
                (
                    event_date,
                    COVID_CHILD_PRODUCT_MODERNA,
                ),
            ]
        )


def test_registration_metadata_must_reconcile():
    event_date = under5_date(
        1
    )

    with pytest.raises(
        ValueError,
        match="must reconcile",
    ):
        normalize(
            [
                (
                    event_date,
                    COVID_CHILD_PRODUCT_PFIZER,
                ),
            ],
            role_events=[
                {
                    "administration_date":
                        event_date
                        + timedelta(
                            days=1,
                        ),
                    "source_registration_role":
                        "D1",
                },
            ],
        )


def test_duplicate_registration_metadata_date_rejected():
    event_date = under5_date(
        1
    )

    with pytest.raises(
        ValueError,
        match="duplicate COVID registration metadata date",
    ):
        normalize(
            [
                (
                    event_date,
                    COVID_CHILD_PRODUCT_PFIZER,
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
                        "1a dose",
                },
            ],
        )


def test_registration_role_is_trimmed_and_preserved():
    event_date = under5_date(
        1
    )

    result = normalize(
        [
            (
                event_date,
                COVID_CHILD_PRODUCT_PFIZER,
            ),
        ],
        role_events=[
            {
                "administration_date":
                    event_date,
                "source_registration_role":
                    "  D1  ",
            },
        ],
    )

    assert result[
        "events"
    ][
        0
    ][
        "source_registration_role"
    ] == "D1"


def test_event_before_exact_6_months_is_retained_but_fails_closed():
    dob = date(
        2026,
        1,
        1,
    )

    event_date = date(
        2026,
        6,
        30,
    )

    result = normalize(
        [
            (
                event_date,
                COVID_CHILD_PRODUCT_PFIZER,
            ),
        ],
        dob=dob,
        assessment=date(
            2026,
            7,
            1,
        ),
    )

    assert result[
        "before_6m_event_count"
    ] == 1

    assert result[
        "valid_under5_exposure_count"
    ] == 0

    assert result[
        "safe_for_under5_series_evaluation"
    ] is False


def test_event_exactly_at_6_months_is_under5_exposure():
    dob = date(
        2026,
        1,
        1,
    )

    event_date = date(
        2026,
        7,
        1,
    )

    result = normalize(
        [
            (
                event_date,
                COVID_CHILD_PRODUCT_PFIZER,
            ),
        ],
        dob=dob,
        assessment=event_date,
    )

    assert result[
        "before_6m_event_count"
    ] == 0

    assert result[
        "valid_under5_exposure_count"
    ] == 1


def test_event_day_before_fifth_birthday_is_under5_exposure():
    dob = date(
        2021,
        9,
        11,
    )

    event_date = date(
        2026,
        9,
        10,
    )

    result = normalize(
        [
            (
                event_date,
                COVID_CHILD_PRODUCT_PFIZER,
            ),
        ],
        dob=dob,
        assessment=date(
            2026,
            9,
            11,
        ),
    )

    assert result[
        "valid_under5_exposure_count"
    ] == 1

    assert result[
        "at_or_after_5y_event_count"
    ] == 0


def test_event_exactly_at_fifth_birthday_is_not_under5_exposure():
    dob = date(
        2021,
        9,
        11,
    )

    event_date = date(
        2026,
        9,
        11,
    )

    result = normalize(
        [
            (
                event_date,
                COVID_CHILD_PRODUCT_PFIZER,
            ),
        ],
        dob=dob,
        assessment=event_date,
    )

    assert result[
        "valid_under5_exposure_count"
    ] == 0

    assert result[
        "at_or_after_5y_event_count"
    ] == 1


def test_post_age5_event_not_folded_into_under5_sequence():
    dob = date(
        2021,
        9,
        11,
    )

    under5 = date(
        2026,
        8,
        1,
    )

    age5 = date(
        2026,
        9,
        11,
    )

    result = normalize(
        [
            (
                under5,
                COVID_CHILD_PRODUCT_PFIZER,
            ),
            (
                age5,
                COVID_CHILD_PRODUCT_MODERNA,
            ),
        ],
        dob=dob,
        assessment=age5,
    )

    assert result[
        "clinical_product_sequence"
    ] == [
        COVID_CHILD_PRODUCT_PFIZER,
    ]

    assert result[
        "valid_under5_exposure_count"
    ] == 1

    assert result[
        "at_or_after_5y_event_count"
    ] == 1


def test_age_out_contract_is_exposed_but_no_decision_is_assigned():
    result = normalize()

    assert result[
        "age_out_rule_resolved"
    ] is True

    assert (
        result[
            "post_age5_under5_completion_allowed"
        ]
        is False
    )

    assert (
        result[
            "normalizer_assigns_due_decision"
        ]
        is False
    )


def test_current_2026_initiation_product_key_is_exposed():
    result = normalize()

    assert (
        result[
            "current_2026_initiation_product_key"
        ]
        == COVID_CHILD_PRODUCT_PFIZER
    )


def test_no_special_condition_or_score_inference():
    result = normalize()

    assert result[
        "special_condition_inferred"
    ] is False

    assert result[
        "synthetic_score_applied"
    ] is False


def test_wrong_vaccine_family_rejected():
    wrong = schemas.PniVaccineHistory(
        vaccine_key="influenza",
        history_state="documented_zero_dose",
    )

    with pytest.raises(
        ValueError,
        match="vaccine_key covid_19",
    ):
        normalize_covid_child_history(
            assessment_date=ASSESSMENT,
            date_of_birth=DOB,
            history=wrong,
            history_scope="complete",
        )
