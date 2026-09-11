from __future__ import annotations

from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient


ROOT = Path(
    __file__
).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )


import main  # noqa: E402

from clinical_tools.methanol import (  # noqa: E402
    METHANOL_METADATA,
    calculate_brazil_methanol_context,
)


client = TestClient(
    main.app
)


def test_context_must_be_explicit_in_python():
    with pytest.raises(
        ValueError,
        match="explicit_methanol_context",
    ):
        calculate_brazil_methanol_context(
            explicit_methanol_context=False,
            sodium_mmol_l=140,
            potassium_mmol_l=4,
            chloride_mmol_l=104,
            bicarbonate_mmol_l=20,
        )


def test_ministry_anion_gap_includes_potassium():
    result = calculate_brazil_methanol_context(
        explicit_methanol_context=True,
        sodium_mmol_l=140,
        potassium_mmol_l=4,
        chloride_mmol_l=104,
        bicarbonate_mmol_l=20,
    )

    assert (
        result[
            "ministry_anion_gap_mmol_l"
        ]
        == 20.0
    )

    assert (
        result[
            "ministry_anion_gap_formula"
        ]
        == "(Na + K) - (HCO3 + Cl)"
    )

    assert (
        result[
            "ministry_anion_gap_potassium_included"
        ]
        is True
    )

    assert (
        result[
            "anion_gap_gt_12"
        ]
        is True
    )


def test_partial_methanol_ag_inputs_fail_closed():
    with pytest.raises(
        ValueError,
        match="must be supplied together",
    ):
        calculate_brazil_methanol_context(
            explicit_methanol_context=True,
            sodium_mmol_l=140,
            potassium_mmol_l=4,
            chloride_mmol_l=104,
        )


def test_osmolality_uses_explicit_mmol_glucose_and_urea():
    result = calculate_brazil_methanol_context(
        explicit_methanol_context=True,
        sodium_mmol_l=140,
        glucose_mmol_l=5,
        urea_mmol_l=5,
    )

    expected = (
        5
        + 5
        + 1.86 * 140
    ) / 0.93

    assert (
        result[
            "ministry_calculated_osmolality_mosm_kg"
        ]
        == round(
            expected,
            2,
        )
    )

    assert (
        result[
            "ministry_osmolality_input_unit"
        ]
        == "mmol/L"
    )

    assert (
        result[
            "ministry_osmolality_uses_urea_not_bun"
        ]
        is True
    )

    assert (
        result[
            "urea_bun_substitution_applied"
        ]
        is False
    )

    assert (
        result[
            "unit_domain_mixed"
        ]
        is False
    )


def test_glucose_and_urea_must_be_supplied_together():
    with pytest.raises(
        ValueError,
        match="must be supplied together",
    ):
        calculate_brazil_methanol_context(
            explicit_methanol_context=True,
            sodium_mmol_l=140,
            glucose_mmol_l=5,
        )


def test_measured_osmolality_cannot_be_used_without_formula_inputs():
    with pytest.raises(
        ValueError,
        match="Measured osmolality requires",
    ):
        calculate_brazil_methanol_context(
            explicit_methanol_context=True,
            sodium_mmol_l=140,
            measured_osmolality_mosm_kg=300,
        )


def test_osmolar_gap_is_measured_minus_calculated():
    calculated = (
        5
        + 5
        + 1.86 * 140
    ) / 0.93

    result = calculate_brazil_methanol_context(
        explicit_methanol_context=True,
        sodium_mmol_l=140,
        glucose_mmol_l=5,
        urea_mmol_l=5,
        measured_osmolality_mosm_kg=(
            calculated + 14
        ),
    )

    assert (
        result[
            "osmolar_gap_mosm_kg"
        ]
        == 14.0
    )

    assert (
        result[
            "osmolar_gap_calculation_applied"
        ]
        is True
    )

    assert (
        result[
            "osmolar_gap_gt_10"
        ]
        is True
    )

    assert (
        result[
            "osmolar_gap_gt_25"
        ]
        is False
    )


