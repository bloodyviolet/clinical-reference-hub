from datetime import date

import pytest

import schemas

from clinical_tools.pni_history import (
    normalize_diphtheria_tetanus_toxoid_history,
    normalize_polio_history,
)


ASSESSMENT = date(
    2026,
    9,
    11,
)


def history(
    key,
    state,
    *,
    dates=None,
    reported_prior=0,
):
    return schemas.PniVaccineHistory(
        vaccine_key=key,
        history_state=state,
        doses=[
            schemas.PniDoseRecord(
                administration_date=value,
                product_key=key,
                documentation_source="official_registry",
            )
            for value in (
                dates
                or []
            )
        ],
        reported_prior_doses_without_exact_dates=reported_prior,
    )


def normalize(
    histories,
    *,
    scope="complete",
):
    return normalize_polio_history(
        assessment_date=ASSESSMENT,
        histories=histories,
        history_scope=scope,
    )


def test_documented_zero_ipv_is_safe_zero_exposure():
    result = normalize(
        [
            history(
                "ipv",
                "documented_zero_dose",
            ),
            history(
                "opv_bivalent_legacy",
                "documented_zero_dose",
            ),
        ]
    )

    assert result[
        "history_state"
    ] == "documented_zero_exposure"

    assert result[
        "exposure_event_count"
    ] == 0

    assert result[
        "safe_for_primary_series_count"
    ] is True

    assert result[
        "legacy_vopb_history_supplied"
    ] is True


def test_ipv_exposure_is_ipv_equivalent():
    result = normalize(
        [
            history(
                "ipv",
                "documented_doses",
                dates=[
                    date(
                        2026,
                        3,
                        1,
                    ),
                ],
            ),
        ]
    )

    assert result[
        "ipv_equivalent_exposure_count"
    ] == 1

    assert result[
        "legacy_vopb_exposure_count"
    ] == 0

    exposure = result[
        "exposures"
    ][
        0
    ]

    assert exposure[
        "source_vaccine_key"
    ] == "ipv"

    assert exposure[
        "contains_ipv"
    ] is True

    assert exposure[
        "legacy_oral"
    ] is False


def test_legacy_vopb_preserves_transition_identity():
    result = normalize(
        [
            history(
                "opv_bivalent_legacy",
                "documented_doses",
                dates=[
                    date(
                        2024,
                        8,
                        1,
                    ),
                ],
            ),
        ]
    )

    assert result[
        "ipv_equivalent_exposure_count"
    ] == 0

    assert result[
        "legacy_vopb_exposure_count"
    ] == 1

    exposure = result[
        "exposures"
    ][
        0
    ]

    assert exposure[
        "legacy_oral"
    ] is True

    assert exposure[
        "exposure_class"
    ] == "legacy_vopb"


@pytest.mark.parametrize(
    "key",
    [
        "penta_acellular_ipv",
        "tetra_acellular_ipv",
        "hexa_acellular_ipv",
    ],
)
def test_supported_acellular_combination_is_ipv_equivalent(
    key,
):
    result = normalize(
        [
            history(
                key,
                "documented_doses",
                dates=[
                    date(
                        2025,
                        3,
                        1,
                    ),
                ],
            ),
        ]
    )

    assert result[
        "ipv_equivalent_exposure_count"
    ] == 1

    assert result[
        "legacy_vopb_exposure_count"
    ] == 0

    assert result[
        "special_pathway_exposure_present"
    ] is False


def test_existing_rie_hexavalent_is_visible_special_pathway():
    result = normalize(
        [
            history(
                "hexa_acellular_rie",
                "documented_doses",
                dates=[
                    date(
                        2025,
                        3,
                        1,
                    ),
                ],
            ),
        ]
    )

    assert result[
        "ipv_equivalent_exposure_count"
    ] == 1

    assert result[
        "special_pathway_exposure_present"
    ] is True

    assert result[
        "safe_for_interval_evaluation"
    ] is True

    assert result[
        "safe_for_transition_evaluation"
    ] is False


def test_mixed_ipv_and_vop_history_preserves_both_classes():
    result = normalize(
        [
            history(
                "ipv",
                "documented_doses",
                dates=[
                    date(2023, 3, 1),
                    date(2023, 5, 1),
                    date(2023, 7, 1),
                ],
            ),
            history(
                "opv_bivalent_legacy",
                "documented_doses",
                dates=[
                    date(
                        2024,
                        8,
                        1,
                    ),
                ],
            ),
        ]
    )

    assert result[
        "ipv_equivalent_exposure_count"
    ] == 3

    assert result[
        "legacy_vopb_exposure_count"
    ] == 1

    assert result[
        "legacy_vopb_history_supplied"
    ] is True

    assert result[
        "safe_for_transition_evaluation"
    ] is True


def test_present_history_keys_expose_legacy_reconciliation_state():
    result = normalize(
        [
            history(
                "ipv",
                "documented_zero_dose",
            ),
        ]
    )

    assert result[
        "ipv_history_supplied"
    ] is True

    assert result[
        "legacy_vopb_history_supplied"
    ] is False

    assert result[
        "present_history_keys"
    ] == [
        "ipv",
    ]


def test_unknown_relevant_history_is_not_safe():
    result = normalize(
        [
            history(
                "ipv",
                "unknown",
            ),
        ]
    )

    assert result[
        "source_history_incomplete"
    ] is True

    assert result[
        "safe_for_primary_series_count"
    ] is False

    assert result[
        "history_state"
    ] == "partial_or_uncertain"


