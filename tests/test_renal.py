from pathlib import Path
import json
import sys

import pytest
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


import main  # noqa: E402

from clinical_tools.renal import (  # noqa: E402
    albuminuria_category,
    calculate_egfr_ckd_epi_2021,
    calculate_kdigo_aki,
    classify_ckd,
    gfr_category,
)


client = TestClient(main.app)


VECTORS = json.loads(
    (
        ROOT
        / "tests"
        / "fixtures"
        / "renal_vectors.json"
    ).read_text(
        encoding="utf-8"
    )
)


def test_egfr_matches_nkf_verification_values():
    for vector in VECTORS[
        "egfr_nkf_verification"
    ]:
        result = (
            calculate_egfr_ckd_epi_2021(
                age_years=vector["age_years"],
                sex=vector["sex"],
                serum_creatinine=(
                    vector["serum_creatinine"]
                ),
                creatinine_unit="mg/dL",
            )
        )

        # The application contract returns one decimal.
        # Verify that representation directly rather than relying
        # on language-specific integer rounding semantics.
        assert (
            result["egfr_ml_min_1_73m2"]
            == pytest.approx(
                vector["expected_1dp"],
                abs=0.000001,
            )
        )

        # NKF Table S1 publishes whole-number verification
        # values. A correctly rounded one-decimal representation
        # must remain within half a unit of that published value.
        assert abs(
            result["egfr_ml_min_1_73m2"]
            - vector["expected_rounded"]
        ) <= 0.5


def test_egfr_si_unit_conversion_matches_mg_dl():
    mg = calculate_egfr_ckd_epi_2021(
        age_years=18,
        sex="male",
        serum_creatinine=0.9,
        creatinine_unit="mg/dL",
    )

    si = calculate_egfr_ckd_epi_2021(
        age_years=18,
        sex="male",
        serum_creatinine=79.56,
        creatinine_unit="umol/L",
    )

    assert (
        si["egfr_ml_min_1_73m2"]
        == mg["egfr_ml_min_1_73m2"]
    )


def test_egfr_has_no_race_coefficient():
    result = calculate_egfr_ckd_epi_2021(
        age_years=50,
        sex="female",
        serum_creatinine=1.0,
        creatinine_unit="mg/dL",
    )

    assert (
        result["race_coefficient_used"]
        is False
    )


@pytest.mark.parametrize(
    ("egfr", "category"),
    [
        (90, "G1"),
        (89.9, "G2"),
        (60, "G2"),
        (59.9, "G3a"),
        (45, "G3a"),
        (44.9, "G3b"),
        (30, "G3b"),
        (29.9, "G4"),
        (15, "G4"),
        (14.9, "G5"),
    ],
)
def test_kdigo_gfr_boundaries(
    egfr,
    category,
):
    assert (
        gfr_category(egfr)[0]
        == category
    )


@pytest.mark.parametrize(
    ("acr", "unit", "category"),
    [
        (29.9, "mg/g", "A1"),
        (30, "mg/g", "A2"),
        (300, "mg/g", "A2"),
        (300.1, "mg/g", "A3"),
        (2.9, "mg/mmol", "A1"),
        (3, "mg/mmol", "A2"),
        (30, "mg/mmol", "A2"),
        (30.1, "mg/mmol", "A3"),
    ],
)
def test_kdigo_albuminuria_boundaries(
    acr,
    unit,
    category,
):
    assert (
        albuminuria_category(
            acr,
            unit,
        )[0]
        == category
    )


def test_g1_a1_does_not_by_itself_establish_ckd():
    result = classify_ckd(
        egfr_ml_min_1_73m2=95,
        acr=10,
        acr_unit="mg/g",
        chronicity_at_least_3_months=True,
        other_kidney_damage_marker=False,
    )

    assert result["gfr_category"] == "G1"
    assert (
        result["albuminuria_category"]
        == "A1"
    )

    assert (
        result["ckd_status_code"]
        == "criteria_not_met_by_supplied_data"
    )


