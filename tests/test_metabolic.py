from pathlib import Path
import json
import sys

import pytest
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )


import main  # noqa: E402

from clinical_tools.metabolic import (  # noqa: E402
    calculate_metabolic_toolkit,
)


client = TestClient(main.app)


VECTORS = json.loads(
    (
        ROOT
        / "tests"
        / "fixtures"
        / "metabolic_vectors.json"
    ).read_text(
        encoding="utf-8"
    )
)


def test_shared_metabolic_vectors():
    for vector in VECTORS:
        result = calculate_metabolic_toolkit(
            **vector["input"]
        )

        assert (
            result["anion_gap_meq_l"]
            == vector["anion_gap"]
        )

        assert (
            result[
                "albumin_corrected_anion_gap_meq_l"
            ]
            == vector[
                "corrected_anion_gap"
            ]
        )

        assert (
            result[
                "calculated_osmolality_mosm_kg"
            ]
            == vector["osmolality"]
        )

        assert (
            result["corrected_sodium_meq_l"]
            == vector["corrected_sodium"]
        )

        assert (
            result["delta_ratio"]
            == vector["delta_ratio"]
        )

        if "winter_expected" in vector:
            assert (
                result[
                    "winter_expected_paco2_mm_hg"
                ]
                == vector["winter_expected"]
            )

            assert (
                result[
                    "winter_compensation_status"
                ]
                == vector["winter_status"]
            )


def test_anion_gap_without_potassium():
    result = calculate_metabolic_toolkit(
        sodium_meq_l=140,
        chloride_meq_l=104,
        bicarbonate_meq_l=24,
    )

    assert result["anion_gap_meq_l"] == 12.0


def test_albumin_correction():
    result = calculate_metabolic_toolkit(
        sodium_meq_l=140,
        chloride_meq_l=106,
        bicarbonate_meq_l=24,
        albumin_g_dl=2,
    )

    assert result["anion_gap_meq_l"] == 10.0

    assert (
        result[
            "albumin_corrected_anion_gap_meq_l"
        ]
        == 15.0
    )


def test_calculated_osmolality():
    result = calculate_metabolic_toolkit(
        sodium_meq_l=140,
        glucose_mg_dl=90,
        bun_mg_dl=14,
    )

    assert (
        result[
            "calculated_osmolality_mosm_kg"
        ]
        == 290.0
    )


def test_corrected_sodium_uses_1_6_convention():
    result = calculate_metabolic_toolkit(
        sodium_meq_l=130,
        glucose_mg_dl=500,
    )

    assert (
        result["corrected_sodium_meq_l"]
        == 136.4
    )

    assert (
        result[
            "corrected_sodium_delta_meq_l"
        ]
        == 6.4
    )


def test_glucose_below_100_does_not_lower_sodium():
    result = calculate_metabolic_toolkit(
        sodium_meq_l=140,
        glucose_mg_dl=80,
    )

    assert (
        result["corrected_sodium_meq_l"]
        == 140.0
    )


def test_winter_is_gated_by_confirmed_metabolic_acidosis():
    result = calculate_metabolic_toolkit(
        sodium_meq_l=140,
        chloride_meq_l=104,
        bicarbonate_meq_l=16,
        paco2_mm_hg=32,
        metabolic_acidosis_confirmed=False,
    )

    assert (
        result["winter_analysis_applied"]
        is False
    )

    assert (
        result["winter_expected_paco2_mm_hg"]
        is None
    )


def test_winter_formula_and_range():
    result = calculate_metabolic_toolkit(
        sodium_meq_l=140,
        chloride_meq_l=104,
        bicarbonate_meq_l=16,
        paco2_mm_hg=32,
        metabolic_acidosis_confirmed=True,
    )

    assert (
        result["winter_analysis_applied"]
        is True
    )

    assert (
        result["winter_expected_paco2_mm_hg"]
        == 32.0
    )

    assert result["winter_lower_mm_hg"] == 30.0
    assert result["winter_upper_mm_hg"] == 34.0

    assert (
        result["winter_compensation_status"]
        == "within_expected"
    )


def test_winter_above_and_below_expected():
    above = calculate_metabolic_toolkit(
        sodium_meq_l=140,
        chloride_meq_l=104,
        bicarbonate_meq_l=16,
        paco2_mm_hg=38,
        metabolic_acidosis_confirmed=True,
    )

    assert (
        above["winter_compensation_status"]
        == "paco2_above_expected"
    )

    below = calculate_metabolic_toolkit(
        sodium_meq_l=140,
        chloride_meq_l=104,
        bicarbonate_meq_l=16,
        paco2_mm_hg=25,
        metabolic_acidosis_confirmed=True,
    )

    assert (
        below["winter_compensation_status"]
        == "paco2_below_expected"
    )


def test_delta_ratio_requires_confirmed_metabolic_acidosis():
    result = calculate_metabolic_toolkit(
        sodium_meq_l=140,
        chloride_meq_l=104,
        bicarbonate_meq_l=16,
        metabolic_acidosis_confirmed=False,
    )

    assert (
        result["delta_analysis_applied"]
        is False
    )

    assert result["delta_ratio"] is None


