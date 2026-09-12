from datetime import date

import pytest

import schemas

from clinical_tools.pni_history import (
    MMR_PRODUCT_SCRV,
    VARICELLA_HISTORY_MODEL_ID,
    normalize_mmr_history,
    normalize_varicella_child_history,
)


def vaccine_history(
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


def mmr_normalized(
    *,
    dob,
    assessment,
    events=None,
    state=None,
    scope="complete",
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

    return normalize_mmr_history(
        assessment_date=assessment,
        date_of_birth=dob,
        history=schemas.PniVaccineHistory(
            vaccine_key="mmr",
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
        ),
        history_scope=scope,
    )


def normalize(
    *,
    dob,
    assessment,
    varicella=None,
    varicella_scope="complete",
    mmr=None,
):
    if varicella is None:
        varicella = vaccine_history(
            "varicella"
        )

    if mmr is None:
        mmr = mmr_normalized(
            dob=dob,
            assessment=assessment,
        )

    return normalize_varicella_child_history(
        assessment_date=assessment,
        date_of_birth=dob,
        varicella_history=varicella,
        varicella_history_scope=varicella_scope,
        mmr_history=mmr,
    )


def test_documented_zero_sources_are_safe():
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
    ] == VARICELLA_HISTORY_MODEL_ID

    assert result[
        "lifetime_varicella_component_event_count"
    ] == 0

    assert result[
        "valid_child_component_dose_count"
    ] == 0

    assert result[
        "child_series_complete"
    ] is False

    assert result[
        "safe_for_routine_evaluation"
    ] is True


def test_monovalent_event_counts_as_one_vz_component():
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
        varicella=vaccine_history(
            "varicella",
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
        "lifetime_varicella_component_event_count"
    ] == 1

    assert result[
        "valid_child_component_dose_count"
    ] == 1

    assert result[
        "first_valid_component_date"
    ] == date(
        2025,
        4,
        1,
    )

    event = result[
        "events"
    ][0]

    assert event[
        "source_family"
    ] == "varicella"

    assert event[
        "product_key"
    ] == "varicella"

    assert event[
        "physical_event_kind"
    ] == "monovalent_varicella"

    assert event[
        "vz_series_counted"
    ] is True

    assert event[
        "vz_series_role"
    ] == "D1"


def test_scrv_event_counts_as_one_vz_component_without_cloning():
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

    mmr = mmr_normalized(
        dob=dob,
        assessment=assessment,
        events=[
            (
                assessment,
                MMR_PRODUCT_SCRV,
            ),
        ],
    )

    result = normalize(
        dob=dob,
        assessment=assessment,
        mmr=mmr,
    )

    assert result[
        "lifetime_varicella_component_event_count"
    ] == 1

    assert len(
        result[
            "scrv_component_events"
        ]
    ) == 1

    assert len(
        result[
            "events"
        ]
    ) == 1

    event = result[
        "events"
    ][0]

    assert event[
        "source_family"
    ] == "mmr"

    assert event[
        "product_key"
    ] == "mmrv_scrv"

    assert event[
        "contains_varicella"
    ] is True

    assert event[
        "physical_event_kind"
    ] == "scrv_varicella_component"

    assert result[
        "physical_event_cloning_applied"
    ] is False


def test_monovalent_plus_scrv_can_complete_child_series():
    dob = date(
        2024,
        1,
        1,
    )

    first = date(
        2025,
        4,
        1,
    )

    second = date(
        2028,
        1,
        1,
    )

    result = normalize(
        dob=dob,
        assessment=second,
        varicella=vaccine_history(
            "varicella",
            [
                first,
            ],
        ),
        mmr=mmr_normalized(
            dob=dob,
            assessment=second,
            events=[
                (
                    second,
                    MMR_PRODUCT_SCRV,
                ),
            ],
        ),
    )

    assert result[
        "valid_child_component_dose_count"
    ] == 2

    assert result[
        "valid_child_series_dates"
    ] == [
        first,
        second,
    ]

    assert result[
        "child_series_complete"
    ] is True

    assert result[
        "safe_for_routine_evaluation"
    ] is True


def test_two_scrv_events_can_complete_child_series():
    dob = date(
        2024,
        1,
        1,
    )

    first = date(
        2025,
        4,
        1,
    )

    second = date(
        2028,
        1,
        1,
    )

    result = normalize(
        dob=dob,
        assessment=second,
        mmr=mmr_normalized(
            dob=dob,
            assessment=second,
            events=[
                (
                    first,
                    MMR_PRODUCT_SCRV,
                ),
                (
                    second,
                    MMR_PRODUCT_SCRV,
                ),
            ],
        ),
    )

    assert len(
        result[
            "scrv_component_events"
        ]
    ) == 2

    assert result[
        "valid_child_component_dose_count"
    ] == 2

    assert result[
        "child_series_complete"
    ] is True


def test_mmr_30_day_validity_does_not_define_vz_validity():
    dob = date(
        2024,
        1,
        1,
    )

    first = date(
        2025,
        4,
        1,
    )

    second = date(
        2025,
        5,
        1,
    )

    mmr = mmr_normalized(
        dob=dob,
        assessment=second,
        events=[
            (
                first,
                MMR_PRODUCT_SCRV,
            ),
            (
                second,
                MMR_PRODUCT_SCRV,
            ),
        ],
    )

    assert mmr[
        "general_valid_component_dose_count"
    ] == 2

    result = normalize(
        dob=dob,
        assessment=second,
        mmr=mmr,
    )

    assert result[
        "valid_child_component_dose_count"
    ] == 1

    assert result[
        "child_series_complete"
    ] is False

    assert result[
        "short_interval_event_count"
    ] == 1

    assert result[
        "mmr_validity_defines_vz_validity"
    ] is False

    assert result[
        "safe_for_routine_evaluation"
    ] is True


def test_exact_three_calendar_month_interval_counts_second_component():
    dob = date(
        2024,
        1,
        1,
    )

    first = date(
        2025,
        4,
        30,
    )

    second = date(
        2025,
        7,
        30,
    )

    result = normalize(
        dob=dob,
        assessment=second,
        varicella=vaccine_history(
            "varicella",
            [
                first,
                second,
            ],
        ),
    )

    assert result[
        "valid_child_component_dose_count"
    ] == 2

    assert result[
        "child_series_complete"
    ] is True

    assert result[
        "interval_checks"
    ][0][
        "minimum_date"
    ] == second

    assert result[
        "interval_checks"
    ][0][
        "fixed_day_conversion_used"
    ] is False


def test_day_before_three_calendar_month_threshold_does_not_count_d2():
    dob = date(
        2024,
        1,
        1,
    )

    first = date(
        2025,
        4,
        30,
    )

    second = date(
        2025,
        7,
        29,
    )

    result = normalize(
        dob=dob,
        assessment=second,
        varicella=vaccine_history(
            "varicella",
            [
                first,
                second,
            ],
        ),
    )

    assert result[
        "valid_child_component_dose_count"
    ] == 1

    assert result[
        "child_series_complete"
    ] is False

    assert result[
        "short_interval_event_count"
    ] == 1

    assert result[
        "safe_for_routine_evaluation"
    ] is True


def test_short_interval_extra_does_not_erase_later_valid_series():
    dob = date(
        2024,
        1,
        1,
    )

    first = date(
        2025,
        4,
        1,
    )

    extra = date(
        2025,
        5,
        1,
    )

    valid_second = date(
        2025,
        7,
        1,
    )

    result = normalize(
        dob=dob,
        assessment=valid_second,
        varicella=vaccine_history(
            "varicella",
            [
                first,
                extra,
                valid_second,
            ],
        ),
    )

    assert result[
        "lifetime_varicella_component_event_count"
    ] == 3

    assert result[
        "valid_child_series_dates"
    ] == [
        first,
        valid_second,
    ]

    assert result[
        "child_series_complete"
    ] is True

    assert result[
        "short_interval_event_count"
    ] == 1

    roles = {
        event[
            "administration_date"
        ]:
            event[
                "vz_series_role"
            ]
        for event in result[
            "events"
        ]
    }

    assert roles[
        first
    ] == "D1"

    assert roles[
        extra
    ] == "short_interval_extra_not_counted"

    assert roles[
        valid_second
    ] == "D2"


def test_pre15_monovalent_evidence_fails_closed():
    dob = date(
        2024,
        1,
        1,
    )

    event_date = date(
        2025,
        3,
        31,
    )

    result = normalize(
        dob=dob,
        assessment=event_date,
        varicella=vaccine_history(
            "varicella",
            [
                event_date,
            ],
        ),
    )

    assert result[
        "pre15_component_evidence_present"
    ] is True

    assert result[
        "valid_child_component_dose_count"
    ] == 0

    assert result[
        "safe_for_routine_evaluation"
    ] is False

    assert (
        "pre15_vz_component_requires_explicit_pathway_context"
        in result[
            "invalid_history_reasons"
        ]
    )


def test_pre15_scrv_mmr_event_is_not_silently_vz_d1():
    dob = date(
        2024,
        1,
        1,
    )

    event_date = date(
        2025,
        1,
        1,
    )

    result = normalize(
        dob=dob,
        assessment=event_date,
        mmr=mmr_normalized(
            dob=dob,
            assessment=event_date,
            events=[
                (
                    event_date,
                    MMR_PRODUCT_SCRV,
                ),
            ],
        ),
    )

    assert result[
        "pre15_component_evidence_present"
    ] is True

    assert result[
        "valid_child_component_dose_count"
    ] == 0

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_age7plus_component_is_preserved_but_not_child_series_counted():
    dob = date(
        2020,
        1,
        1,
    )

    event_date = date(
        2027,
        1,
        1,
    )

    result = normalize(
        dob=dob,
        assessment=event_date,
        varicella=vaccine_history(
            "varicella",
            [
                event_date,
            ],
        ),
    )

    assert result[
        "lifetime_varicella_component_event_count"
    ] == 1

    assert result[
        "routine_age_component_event_count"
    ] == 0

    assert result[
        "valid_child_component_dose_count"
    ] == 0

    assert result[
        "events"
    ][0][
        "vz_age_scope"
    ] == "age7plus_component_evidence"

    assert result[
        "safe_for_routine_evaluation"
    ] is True


def test_same_day_monovalent_and_scrv_are_ambiguous():
    dob = date(
        2024,
        1,
        1,
    )

    event_date = date(
        2025,
        4,
        1,
    )

    result = normalize(
        dob=dob,
        assessment=event_date,
        varicella=vaccine_history(
            "varicella",
            [
                event_date,
            ],
        ),
        mmr=mmr_normalized(
            dob=dob,
            assessment=event_date,
            events=[
                (
                    event_date,
                    MMR_PRODUCT_SCRV,
                ),
            ],
        ),
    )

    assert result[
        "chronology_ambiguous"
    ] is True

    assert result[
        "same_day_ambiguous_dates"
    ] == [
        event_date,
    ]

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_partial_monovalent_history_fails_closed():
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

    result = normalize(
        dob=dob,
        assessment=assessment,
        varicella=vaccine_history(
            "varicella",
            state="partial_record",
            undated=1,
        ),
        varicella_scope="partial",
    )

    assert result[
        "source_history_incomplete"
    ] is True

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_partial_mmr_history_fails_closed_for_cross_family_completeness():
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

    mmr = mmr_normalized(
        dob=dob,
        assessment=assessment,
        state="partial_record",
        scope="partial",
        undated=1,
    )

    result = normalize(
        dob=dob,
        assessment=assessment,
        mmr=mmr,
    )

    assert result[
        "source_history_incomplete"
    ] is True

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_scrv_must_arrive_through_locked_mmr_history():
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
        varicella=vaccine_history(
            "varicella",
            [
                date(
                    2025,
                    4,
                    1,
                ),
            ],
            product_key="mmrv_scrv",
        ),
    )

    assert (
        "mmrv_scrv"
        in result[
            "unsupported_product_keys"
        ]
    )

    assert result[
        "safe_for_routine_evaluation"
    ] is False