def test_g2_with_other_damage_marker_can_meet_ckd_definition():
    result = classify_ckd(
        egfr_ml_min_1_73m2=70,
        acr=10,
        acr_unit="mg/g",
        chronicity_at_least_3_months=True,
        other_kidney_damage_marker=True,
    )

    assert (
        result["ckd_status_code"]
        == "criteria_met"
    )


def test_abnormality_without_chronicity_does_not_assert_ckd():
    result = classify_ckd(
        egfr_ml_min_1_73m2=40,
        acr=100,
        acr_unit="mg/g",
        chronicity_at_least_3_months=False,
    )

    assert result["ga_classification"] == "G3b/A2"

    assert (
        result["ckd_status_code"]
        == "chronicity_not_established"
    )


def aki_base(**changes):
    payload = {
        "current_creatinine": 1.0,
        "current_creatinine_unit": "mg/dL",
    }

    payload.update(changes)

    return payload


def test_aki_stage1_by_delta_within_48h():
    result = calculate_kdigo_aki(
        **aki_base(
            current_creatinine=1.2,
            baseline_creatinine=0.9,
            baseline_interval_hours=24,
        )
    )

    assert result["stage"] == 1
    assert (
        "creatinine_delta_0_3_within_48h"
        in result["criteria_codes"]
    )


def test_aki_stage1_by_ratio_within_7_days():
    result = calculate_kdigo_aki(
        **aki_base(
            current_creatinine=1.5,
            baseline_creatinine=1.0,
            baseline_interval_hours=120,
        )
    )

    assert result["stage"] == 1


def test_aki_stage2_by_creatinine_ratio():
    result = calculate_kdigo_aki(
        **aki_base(
            current_creatinine=2.2,
            baseline_creatinine=1.0,
            baseline_interval_hours=72,
        )
    )

    assert result["stage"] == 2
    assert result["creatinine_stage"] == 2


def test_aki_stage3_by_creatinine_ratio():
    result = calculate_kdigo_aki(
        **aki_base(
            current_creatinine=3.0,
            baseline_creatinine=1.0,
            baseline_interval_hours=72,
        )
    )

    assert result["stage"] == 3


def test_aki_stage3_by_acute_rise_to_four():
    result = calculate_kdigo_aki(
        **aki_base(
            current_creatinine=4.0,
            baseline_creatinine=3.6,
            baseline_interval_hours=24,
        )
    )

    assert result["stage"] == 3
    assert (
        "creatinine_to_4_0"
        in result["criteria_codes"]
    )


def test_old_baseline_is_not_used_as_7_day_aki_baseline():
    result = calculate_kdigo_aki(
        **aki_base(
            current_creatinine=2.0,
            baseline_creatinine=1.0,
            baseline_interval_hours=200,
        )
    )

    assert result["evaluable"] is False
    assert result["stage"] is None
    assert result["aki_criteria_met"] is None


def test_aki_stage1_by_urine_output():
    result = calculate_kdigo_aki(
        **aki_base(
            weight_kg=70,
            urine_output_ml=200,
            urine_output_duration_hours=6,
        )
    )

    assert result["stage"] == 1
    assert (
        result["urine_output_ml_kg_h"]
        < 0.5
    )


def test_aki_stage2_by_urine_output():
    result = calculate_kdigo_aki(
        **aki_base(
            weight_kg=70,
            urine_output_ml=300,
            urine_output_duration_hours=12,
        )
    )

    assert result["stage"] == 2


def test_aki_stage3_by_urine_output():
    result = calculate_kdigo_aki(
        **aki_base(
            weight_kg=70,
            urine_output_ml=400,
            urine_output_duration_hours=24,
        )
    )

    assert result["stage"] == 3


def test_aki_stage3_by_anuria():
    result = calculate_kdigo_aki(
        **aki_base(
            anuria_duration_hours=12,
        )
    )

    assert result["stage"] == 3


def test_aki_stage3_by_kidney_replacement_therapy():
    result = calculate_kdigo_aki(
        **aki_base(
            renal_replacement_therapy=True,
        )
    )

    assert result["stage"] == 3
    assert result["rrt_stage"] == 3


