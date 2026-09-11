from __future__ import annotations

from pathlib import Path
import sys

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )


import main  # noqa: E402

from clinical_tools.renal import (  # noqa: E402
    AKI_METADATA,
    CKD_METADATA,
    EGFR_METADATA,
    calculate_egfr_ckd_epi_2021,
    classify_brazil_pcdt_ckd_context,
    classify_ckd,
)


client = TestClient(main.app)


def test_ckd_epi_2021_matches_corrected_brazilian_erratum_sign():
    result = calculate_egfr_ckd_epi_2021(
        age_years=50,
        sex="male",
        serum_creatinine=2.0,
        creatinine_unit="mg/dL",
    )

    assert (
        result["equation"]
        == "CKD-EPI creatinine 2021"
    )

    assert (
        result["race_coefficient_used"]
        is False
    )


def test_pcdt_stage_1_requires_damage_marker():
    no_marker = (
        classify_brazil_pcdt_ckd_context(
            egfr_ml_min_1_73m2=95,
            chronicity_at_least_3_months=True,
        )
    )

    assert no_marker["pcdt_stage"] is None

    marker = (
        classify_brazil_pcdt_ckd_context(
            egfr_ml_min_1_73m2=95,
            chronicity_at_least_3_months=True,
            other_kidney_damage_marker=True,
        )
    )

    assert marker["pcdt_stage"] == "1"


def test_pcdt_stage_2_requires_damage_marker():
    result = (
        classify_brazil_pcdt_ckd_context(
            egfr_ml_min_1_73m2=70,
            acr=100,
            acr_unit="mg/g",
            chronicity_at_least_3_months=True,
        )
    )

    assert result["pcdt_stage"] == "2"


def test_pcdt_gfr_stage_boundaries():
    cases = [
        (59.9, "3A"),
        (45, "3A"),
        (44.9, "3B"),
        (30, "3B"),
        (29.9, "4"),
        (15, "4"),
        (14.9, "5"),
    ]

    for egfr, expected in cases:
        result = (
            classify_brazil_pcdt_ckd_context(
                egfr_ml_min_1_73m2=egfr,
            )
        )

        assert (
            result["pcdt_stage"]
            == expected
        )


def test_pcdt_stage_5d_requires_low_egfr_and_dialysis():
    result = (
        classify_brazil_pcdt_ckd_context(
            egfr_ml_min_1_73m2=14.9,
            on_dialysis=True,
        )
    )

    assert result["pcdt_stage"] == "5D"


def test_pcdt_acr_boundaries_fail_closed_at_exact_300():
    a1 = classify_brazil_pcdt_ckd_context(
        egfr_ml_min_1_73m2=50,
        acr=29.9,
        acr_unit="mg/g",
    )

    a2 = classify_brazil_pcdt_ckd_context(
        egfr_ml_min_1_73m2=50,
        acr=30,
        acr_unit="mg/g",
    )

    upper_a2 = classify_brazil_pcdt_ckd_context(
        egfr_ml_min_1_73m2=50,
        acr=299.9,
        acr_unit="mg/g",
    )

    exact = classify_brazil_pcdt_ckd_context(
        egfr_ml_min_1_73m2=50,
        acr=300,
        acr_unit="mg/g",
    )

    a3 = classify_brazil_pcdt_ckd_context(
        egfr_ml_min_1_73m2=50,
        acr=300.1,
        acr_unit="mg/g",
    )

    assert a1["pcdt_acr_category"] == "A1"
    assert a2["pcdt_acr_category"] == "A2"
    assert upper_a2["pcdt_acr_category"] == "A2"

    assert exact["pcdt_acr_category"] is None

    assert (
        exact[
            "pcdt_acr_exact_300_ambiguous"
        ]
        is True
    )

    assert a3["pcdt_acr_category"] == "A3"


def test_international_exact_300_rule_is_preserved():
    result = classify_ckd(
        egfr_ml_min_1_73m2=50,
        acr=300,
        acr_unit="mg/g",
    )

    assert (
        result["albuminuria_category"]
        == "A2"
    )

    assert (
        result[
            "brazil_pcdt_context"
        ][
            "pcdt_acr_category"
        ]
        is None
    )

    assert (
        result[
            "brazil_pcdt_context"
        ][
            "pcdt_acr_exact_300_ambiguous"
        ]
        is True
    )


def test_pcdt_mg_mmol_category_is_not_auto_converted():
    result = (
        classify_brazil_pcdt_ckd_context(
            egfr_ml_min_1_73m2=70,
            acr=3,
            acr_unit="mg/mmol",
        )
    )

    assert (
        result[
            "pcdt_acr_category_evaluable"
        ]
        is False
    )

    assert (
        result[
            "pcdt_acr_category"
        ]
        is None
    )

    assert (
        result[
            "kidney_damage_marker_present"
        ]
        is True
    )

    assert result["pcdt_stage"] == "2"


def test_pcdt_never_uses_race_or_runs_printed_equation():
    result = (
        classify_brazil_pcdt_ckd_context(
            egfr_ml_min_1_73m2=40,
        )
    )

    assert (
        result[
            "race_or_ancestry_input_used"
        ]
        is False
    )

    assert (
        result[
            "pcdt_equation_calculation_applied"
        ]
        is False
    )

    assert (
        result[
            "pcdt_equation_status"
        ]
        == (
            "not_implemented_due_verified_"
            "source_conflict"
        )
    )


def test_ckd_api_exposes_brazil_pcdt_context():
    response = client.post(
        "/api/v1/tools/ckd-classification",
        json={
            "egfr_ml_min_1_73m2": 14.9,
            "acr": 100,
            "acr_unit": "mg/g",
            "chronicity_at_least_3_months": True,
            "other_kidney_damage_marker": False,
            "on_dialysis": True,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["gfr_category"] == "G5"

    assert (
        payload[
            "brazil_pcdt_context"
        ][
            "pcdt_stage"
        ]
        == "5D"
    )


def test_egfr_metadata_has_brazilian_consensus_provenance():
    assert (
        EGFR_METADATA[
            "brazil_applicability_status"
        ]
        == "complementary_brazil_guidance"
    )

    assert (
        EGFR_METADATA[
            "brazil_differs_from_international"
        ]
        is False
    )

    assert (
        "SBN"
        in EGFR_METADATA[
            "brazil_authority"
        ]
    )


def test_ckd_metadata_identifies_national_variant():
    assert (
        CKD_METADATA[
            "brazil_applicability_status"
        ]
        == "national_variant"
    )

    assert (
        CKD_METADATA[
            "brazil_differs_from_international"
        ]
        is True
    )

    assert (
        "11/2024"
        in CKD_METADATA[
            "brazil_document_or_portaria"
        ]
    )


def test_aki_metadata_records_ministry_alignment():
    assert (
        AKI_METADATA[
            "brazil_differs_from_international"
        ]
        is False
    )

    assert (
        "Ministério da Saúde"
        in AKI_METADATA[
            "brazil_authority"
        ]
    )


def test_all_renal_metadata_endpoints_expose_brazil_layer():
    urls = [
        "/api/v1/tools/egfr-ckd-epi-2021/meta",
        "/api/v1/tools/ckd-classification/meta",
        "/api/v1/tools/kdigo-aki/meta",
    ]

    for url in urls:
        response = client.get(url)

        assert response.status_code == 200

        payload = response.json()

        assert payload[
            "brazil_review_date"
        ] == "2026-09-11"

        assert payload[
            "final_brazil_review_status"
        ] == "pass"
