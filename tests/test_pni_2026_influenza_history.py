from datetime import date

import pytest

import schemas

from clinical_tools.pni_history import (
    normalize_influenza_history,
)


ASSESSMENT = date(
    2026,
    9,
    11,
)


def history(
    dates=None,
    *,
    state=None,
    product_key="influenza",
    undated=0,
):
    dates = list(
        dates
        or []
    )

    if state is None:
        state = (
            "documented_doses"
            if dates or undated
            else "documented_zero_dose"
        )

    return schemas.PniVaccineHistory(
        vaccine_key="influenza",
        history_state=state,
        doses=[
            schemas.PniDoseRecord(
                administration_date=value,
                product_key=product_key,
                documentation_source="official_registry",
            )
            for value in dates
        ],
        reported_prior_doses_without_exact_dates=undated,
    )


def normalize(
    *,
    lifetime=None,
    scope="complete",
    cycle_key="SOURCE-CYCLE-A",
    cycle_state="documented_zero_dose",
    events=None,
    prior_state="documented_none",
):
    if lifetime is None:
        lifetime = history()

    return normalize_influenza_history(
        assessment_date=ASSESSMENT,
        history=lifetime,
        history_scope=scope,
        current_cycle_key=cycle_key,
        current_cycle_history_state=cycle_state,
        current_cycle_events=list(
            events
            or []
        ),
        prior_cycle_vaccination_state=prior_state,
    )


def event(
    value,
    strategy="routine",
):
    return {
        "administration_date":
            value,

        "strategy_layer":
            strategy,
    }


def test_opaque_cycle_key_is_preserved_without_parsing():
    result = normalize(
        cycle_key=(
            "Região Norte – 2025 / source supplied"
        ),
    )

    assert result[
        "current_cycle_key"
    ] == "Região Norte – 2025 / source supplied"

    assert result[
        "cycle_key_opaque"
    ] is True

    assert result[
        "cycle_key_parsed"
    ] is False

    assert result[
        "cycle_identity_derived_from_calendar_year"
    ] is False

    assert result[
        "geography_inferred_from_cycle_key"
    ] is False


def test_same_calendar_year_does_not_define_cycle_identity():
    dose_date = date(
        2026,
        1,
        15,
    )

    lifetime = history(
        [
            dose_date,
        ]
    )

    a = normalize(
        lifetime=lifetime,
        cycle_key="SOURCE-CYCLE-A",
        cycle_state="documented_doses",
        events=[
            event(
                dose_date
            ),
        ],
        prior_state="documented_prior",
    )

    b = normalize(
        lifetime=lifetime,
        cycle_key="SOURCE-CYCLE-B",
        cycle_state="documented_doses",
        events=[
            event(
                dose_date
            ),
        ],
        prior_state="documented_prior",
    )

    assert (
        a[
            "current_cycle_key"
        ]
        != b[
            "current_cycle_key"
        ]
    )

    assert (
        a[
            "current_cycle_events"
        ][
            0
        ][
            "administration_date"
        ].year
        == 2026
    )

    assert (
        b[
            "current_cycle_events"
        ][
            0
        ][
            "administration_date"
        ].year
        == 2026
    )


def test_documented_zero_current_cycle_is_safe_when_priming_known():
    result = normalize()

    assert result[
        "current_cycle_event_count"
    ] == 0

    assert result[
        "prior_cycle_vaccination_state"
    ] == "documented_none"

    assert result[
        "safe_for_routine_child_evaluation"
    ] is True


def test_prior_cycle_state_is_explicit_not_year_derived():
    prior_date = date(
        2025,
        4,
        1,
    )

    result = normalize(
        lifetime=history(
            [
                prior_date,
            ]
        ),
        prior_state="documented_prior",
    )

    assert result[
        "prior_cycle_vaccination_state"
    ] == "documented_prior"

    assert result[
        "unassigned_lifetime_event_count"
    ] == 1

    assert result[
        "cycle_identity_derived_from_calendar_year"
    ] is False


def test_current_cycle_event_reconciles_to_lifetime_history():
    dose_date = date(
        2026,
        4,
        1,
    )

    result = normalize(
        lifetime=history(
            [
                dose_date,
            ]
        ),
        cycle_state="documented_doses",
        events=[
            event(
                dose_date
            ),
        ],
        prior_state="documented_none",
    )

    assert result[
        "current_cycle_event_count"
    ] == 1

    assert result[
        "routine_event_count"
    ] == 1

    assert result[
        "special_event_count"
    ] == 0

    assert result[
        "safe_for_routine_child_evaluation"
    ] is True