def test_delta_ratio_reference_case():
    result = calculate_metabolic_toolkit(
        sodium_meq_l=140,
        chloride_meq_l=104,
        bicarbonate_meq_l=16,
        metabolic_acidosis_confirmed=True,
    )

    assert result["anion_gap_meq_l"] == 20.0
    assert result["delta_ratio"] == 1.0

    assert (
        result["delta_interpretation_code"]
        == "compatible_with_predominant_hagma"
    )


def test_delta_ratio_uses_albumin_corrected_ag_when_available():
    result = calculate_metabolic_toolkit(
        sodium_meq_l=140,
        chloride_meq_l=108,
        bicarbonate_meq_l=16,
        albumin_g_dl=2,
        metabolic_acidosis_confirmed=True,
    )

    # Raw AG 16; corrected AG 21.
    assert result["anion_gap_meq_l"] == 16.0

    assert (
        result[
            "albumin_corrected_anion_gap_meq_l"
        ]
        == 21.0
    )

    assert (
        result["delta_ag_basis"]
        == "albumin_corrected"
    )

    assert result["delta_ratio"] == 1.12


def test_delta_not_applied_at_exact_ag_12():
    result = calculate_metabolic_toolkit(
        sodium_meq_l=140,
        chloride_meq_l=112,
        bicarbonate_meq_l=16,
        metabolic_acidosis_confirmed=True,
    )

    assert result["anion_gap_meq_l"] == 12.0

    assert (
        result["delta_analysis_applied"]
        is False
    )


def test_compensation_not_applied_at_bicarbonate_24():
    result = calculate_metabolic_toolkit(
        sodium_meq_l=140,
        chloride_meq_l=104,
        bicarbonate_meq_l=24,
        paco2_mm_hg=40,
        metabolic_acidosis_confirmed=True,
    )

    assert (
        result["winter_analysis_applied"]
        is False
    )

    assert (
        result["delta_analysis_applied"]
        is False
    )


def test_partial_anion_gap_inputs_fail_closed():
    with pytest.raises(
        ValueError,
        match="must be supplied together",
    ):
        calculate_metabolic_toolkit(
            sodium_meq_l=140,
            chloride_meq_l=104,
        )


def test_albumin_without_ag_inputs_fails_closed():
    with pytest.raises(
        ValueError,
        match="Albumin correction requires",
    ):
        calculate_metabolic_toolkit(
            sodium_meq_l=140,
            albumin_g_dl=2,
            glucose_mg_dl=100,
        )


def test_bun_without_glucose_fails_closed():
    with pytest.raises(
        ValueError,
        match="glucose_mg_dl is required",
    ):
        calculate_metabolic_toolkit(
            sodium_meq_l=140,
            bun_mg_dl=14,
        )


def test_sodium_only_has_no_calculation_path():
    with pytest.raises(
        ValueError,
        match="perform a metabolic calculation",
    ):
        calculate_metabolic_toolkit(
            sodium_meq_l=140,
        )


def test_metabolic_api_full_path():
    response = client.post(
        "/api/v1/tools/acid-base-metabolic",
        json={
            "sodium_meq_l": 140,
            "chloride_meq_l": 104,
            "bicarbonate_meq_l": 16,
            "albumin_g_dl": 4,
            "glucose_mg_dl": 500,
            "bun_mg_dl": 28,
            "paco2_mm_hg": 32,
            "metabolic_acidosis_confirmed": True,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["anion_gap_meq_l"] == 20.0
    assert payload["corrected_sodium_meq_l"] == 146.4

    assert (
        payload[
            "calculated_osmolality_mosm_kg"
        ]
        == 317.8
    )

    assert payload["delta_ratio"] == 1.0

    assert (
        payload["winter_compensation_status"]
        == "within_expected"
    )

    assert payload["interpretation_pt"]
    assert payload["interpretation_en"]


def test_metabolic_metadata_contract():
    response = client.get(
        "/api/v1/tools/acid-base-metabolic/meta"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["id"]
        == "acid-base-metabolic"
    )

    assert payload["name_pt"]
    assert payload["name_en"]

    assert payload["aliases_pt"]
    assert payload["aliases_en"]

    assert payload["limitations_pt"]
    assert payload["limitations_en"]

    assert (
        payload["offline_capable"]
        is True
    )


def test_metabolic_metadata_exposes_brazil_methanol_separation():
    response = client.get(
        "/api/v1/tools/acid-base-metabolic/meta"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload[
            "brazil_applicability_status"
        ]
        == "complementary_brazil_guidance"
    )

    assert (
        payload[
            "brazil_document_or_portaria"
        ]
        == "Nota Técnica Conjunta nº 376/2025"
    )

    assert (
        payload[
            "brazil_differs_from_international"
        ]
        is True
    )

    assert (
        payload[
            "final_brazil_review_status"
        ]
        == "pass"
    )

    assert (
        "separate"
        in payload[
            "brazil_scope_en"
        ].lower()
    )

    assert (
        "não substituem"
        in payload[
            "brazil_difference_notes_pt"
        ]
    )