def test_partial_undated_relevant_history_is_not_safe():
    result = normalize(
        [
            history(
                "opv_bivalent_legacy",
                "partial_record",
                reported_prior=1,
            ),
        ]
    )

    assert result[
        "source_history_incomplete"
    ] is True

    assert result[
        "safe_for_transition_evaluation"
    ] is False


def test_partial_global_scope_is_not_safe():
    result = normalize(
        [
            history(
                "ipv",
                "documented_zero_dose",
            ),
        ],
        scope="partial",
    )

    assert result[
        "safe_for_primary_series_count"
    ] is False

    assert result[
        "history_state"
    ] == "partial_or_uncertain"


def test_unknown_global_scope_is_unknown():
    result = normalize(
        [],
        scope="unknown",
    )

    assert result[
        "history_state"
    ] == "unknown"

    assert result[
        "safe_for_interval_evaluation"
    ] is False


def test_known_unrelated_vaccine_is_ignored():
    result = normalize(
        [
            history(
                "hepatitis_a",
                "documented_zero_dose",
            ),
            history(
                "ipv",
                "documented_zero_dose",
            ),
        ]
    )

    assert result[
        "unmapped_vaccine_keys"
    ] == []

    assert result[
        "safe_for_primary_series_count"
    ] is True


def test_unknown_extra_vaccine_key_fails_closed():
    result = normalize(
        [
            history(
                "ipv",
                "documented_zero_dose",
            ),
            history(
                "mystery_polio_product",
                "documented_zero_dose",
            ),
        ]
    )

    assert result[
        "unmapped_vaccine_keys"
    ] == [
        "mystery_polio_product",
    ]

    assert result[
        "safe_for_primary_series_count"
    ] is False


def test_same_day_cross_history_exposures_are_ambiguous():
    same_day = date(
        2025,
        3,
        1,
    )

    result = normalize(
        [
            history(
                "ipv",
                "documented_doses",
                dates=[
                    same_day,
                ],
            ),
            history(
                "penta_acellular_ipv",
                "documented_doses",
                dates=[
                    same_day,
                ],
            ),
        ]
    )

    assert result[
        "ambiguous_same_day_exposure_dates"
    ] == [
        same_day,
    ]

    assert result[
        "safe_for_primary_series_count"
    ] is False


def test_duplicate_history_key_rejected():
    with pytest.raises(
        ValueError,
        match="duplicate vaccine history entries",
    ):
        normalize_polio_history(
            assessment_date=ASSESSMENT,
            histories=[
                history(
                    "ipv",
                    "documented_zero_dose",
                ),
                history(
                    "ipv",
                    "documented_zero_dose",
                ),
            ],
            history_scope="complete",
        )


def test_future_polio_dose_rejected():
    with pytest.raises(
        ValueError,
        match="cannot follow assessment_date",
    ):
        normalize(
            [
                history(
                    "ipv",
                    "documented_doses",
                    dates=[
                        date(
                            2026,
                            9,
                            12,
                        ),
                    ],
                ),
            ]
        )


def test_cross_labeled_product_identity_rejected():
    bad = schemas.PniVaccineHistory(
        vaccine_key="ipv",
        history_state="documented_doses",
        doses=[
            schemas.PniDoseRecord(
                administration_date=date(
                    2025,
                    3,
                    1,
                ),
                product_key="opv_bivalent_legacy",
                documentation_source="official_registry",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match="incompatible product_key",
    ):
        normalize(
            [
                bad,
            ]
        )


@pytest.mark.parametrize(
    "key",
    [
        "penta_acellular_ipv",
        "tetra_acellular_ipv",
        "hexa_acellular_ipv",
    ],
)
def test_new_acellular_ipv_products_are_polio_only_and_toxoid_fails_closed(
    key,
):
    polio = normalize_polio_history(
        assessment_date=ASSESSMENT,
        histories=[
            history(
                key,
                "documented_doses",
                dates=[
                    date(
                        2025,
                        3,
                        1,
                    ),
                ],
            ),
        ],
        history_scope="complete",
    )

    assert polio[
        "ipv_equivalent_exposure_count"
    ] == 1

    assert polio[
        "safe_for_primary_series_count"
    ] is True

    toxoid = normalize_diphtheria_tetanus_toxoid_history(
        assessment_date=ASSESSMENT,
        histories=[
            history(
                key,
                "documented_doses",
                dates=[
                    date(
                        2025,
                        3,
                        1,
                    ),
                ],
            ),
        ],
        history_scope="complete",
    )

    assert toxoid[
        "exposure_event_count"
    ] == 0

    assert toxoid[
        "unmapped_vaccine_keys"
    ] == [
        key,
    ]

    assert toxoid[
        "safe_for_interval_evaluation"
    ] is False

    assert toxoid[
        "safe_for_basic_series_count"
    ] is False


def test_legacy_vopb_is_known_non_toxoid_not_unmapped():
    toxoid = normalize_diphtheria_tetanus_toxoid_history(
        assessment_date=ASSESSMENT,
        histories=[
            history(
                "opv_bivalent_legacy",
                "documented_doses",
                dates=[
                    date(
                        2024,
                        8,
                        1,
                    ),
                ],
            ),
        ],
        history_scope="complete",
    )

    assert toxoid[
        "exposure_event_count"
    ] == 0

    assert toxoid[
        "unmapped_vaccine_keys"
    ] == []

    assert toxoid[
        "safe_for_interval_evaluation"
    ] is True