def test_unreconciled_current_cycle_event_is_rejected():
    with pytest.raises(
        ValueError,
        match="reconcile",
    ):
        normalize(
            lifetime=history(
                [
                    date(
                        2026,
                        4,
                        1,
                    ),
                ]
            ),
            cycle_state="documented_doses",
            events=[
                event(
                    date(
                        2026,
                        4,
                        2,
                    )
                ),
            ],
            prior_state="documented_none",
        )


def test_future_cycle_event_is_rejected():
    future = date(
        2026,
        9,
        12,
    )

    with pytest.raises(
        ValueError,
        match="cannot follow assessment_date",
    ):
        normalize(
            lifetime=history(
                [
                    future,
                ]
            ),
            cycle_state="documented_doses",
            events=[
                event(
                    future
                ),
            ],
            prior_state="documented_none",
        )


def test_duplicate_cycle_event_date_is_rejected():
    dose_date = date(
        2026,
        4,
        1,
    )

    with pytest.raises(
        ValueError,
        match="duplicate influenza current-cycle",
    ):
        normalize(
            lifetime=history(
                [
                    dose_date,
                ]
            ),
            cycle_state="documented_doses",
            events=[
                event(
                    dose_date
                ),
                event(
                    dose_date
                ),
            ],
            prior_state="documented_none",
        )


def test_same_day_lifetime_ambiguity_fails_closed():
    dose_date = date(
        2026,
        4,
        1,
    )

    lifetime = schemas.PniVaccineHistory(
        vaccine_key="influenza",
        history_state="documented_doses",
        doses=[
            schemas.PniDoseRecord(
                administration_date=dose_date,
                product_key="influenza",
                documentation_source="official_registry",
            ),
            schemas.PniDoseRecord(
                administration_date=dose_date,
                product_key="influenza",
                documentation_source="vaccination_card",
            ),
        ],
    )

    result = normalize(
        lifetime=lifetime,
        cycle_state="documented_zero_dose",
        prior_state="documented_prior",
    )

    assert result[
        "ambiguous_lifetime_same_day_dates"
    ] == [
        dose_date,
    ]

    assert result[
        "safe_for_chronology_evaluation"
    ] is False

    assert result[
        "safe_for_routine_child_evaluation"
    ] is False