def test_aki_uses_highest_available_stage():
    result = calculate_kdigo_aki(
        **aki_base(
            current_creatinine=1.6,
            baseline_creatinine=1.0,
            baseline_interval_hours=24,
            weight_kg=70,
            urine_output_ml=400,
            urine_output_duration_hours=24,
        )
    )

    assert result["creatinine_stage"] == 1
    assert result["urine_output_stage"] == 3
    assert result["stage"] == 3


def test_aki_partial_urine_data_fails_closed():
    with pytest.raises(
        ValueError,
        match="must be supplied together",
    ):
        calculate_kdigo_aki(
            **aki_base(
                weight_kg=70,
                urine_output_ml=100,
            )
        )


def test_aki_baseline_requires_time_window():
    with pytest.raises(
        ValueError,
        match="baseline_interval_hours",
    ):
        calculate_kdigo_aki(
            **aki_base(
                baseline_creatinine=1.0,
            )
        )


def test_renal_api_endpoints_are_bilingual():
    egfr = client.post(
        "/api/v1/tools/egfr-ckd-epi-2021",
        json={
            "age_years": 18,
            "sex": "male",
            "serum_creatinine": 0.9,
            "creatinine_unit": "mg/dL",
        },
    )

    assert egfr.status_code == 200
    assert round(
        egfr.json()["egfr_ml_min_1_73m2"]
    ) == 127

    assert egfr.json()["interpretation_pt"]
    assert egfr.json()["interpretation_en"]

    ckd = client.post(
        "/api/v1/tools/ckd-classification",
        json={
            "egfr_ml_min_1_73m2": 40,
            "acr": 100,
            "acr_unit": "mg/g",
            "chronicity_at_least_3_months": True,
        },
    )

    assert ckd.status_code == 200
    assert (
        ckd.json()["ga_classification"]
        == "G3b/A2"
    )
    assert (
        ckd.json()["ckd_status_code"]
        == "criteria_met"
    )

    aki = client.post(
        "/api/v1/tools/kdigo-aki",
        json={
            "current_creatinine": 2.0,
            "current_creatinine_unit": "mg/dL",
            "baseline_creatinine": 1.0,
            "baseline_interval_hours": 24,
        },
    )

    assert aki.status_code == 200
    assert aki.json()["stage"] == 2
    assert aki.json()["criteria_pt"]
    assert aki.json()["criteria_en"]


