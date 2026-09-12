from datetime import date
from pathlib import Path
import json

import pytest

import schemas

from clinical_tools import pni_2026
from clinical_tools.pni_history import (
    DIPHTHERIA_TOXOID,
    PERTUSSIS_ANTIGEN,
    TETANUS_TOXOID,
    TOXOID_VACCINE_COMPONENTS,
    normalize_diphtheria_tetanus_toxoid_history,
)


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


ASSESSMENT_DATE = date(
    2026,
    9,
    11,
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
    state,
    *,
    doses=None,
):
    return schemas.PniVaccineHistory(
        vaccine_key=vaccine_key,
        history_state=state,
        doses=doses or [],
    )


def normalize(
    histories,
    *,
    scope="complete",
):
    result = (
        normalize_diphtheria_tetanus_toxoid_history(
            assessment_date=ASSESSMENT_DATE,
            histories=histories,
            history_scope=scope,
        )
    )

    schemas.PniAntigenHistorySummary.model_validate(
        result
    )

    return result


def test_canonical_component_map_is_source_limited():
    assert set(
        TOXOID_VACCINE_COMPONENTS
    ) == {
        "dtpa",
        "dt",
        "dtp",
        "pentavalent",
        "hexa_acellular_rie",
    }


def test_dt_contains_diphtheria_and_tetanus_only():
    assert (
        TOXOID_VACCINE_COMPONENTS[
            "dt"
        ]
        == (
            DIPHTHERIA_TOXOID,
            TETANUS_TOXOID,
        )
    )


@pytest.mark.parametrize(
    "vaccine_key",
    [
        "dtpa",
        "dtp",
        "pentavalent",
        "hexa_acellular_rie",
    ],
)
def test_three_component_products_preserve_pertussis(
    vaccine_key,
):
    components = (
        TOXOID_VACCINE_COMPONENTS[
            vaccine_key
        ]
    )

    assert (
        DIPHTHERIA_TOXOID
        in components
    )

    assert (
        TETANUS_TOXOID
        in components
    )

    assert (
        PERTUSSIS_ANTIGEN
        in components
    )


def test_complete_reconciled_zero_history_is_explicit_zero_exposure():
    result = normalize(
        [],
        scope="complete",
    )

    assert (
        result[
            "history_state"
        ]
        == "documented_zero_exposure"
    )

    assert (
        result[
            "exposure_event_count"
        ]
        == 0
    )

    assert (
        result[
            "safe_for_interval_evaluation"
        ]
        is True
    )

    assert (
        result[
            "safe_for_basic_series_count"
        ]
        is True
    )


def test_complete_history_aggregates_across_vaccine_families():
    result = normalize([
        history(
            "pentavalent",
            "documented_doses",
            doses=[
                dose(
                    date(
                        2000,
                        1,
                        1,
                    ),
                ),
            ],
        ),
        history(
            "dtp",
            "documented_doses",
            doses=[
                dose(
                    date(
                        2001,
                        1,
                        1,
                    ),
                ),
            ],
        ),
        history(
            "dt",
            "documented_doses",
            doses=[
                dose(
                    date(
                        2020,
                        1,
                        1,
                    ),
                ),
            ],
        ),
    ])

    assert (
        result[
            "history_state"
        ]
        == "documented_exposures"
    )

    assert (
        result[
            "exposure_event_count"
        ]
        == 3
    )

    assert (
        result[
            "last_exposure_date"
        ]
        == date(
            2020,
            1,
            1,
        )
    )

    assert (
        result[
            "safe_for_basic_series_count"
        ]
        is True
    )


def test_non_toxoid_baseline_history_is_ignored():
    result = normalize([
        history(
            "hepatitis_b",
            "documented_doses",
            doses=[
                dose(
                    date(
                        2026,
                        1,
                        1,
                    ),
                ),
            ],
        ),
    ])

    assert (
        result[
            "exposure_event_count"
        ]
        == 0
    )

    assert (
        result[
            "unmapped_vaccine_keys"
        ]
        == []
    )


def test_unknown_vaccine_key_is_not_silently_classified():
    result = normalize([
        history(
            "historical_combination_unknown",
            "documented_doses",
            doses=[
                dose(
                    date(
                        2010,
                        1,
                        1,
                    ),
                ),
            ],
        ),
    ])

    assert result[
        "unmapped_vaccine_keys"
    ] == [
        "historical_combination_unknown",
    ]

    assert (
        result[
            "safe_for_interval_evaluation"
        ]
        is False
    )

    assert (
        result[
            "safe_for_basic_series_count"
        ]
        is False
    )


def test_partial_cross_vaccine_scope_is_not_safe():
    result = normalize([
        history(
            "dt",
            "documented_doses",
            doses=[
                dose(
                    date(
                        2025,
                        1,
                        1,
                    ),
                ),
            ],
        ),
    ], scope="partial")

    assert (
        result[
            "history_state"
        ]
        == "partial_record"
    )

    assert (
        result[
            "safe_for_interval_evaluation"
        ]
        is False
    )


def test_unknown_cross_vaccine_scope_remains_unknown():
    result = normalize(
        [],
        scope="unknown",
    )

    assert (
        result[
            "history_state"
        ]
        == "unknown"
    )

    assert (
        result[
            "safe_for_basic_series_count"
        ]
        is False
    )


def test_unknown_constituent_history_makes_complete_scope_unsafe():
    result = normalize([
        history(
            "dt",
            "unknown",
        ),
    ], scope="complete")

    assert (
        result[
            "source_history_incomplete"
        ]
        is True
    )

    assert (
        result[
            "safe_for_interval_evaluation"
        ]
        is False
    )