def test_raw_mmr_history_is_rejected():
    with pytest.raises(
        ValueError,
        match="LOCKED normalized MMR history",
    ):
        normalize_varicella_child_history(
            assessment_date=date(
                2025,
                4,
                1,
            ),
            date_of_birth=date(
                2024,
                1,
                1,
            ),
            varicella_history=vaccine_history(
                "varicella"
            ),
            varicella_history_scope="complete",
            mmr_history=schemas.PniVaccineHistory(
                vaccine_key="mmr",
                history_state="documented_zero_dose",
            ),
        )


def test_wrong_normalized_mmr_family_is_rejected():
    mmr = {
        "target_family":
            "not_mmr_routine_history",

        "history_scope":
            "complete",

        "age_15m_date":
            date(
                2025,
                4,
                1,
            ),

        "events":
            [],
    }

    with pytest.raises(
        ValueError,
        match="target_family",
    ):
        normalize_varicella_child_history(
            assessment_date=date(
                2025,
                4,
                1,
            ),
            date_of_birth=date(
                2024,
                1,
                1,
            ),
            varicella_history=vaccine_history(
                "varicella"
            ),
            varicella_history_scope="complete",
            mmr_history=mmr,
        )


def test_future_monovalent_event_is_rejected():
    dob = date(
        2024,
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
                2025,
                4,
                1,
            ),
            varicella=vaccine_history(
                "varicella",
                [
                    date(
                        2025,
                        4,
                        2,
                    ),
                ],
            ),
        )


def test_normalizer_never_infers_disease_or_context():
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
        "mmr_validity_defines_vz_validity"
    ] is False

    assert result[
        "physical_event_cloning_applied"
    ] is False

    assert result[
        "disease_history_inferred"
    ] is False

    assert result[
        "epidemiologic_context_inferred"
    ] is False

    assert result[
        "pregnancy_inferred"
    ] is False

    assert result[
        "special_condition_inferred"
    ] is False

    assert result[
        "normalizer_assigns_due_decision"
    ] is False

    assert result[
        "synthetic_score_applied"
    ] is False