def test_cycle_event_against_ambiguous_same_day_lifetime_is_rejected():
    dose_date = date(
        2026,
        4,
        1,
    )

    lifetime = schemas.PniVaccineHistory(
        vaccine_key="influenza",
        history_state="documented_doses",
        doses=[
            schemas.PniDoseRecord(
                administration_date=dose_date,
                product_key="influenza",
                documentation_source="official_registry",
            ),
            schemas.PniDoseRecord(
                administration_date=dose_date,
                product_key="influenza",
                documentation_source="vaccination_card",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match="exactly one lifetime",
    ):
        normalize(
            lifetime=lifetime,
            cycle_state="documented_doses",
            events=[
                event(
                    dose_date
                ),
            ],
            prior_state="documented_none",
        )


def test_special_strategy_event_is_preserved_but_not_routine_safe():
    dose_date = date(
        2026,
        4,
        1,
    )

    result = normalize(
        lifetime=history(
            [
                dose_date,
            ]
        ),
        cycle_state="documented_doses",
        events=[
            event(
                dose_date,
                strategy="special",
            ),
        ],
        prior_state="documented_prior",
    )

    assert result[
        "special_strategy_present"
    ] is True

    assert result[
        "special_event_count"
    ] == 1

    assert result[
        "safe_for_chronology_evaluation"
    ] is True

    assert result[
        "safe_for_routine_child_evaluation"
    ] is False


def test_unknown_prior_cycle_state_fails_closed():
    result = normalize(
        prior_state="unknown",
    )

    assert result[
        "priming_history_incomplete"
    ] is True

    assert result[
        "source_history_incomplete"
    ] is True

    assert result[
        "safe_for_routine_child_evaluation"
    ] is False


@pytest.mark.parametrize(
    "cycle_state",
    [
        "unknown",
        "partial_record",
    ],
)
def test_unknown_or_partial_cycle_history_fails_closed(
    cycle_state,
):
    result = normalize(
        cycle_state=cycle_state,
        prior_state="documented_none",
    )

    assert result[
        "cycle_history_incomplete"
    ] is True

    assert result[
        "safe_for_routine_child_evaluation"
    ] is False


@pytest.mark.parametrize(
    "scope",
    [
        "partial",
        "unknown",
    ],
)
def test_partial_or_unknown_generic_scope_fails_closed(
    scope,
):
    result = normalize(
        scope=scope,
    )

    assert result[
        "generic_history_incomplete"
    ] is True

    assert result[
        "safe_for_routine_child_evaluation"
    ] is False


def test_private_or_unsupported_product_identity_fails_closed():
    dose_date = date(
        2026,
        4,
        1,
    )

    result = normalize(
        lifetime=history(
            [
                dose_date,
            ],
            product_key="influenza_quadrivalent_private",
        ),
        cycle_state="documented_doses",
        events=[
            event(
                dose_date
            ),
        ],
        prior_state="documented_prior",
    )

    assert result[
        "unsupported_product_keys"
    ] == [
        "influenza_quadrivalent_private",
    ]

    assert result[
        "safe_for_chronology_evaluation"
    ] is False

    assert result[
        "safe_for_routine_child_evaluation"
    ] is False


def test_documented_zero_cycle_cannot_contain_events():
    dose_date = date(
        2026,
        4,
        1,
    )

    with pytest.raises(
        ValueError,
        match="documented zero influenza current cycle",
    ):
        normalize(
            lifetime=history(
                [
                    dose_date,
                ]
            ),
            cycle_state="documented_zero_dose",
            events=[
                event(
                    dose_date
                ),
            ],
        )


def test_documented_cycle_doses_require_events():
    with pytest.raises(
        ValueError,
        match="require events",
    ):
        normalize(
            cycle_state="documented_doses",
        )


def test_unknown_cycle_state_cannot_assert_events():
    dose_date = date(
        2026,
        4,
        1,
    )

    with pytest.raises(
        ValueError,
        match="unknown influenza current-cycle history",
    ):
        normalize(
            lifetime=history(
                [
                    dose_date,
                ]
            ),
            cycle_state="unknown",
            events=[
                event(
                    dose_date
                ),
            ],
        )


def test_more_than_two_routine_cycle_events_fails_closed():
    dates = [
        date(
            2026,
            3,
            1,
        ),
        date(
            2026,
            4,
            1,
        ),
        date(
            2026,
            5,
            1,
        ),
    ]

    result = normalize(
        lifetime=history(
            dates
        ),
        cycle_state="documented_doses",
        events=[
            event(
                value
            )
            for value in dates
        ],
        prior_state="documented_none",
    )

    assert result[
        "excess_routine_cycle_events"
    ] is True

    assert result[
        "safe_for_routine_child_evaluation"
    ] is False


def test_normalizer_assigns_no_d1_d2_or_du_roles():
    dose_date = date(
        2026,
        4,
        1,
    )

    result = normalize(
        lifetime=history(
            [
                dose_date,
            ]
        ),
        cycle_state="documented_doses",
        events=[
            event(
                dose_date
            ),
        ],
        prior_state="documented_none",
    )

    assert result[
        "normalizer_assigns_dose_roles"
    ] is False

    serialized = repr(
        result[
            "current_cycle_events"
        ]
    ).lower()

    assert "normalized_role" not in serialized
    assert "is_booster" not in serialized
    assert "dose_code" not in serialized


def test_wrong_history_vaccine_key_is_rejected():
    wrong = schemas.PniVaccineHistory(
        vaccine_key="ipv",
        history_state="documented_zero_dose",
    )

    with pytest.raises(
        ValueError,
        match="vaccine_key influenza",
    ):
        normalize(
            lifetime=wrong
        )


def test_blank_cycle_key_is_rejected():
    with pytest.raises(
        ValueError,
        match="non-empty opaque string",
    ):
        normalize(
            cycle_key="   "
        )


def test_strategy_layer_is_closed_enum():
    dose_date = date(
        2026,
        4,
        1,
    )

    with pytest.raises(
        ValueError,
        match="strategy_layer",
    ):
        normalize(
            lifetime=history(
                [
                    dose_date,
                ]
            ),
            cycle_state="documented_doses",
            events=[
                event(
                    dose_date,
                    strategy="campaign-ish",
                ),
            ],
        )


def test_generic_schema_has_not_gained_cycle_fields():
    for model in (
        schemas.PniDoseRecord,
        schemas.PniVaccineHistory,
        schemas.PniAssessmentContext,
    ):
        fields = set(
            model.model_fields
        )

        assert not any(
            token in field.lower()
            for field in fields
            for token in (
                "influenza_cycle",
                "season_key",
                "campaign_key",
            )
        )