@pytest.mark.parametrize(
    "slug",
    [
        "egfr-ckd-epi-2021",
        "ckd-classification",
        "kdigo-aki",
    ],
)
def test_renal_metadata_contract(
    slug,
):
    response = client.get(
        f"/api/v1/tools/{slug}/meta"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["name_pt"]
    assert payload["name_en"]

    assert payload["description_pt"]
    assert payload["description_en"]

    assert payload["aliases_pt"]
    assert payload["aliases_en"]

    assert payload["source_url"].startswith(
        "https://"
    )

    assert payload["source_language"]
    assert payload["canonical_language"]

    assert payload["translation_status_pt"]
    assert payload["translation_status_en"]

    assert payload["limitations_pt"]
    assert payload["limitations_en"]

    assert payload["offline_capable"] is True


def test_aki_delta_exact_decimal_boundary_is_stage1():
    """1.2 - 0.9 must clinically satisfy the 0.3 mg/dL threshold."""
    result = calculate_kdigo_aki(
        **aki_base(
            current_creatinine=1.2,
            baseline_creatinine=0.9,
            baseline_interval_hours=24,
        )
    )

    assert result["stage"] == 1

    assert (
        "creatinine_delta_0_3_within_48h"
        in result["criteria_codes"]
    )


def test_aki_delta_genuinely_below_boundary_does_not_round_up():
    result = calculate_kdigo_aki(
        **aki_base(
            current_creatinine=1.199999,
            baseline_creatinine=0.9,
            baseline_interval_hours=24,
        )
    )

    assert result["stage"] == 0

    assert (
        "creatinine_delta_0_3_within_48h"
        not in result["criteria_codes"]
    )


def test_aki_ratio_exact_boundary_is_stage1():
    result = calculate_kdigo_aki(
        **aki_base(
            current_creatinine=1.5,
            baseline_creatinine=1.0,
            baseline_interval_hours=72,
        )
    )

    assert result["stage"] == 1


def test_aki_ratio_genuinely_below_boundary_does_not_round_up():
    result = calculate_kdigo_aki(
        **aki_base(
            current_creatinine=1.499999,
            baseline_creatinine=1.0,
            baseline_interval_hours=72,
        )
    )

    assert result["stage"] == 0


def test_urine_output_exact_half_boundary_does_not_meet_strict_less_than():
    # 210 mL / 70 kg / 6 h = exactly 0.5 mL/kg/h.
    result = calculate_kdigo_aki(
        **aki_base(
            weight_kg=70,
            urine_output_ml=210,
            urine_output_duration_hours=6,
        )
    )

    assert result["urine_output_stage"] == 0
    assert result["stage"] == 0


def test_urine_output_just_below_half_boundary_meets_stage1():
    result = calculate_kdigo_aki(
        **aki_base(
            weight_kg=70,
            urine_output_ml=209.999,
            urine_output_duration_hours=6,
        )
    )

    assert result["urine_output_stage"] == 1
    assert result["stage"] == 1


def test_urine_output_exact_point_three_boundary_is_not_stage3():
    # 504 mL / 70 kg / 24 h = exactly 0.3 mL/kg/h.
    # KDIGO stage 3 requires <0.3, not <=0.3.
    result = calculate_kdigo_aki(
        **aki_base(
            weight_kg=70,
            urine_output_ml=504,
            urine_output_duration_hours=24,
        )
    )

    assert result["urine_output_stage"] == 2
    assert result["stage"] == 2


def test_nkf_female_knot_value_preserves_one_decimal_contract():
    """NKF Table S1 reports 128; our 1-dp result is 128.5."""
    result = calculate_egfr_ckd_epi_2021(
        age_years=18,
        sex="female",
        serum_creatinine=0.70,
        creatinine_unit="mg/dL",
    )

    assert (
        result["egfr_ml_min_1_73m2"]
        == pytest.approx(
            128.5,
            abs=0.000001,
        )
    )


def test_python_and_js_rounding_must_not_define_clinical_result():
    """Document why whole-number round() is not the parity contract."""
    assert round(128.5) == 128


def test_aki_urine_output_can_stage_without_creatinine():
    result = calculate_kdigo_aki(
        weight_kg=70,
        urine_output_ml=200,
        urine_output_duration_hours=6,
    )

    assert result["stage"] == 1

    assert (
        result["current_creatinine_mg_dl"]
        is None
    )


def test_aki_anuria_can_stage_without_creatinine():
    result = calculate_kdigo_aki(
        anuria_duration_hours=12,
    )

    assert result["stage"] == 3

    assert (
        result["current_creatinine_mg_dl"]
        is None
    )


def test_aki_krt_can_stage_without_creatinine():
    result = calculate_kdigo_aki(
        renal_replacement_therapy=True,
    )

    assert result["stage"] == 3
    assert result["rrt_stage"] == 3

    assert (
        result["current_creatinine_mg_dl"]
        is None
    )


def test_aki_baseline_requires_current_creatinine():
    with pytest.raises(
        ValueError,
        match="current_creatinine",
    ):
        calculate_kdigo_aki(
            baseline_creatinine=1.0,
            baseline_interval_hours=24,
        )


def test_aki_no_criteria_is_not_evaluable():
    result = calculate_kdigo_aki()

    assert result["evaluable"] is False
    assert result["stage"] is None
    assert result["aki_criteria_met"] is None


def test_aki_api_accepts_urine_only_path():
    response = client.post(
        "/api/v1/tools/kdigo-aki",
        json={
            "weight_kg": 70,
            "urine_output_ml": 200,
            "urine_output_duration_hours": 6,
            "renal_replacement_therapy": False,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["stage"] == 1

    assert (
        payload["current_creatinine_mg_dl"]
        is None
    )


def test_shared_aki_vectors_python_parity():
    for vector in VECTORS["aki"]:
        result = calculate_kdigo_aki(
            **vector["input"]
        )

        assert (
            result["stage"]
            == vector["stage"]
        ), vector["name"]