def test_osmolar_gap_thresholds_are_strictly_above():
    calculated = (
        5
        + 5
        + 1.86 * 140
    ) / 0.93

    exact_10 = calculate_brazil_methanol_context(
        explicit_methanol_context=True,
        sodium_mmol_l=140,
        glucose_mmol_l=5,
        urea_mmol_l=5,
        measured_osmolality_mosm_kg=(
            calculated + 10
        ),
    )

    exact_25 = calculate_brazil_methanol_context(
        explicit_methanol_context=True,
        sodium_mmol_l=140,
        glucose_mmol_l=5,
        urea_mmol_l=5,
        measured_osmolality_mosm_kg=(
            calculated + 25
        ),
    )

    above_25 = calculate_brazil_methanol_context(
        explicit_methanol_context=True,
        sodium_mmol_l=140,
        glucose_mmol_l=5,
        urea_mmol_l=5,
        measured_osmolality_mosm_kg=(
            calculated + 25.1
        ),
    )

    assert (
        exact_10[
            "osmolar_gap_gt_10"
        ]
        is False
    )

    assert (
        exact_25[
            "osmolar_gap_gt_25"
        ]
        is False
    )

    assert (
        above_25[
            "osmolar_gap_gt_25"
        ]
        is True
    )


def test_gap_values_never_apply_methanol_diagnosis():
    result = calculate_brazil_methanol_context(
        explicit_methanol_context=True,
        sodium_mmol_l=140,
        potassium_mmol_l=5,
        chloride_mmol_l=100,
        bicarbonate_mmol_l=10,
        glucose_mmol_l=5,
        urea_mmol_l=5,
        measured_osmolality_mosm_kg=330,
    )

    assert (
        result[
            "anion_gap_gt_12"
        ]
        is True
    )

    assert (
        result[
            "osmolar_gap_gt_25"
        ]
        is True
    )

    assert (
        result[
            "methanol_diagnosis_applied"
        ]
        is False
    )

    assert (
        result[
            "automatic_toxicology_context_inference_applied"
        ]
        is False
    )

    assert (
        result[
            "thresholds_contextual_only"
        ]
        is True
    )


def test_normal_osmolar_gap_does_not_exclude_late_poisoning():
    result = calculate_brazil_methanol_context(
        explicit_methanol_context=True,
        sodium_mmol_l=140,
        glucose_mmol_l=5,
        urea_mmol_l=5,
        measured_osmolality_mosm_kg=291,
    )

    assert (
        result[
            "normal_osmolar_gap_excludes_late_poisoning"
        ]
        is False
    )


def test_api_requires_explicit_context_literal_true():
    response = client.post(
        "/api/v1/tools/brazil-methanol",
        json={
            "sodium_mmol_l": 140,
            "potassium_mmol_l": 4,
            "chloride_mmol_l": 104,
            "bicarbonate_mmol_l": 20,
        },
    )

    assert response.status_code == 422


def test_api_matches_python_engine():
    payload = {
        "explicit_methanol_context": True,
        "sodium_mmol_l": 140,
        "potassium_mmol_l": 4,
        "chloride_mmol_l": 104,
        "bicarbonate_mmol_l": 20,
        "glucose_mmol_l": 5,
        "urea_mmol_l": 5,
        "measured_osmolality_mosm_kg": 305,
    }

    response = client.post(
        "/api/v1/tools/brazil-methanol",
        json=payload,
    )

    assert response.status_code == 200

    api = response.json()

    local = calculate_brazil_methanol_context(
        **payload
    )

    assert api == local


def test_methanol_metadata_is_context_specific_and_pending_ui():
    assert (
        METHANOL_METADATA[
            "brazil_applicability_status"
        ]
        == "complementary_brazil_guidance"
    )

    assert (
        METHANOL_METADATA[
            "final_brazil_review_status"
        ]
        == "pass"
    )

    assert (
        "urea is not BUN"
        in " ".join(
            METHANOL_METADATA[
                "limitations_en"
            ]
        )
    )


def test_methanol_metadata_api():
    response = client.get(
        "/api/v1/tools/brazil-methanol/meta"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload[
            "brazil_document_or_portaria"
        ]
        == "Nota Técnica Conjunta nº 376/2025"
    )

    assert (
        payload[
            "final_brazil_review_status"
        ]
        == "pass"
    )