def test_partial_constituent_history_preserves_known_exposure_but_is_unsafe():
    result = normalize([
        history(
            "dt",
            "partial_record",
            doses=[
                dose(
                    date(
                        2025,
                        1,
                        1,
                    ),
                ),
            ],
            # PniVaccineHistory requires evidence for partial_record;
            # the exact dated dose provides it.
        ),
    ], scope="complete")

    assert (
        result[
            "exposure_event_count"
        ]
        == 1
    )

    assert (
        result[
            "history_state"
        ]
        == "partial_record"
    )

    assert (
        result[
            "safe_for_basic_series_count"
        ]
        is False
    )


def test_same_day_toxoid_records_are_flagged_not_deduplicated():
    same_day = date(
        2025,
        1,
        1,
    )

    result = normalize([
        history(
            "dt",
            "documented_doses",
            doses=[
                dose(
                    same_day,
                ),
            ],
        ),
        history(
            "dtpa",
            "documented_doses",
            doses=[
                dose(
                    same_day,
                ),
            ],
        ),
    ])

    assert (
        result[
            "exposure_event_count"
        ]
        == 2
    )

    assert result[
        "ambiguous_same_day_exposure_dates"
    ] == [
        same_day,
    ]

    assert (
        result[
            "safe_for_interval_evaluation"
        ]
        is False
    )


def test_exposures_are_sorted_chronologically():
    result = normalize([
        history(
            "dt",
            "documented_doses",
            doses=[
                dose(
                    date(
                        2025,
                        1,
                        1,
                    ),
                ),
                dose(
                    date(
                        2020,
                        1,
                        1,
                    ),
                ),
            ],
        ),
    ])

    dates = [
        item[
            "administration_date"
        ]
        for item
        in result[
            "exposures"
        ]
    ]

    assert dates == [
        date(
            2020,
            1,
            1,
        ),
        date(
            2025,
            1,
            1,
        ),
    ]


def test_future_toxoid_administration_is_rejected():
    with pytest.raises(
        ValueError,
        match="cannot follow assessment_date",
    ):
        normalize([
            history(
                "dt",
                "documented_doses",
                doses=[
                    dose(
                        date(
                            2026,
                            9,
                            12,
                        ),
                    ),
                ],
            ),
        ])


def test_duplicate_vaccine_history_buckets_are_rejected():
    with pytest.raises(
        ValueError,
        match="duplicate vaccine history",
    ):
        normalize([
            history(
                "dt",
                "documented_zero_dose",
            ),
            history(
                "dt",
                "documented_zero_dose",
            ),
        ])


def test_rie_hexavalent_is_visibly_special_pathway():
    result = normalize([
        history(
            "hexa_acellular_rie",
            "documented_doses",
            doses=[
                dose(
                    date(
                        2024,
                        1,
                        1,
                    ),
                ),
            ],
        ),
    ])

    assert (
        result[
            "exposures"
        ][
            0
        ][
            "special_pathway_product"
        ]
        is True
    )


def test_normalizer_does_not_apply_interval_rule():
    result = normalize([
        history(
            "dt",
            "documented_doses",
            doses=[
                dose(
                    date(
                        2026,
                        8,
                        20,
                    ),
                ),
            ],
        ),
    ])

    assert (
        "recommended_interval_days"
        not in result
    )

    assert (
        "minimum_interval_days"
        not in result
    )

    assert (
        "decision"
        not in result
    )



def test_dtpa_maternal_rule_exists_after_history_normalization():
    assert hasattr(
        pni_2026,
        "evaluate_pni_dtpa_maternal_routine",
    )

    assert not hasattr(
        pni_2026,
        "evaluate_pni_dtpa_occupational_routine",
    )



def test_source_contract_keeps_60_and_30_as_future_rule_inputs():
    source = json.loads(
        (
            ROOT
            / "data"
            / "clinical-sources"
            / "pni_2026_toxoid_history.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    clinical = source[
        "clinical_reason"
    ]

    assert (
        clinical[
            "basic_series_target_toxoid_doses"
        ]
        == 3
    )

    assert (
        clinical[
            "recommended_interval_days"
        ]
        == 60
    )

    assert (
        clinical[
            "minimum_interval_days_exceptional"
        ]
        == 30
    )

    assert (
        clinical[
            "normalizer_applies_interval_rule"
        ]
        is False
    )

    assert (
        source[
            "dtpa_rule_implemented"
        ]
        is False
    )



def test_living_governance_records_locked_normalization():
    harmonization = json.loads(
        (
            ROOT
            / "data"
            / "brazil_clinical_harmonization.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    item8 = (
        harmonization[
            "future_items"
        ][
            "8"
        ]
    )

    assert (
        item8[
            "implementation_state"
        ]
        == "rule_implementation_in_progress"
    )

    assert (
        item8[
            "implemented_rule_families"
        ]
        == [
            "vvsr",
        ]
    )

    assert (
        item8[
            "toxoid_history_normalization_state"
        ]
        == "locked"
    )

    assert (
        item8[
            "dtpa_rule_contract_state"
        ]
        == "locked"
    )

    assert (
        item8[
            "dtpa_maternal_rule_state"
        ]
        == "python_core_implemented"
    )

    assert (
        "dtpa_maternal_routine"
        in item8[
            "implemented_rule_subfamilies"
        ]
    )

    assert (
        "occupational"
        in item8[
            "deferred_rule_families"
        ][
            "dtpa"
        ]
    )



def test_document_records_fail_closed_boundary():
    document = (
        ROOT
        / "docs"
        / "PNI_2026_TOXOID_HISTORY.md"
    ).read_text(
        encoding="utf-8"
    ).lower()

    for phrase in (
        "cross-vaccine",
        "complete",
        "same-day ambiguity",
        "does not itself label the basic series complete",
        "dtpa itself remains unimplemented",
    ):
        assert (
            phrase
            in document
        )
