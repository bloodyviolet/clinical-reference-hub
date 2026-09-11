from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )


from clinical_tools.growth import (  # noqa: E402
    _brazil_classification,
    _load_json,
    calculate_who_growth,
)


def indicator(
    result,
    name,
):
    value = result[
        "indicators"
    ][name]

    assert value is not None

    return value


@pytest.mark.parametrize(
    (
        "sex",
        "age_days",
        "weight",
        "height",
        "expected_hfa",
        "expected_wfa",
        "expected_wfh",
        "expected_bfa",
    ),
    [
        (
            "male",
            1001,
            18,
            120,
            7.31,
            2.20,
            -2.39,
            -3.01,
        ),
        (
            "female",
            1000,
            15,
            80,
            -3.50,
            0.95,
            4.13,
            4.66,
        ),
        (
            "male",
            1010,
            10,
            100,
            1.62,
            -2.76,
            -5.19,
            -5.61,
        ),
        (
            "male",
            1000,
            15,
            100,
            1.70,
            0.69,
            -0.29,
            -0.58,
        ),
    ],
)
def test_who_anthro_official_readme_vectors(
    sex,
    age_days,
    weight,
    height,
    expected_hfa,
    expected_wfa,
    expected_wfh,
    expected_bfa,
):
    result = calculate_who_growth(
        sex=sex,
        age_value=age_days,
        age_unit="days",
        weight_kg=weight,
        length_height_cm=height,
        measurement_position="height",
    )

    assert (
        indicator(
            result,
            "length_height_for_age",
        )["z_score"]
        == expected_hfa
    )

    assert (
        indicator(
            result,
            "weight_for_age",
        )["z_score"]
        == expected_wfa
    )

    assert (
        indicator(
            result,
            "weight_for_length_height",
        )["z_score"]
        == expected_wfh
    )

    assert (
        indicator(
            result,
            "bmi_for_age",
        )["z_score"]
        == expected_bfa
    )


@pytest.mark.parametrize(
    (
        "sex",
        "age_months",
        "height",
        "weight",
        "expected_hfa",
        "expected_wfa",
        "expected_bfa",
    ),
    [
        (
            "male",
            100,
            100,
            30,
            -5.04,
            0.87,
            5.03,
        ),
        (
            "female",
            110,
            90,
            40,
            -7.06,
            1.78,
            7.37,
        ),
    ],
)
def test_who_anthroplus_official_readme_vectors(
    sex,
    age_months,
    height,
    weight,
    expected_hfa,
    expected_wfa,
    expected_bfa,
):
    result = calculate_who_growth(
        sex=sex,
        age_value=age_months,
        age_unit="months",
        weight_kg=weight,
        length_height_cm=height,
        measurement_position="height",
    )

    assert (
        indicator(
            result,
            "length_height_for_age",
        )["z_score"]
        == expected_hfa
    )

    assert (
        indicator(
            result,
            "weight_for_age",
        )["z_score"]
        == expected_wfa
    )

    assert (
        indicator(
            result,
            "bmi_for_age",
        )["z_score"]
        == expected_bfa
    )


def test_who2006_median_weight_for_age_is_zero_and_percentile_50():
    table = _load_json(
        "who2006_weight_for_age.json"
    )

    row = next(
        item
        for item in table
        if (
            item["sex"] == 1
            and item["age"] == 365
        )
    )

    result = calculate_who_growth(
        sex="male",
        age_value=365,
        age_unit="days",
        weight_kg=row["m"],
    )

    wfa = indicator(
        result,
        "weight_for_age",
    )

    assert wfa["z_score"] == 0.0
    assert wfa["percentile"] == 50.0


def test_head_circumference_median_is_zero():
    table = _load_json(
        "who2006_head_circumference_for_age.json"
    )

    row = next(
        item
        for item in table
        if (
            item["sex"] == 2
            and item["age"] == 180
        )
    )

    result = calculate_who_growth(
        sex="female",
        age_value=180,
        age_unit="days",
        head_circumference_cm=row["m"],
    )

    hc = indicator(
        result,
        "head_circumference_for_age",
    )

    assert hc["z_score"] == 0.0
    assert hc["percentile"] == 50.0


def test_percentile_unavailable_outside_plus_or_minus_3():
    result = calculate_who_growth(
        sex="male",
        age_value=1001,
        age_unit="days",
        weight_kg=18,
        length_height_cm=120,
        measurement_position="height",
    )

    hfa = indicator(
        result,
        "length_height_for_age",
    )

    assert hfa["z_score"] == 7.31

    assert (
        hfa["percentile_available"]
        is False
    )

    assert hfa["percentile"] is None


def test_measurement_position_conversion_before_24_months():
    result = calculate_who_growth(
        sex="female",
        age_value=400,
        age_unit="days",
        length_height_cm=70,
        measurement_position="height",
    )

    assert (
        result[
            "measurement_adjustment_cm"
        ]
        == 0.7
    )

    assert (
        result[
            "length_height_effective_cm"
        ]
        == 70.7
    )

    assert (
        result[
            "measurement_position_effective"
        ]
        == "length"
    )


def test_measurement_position_conversion_after_24_months():
    result = calculate_who_growth(
        sex="male",
        age_value=800,
        age_unit="days",
        length_height_cm=85,
        measurement_position="length",
    )

    assert (
        result[
            "measurement_adjustment_cm"
        ]
        == -0.7
    )

    assert (
        result[
            "length_height_effective_cm"
        ]
        == 84.3
    )

    assert (
        result[
            "measurement_position_effective"
        ]
        == "height"
    )


def test_height_under_9_months_is_explicitly_flagged():
    result = calculate_who_growth(
        sex="male",
        age_value=200,
        age_unit="days",
        length_height_cm=65,
        measurement_position="height",
    )

    assert (
        result[
            "measurement_adjustment_cm"
        ]
        == 0.0
    )

    assert any(
        "menos de 9 meses"
        in warning
        for warning
        in result["warnings_pt"]
    )


def test_weight_for_length_reference_median_is_zero():
    table = _load_json(
        "who2006_weight_for_length.json"
    )

    row = next(
        item
        for item in table
        if (
            item["sex"] == 1
            and item["length"] == 70
        )
    )

    result = calculate_who_growth(
        sex="male",
        age_value=400,
        age_unit="days",
        weight_kg=row["m"],
        length_height_cm=70,
        measurement_position="length",
    )

    wfl = indicator(
        result,
        "weight_for_length_height",
    )

    assert wfl["z_score"] == 0.0


def test_2007_fractional_month_interpolation_changes_result():
    low = calculate_who_growth(
        sex="male",
        age_value=100,
        age_unit="months",
        weight_kg=30,
        length_height_cm=100,
        measurement_position="height",
    )

    fractional = calculate_who_growth(
        sex="male",
        age_value=100.5,
        age_unit="months",
        weight_kg=30,
        length_height_cm=100,
        measurement_position="height",
    )

    assert (
        indicator(
            low,
            "bmi_for_age",
        )["z_score"]
        != indicator(
            fractional,
            "bmi_for_age",
        )["z_score"]
    )


def test_no_who2007_extrapolation_at_229_months():
    result = calculate_who_growth(
        sex="female",
        age_value=229,
        age_unit="months",
        weight_kg=55,
        length_height_cm=165,
        measurement_position="height",
    )

    assert all(
        value is None
        for value
        in result[
            "indicators"
        ].values()
    )

    assert any(
        "nenhum LMS foi extrapolado"
        in warning
        for warning
        in result["warnings_pt"]
    )


def test_weight_for_age_brazil_classification_stops_at_10_years():
    result = calculate_who_growth(
        sex="male",
        age_value=120.5,
        age_unit="months",
        weight_kg=30,
    )

    wfa = indicator(
        result,
        "weight_for_age",
    )

    assert (
        wfa["classification_br"]
        is None
    )

    assert any(
        "a partir dos 10 anos"
        in warning
        for warning
        in result["warnings_pt"]
    )


def test_who2007_requires_standing_height():
    with pytest.raises(
        ValueError,
        match="standing height",
    ):
        calculate_who_growth(
            sex="female",
            age_value=100,
            age_unit="months",
            length_height_cm=140,
            measurement_position="length",
        )


def test_oedema_suppresses_weight_related_indicators():
    result = calculate_who_growth(
        sex="female",
        age_value=800,
        age_unit="days",
        weight_kg=12,
        length_height_cm=85,
        measurement_position="height",
        oedema=True,
    )

    assert (
        result[
            "indicators"
        ][
            "weight_for_age"
        ]
        is None
    )

    assert (
        result[
            "indicators"
        ][
            "weight_for_length_height"
        ]
        is None
    )

    assert (
        result[
            "indicators"
        ][
            "bmi_for_age"
        ]
        is None
    )

    assert (
        result[
            "indicators"
        ][
            "length_height_for_age"
        ]
        is not None
    )


@pytest.mark.parametrize(
    (
        "indicator_name",
        "age_months",
        "z_score",
        "expected",
    ),
    [
        (
            "bmi_for_age",
            24,
            1.00,
            "eutrophy",
        ),
        (
            "bmi_for_age",
            24,
            1.01,
            "risk_overweight",
        ),
        (
            "bmi_for_age",
            24,
            2.00,
            "risk_overweight",
        ),
        (
            "bmi_for_age",
            24,
            2.01,
            "overweight",
        ),
        (
            "bmi_for_age",
            24,
            3.00,
            "overweight",
        ),
        (
            "bmi_for_age",
            24,
            3.01,
            "obesity",
        ),
        (
            "bmi_for_age",
            80,
            1.00,
            "eutrophy",
        ),
        (
            "bmi_for_age",
            80,
            1.01,
            "overweight",
        ),
        (
            "bmi_for_age",
            80,
            2.01,
            "obesity",
        ),
        (
            "bmi_for_age",
            80,
            3.01,
            "severe_obesity",
        ),
        (
            "weight_for_age",
            48,
            -3.01,
            "very_low_weight",
        ),
        (
            "weight_for_age",
            48,
            -3.00,
            "low_weight",
        ),
        (
            "weight_for_age",
            48,
            -2.00,
            "adequate_weight",
        ),
        (
            "weight_for_age",
            48,
            2.01,
            "high_weight",
        ),
    ],
)
def test_brazil_sisvan_classification_boundaries(
    indicator_name,
    age_months,
    z_score,
    expected,
):
    classification = (
        _brazil_classification(
            indicator=indicator_name,
            age_months=age_months,
            z_score=z_score,
        )
    )

    assert classification is not None

    assert (
        classification["code"]
        == expected
    )


def test_head_circumference_brazil_monitoring_context():
    table = _load_json(
        "who2006_head_circumference_for_age.json"
    )

    row = next(
        item
        for item in table
        if (
            item["sex"] == 1
            and item["age"] == 800
        )
    )

    result = calculate_who_growth(
        sex="male",
        age_value=800,
        age_unit="days",
        head_circumference_cm=row["m"],
    )

    hc = indicator(
        result,
        "head_circumference_for_age",
    )

    assert (
        hc[
            "brazil_routine_monitoring_applicable"
        ]
        is False
    )


def test_corrected_age_basis_is_explicit():
    result = calculate_who_growth(
        sex="female",
        age_value=300,
        age_unit="days",
        age_basis="corrected",
        weight_kg=8,
    )

    assert (
        result["age_basis"]
        == "corrected"
    )

    assert any(
        "idade corrigida"
        in warning.lower()
        for warning
        in result["warnings_pt"]
    )


def test_reference_provenance_is_pinned():
    result = calculate_who_growth(
        sex="male",
        age_value=365,
        age_unit="days",
        weight_kg=10,
    )

    assert (
        result[
            "provenance"
        ][
            "who2006_commit"
        ]
        == (
            "b776d8a12b1c97369c748b561159fd2ec4f4db58"
        )
    )

    assert (
        result[
            "provenance"
        ][
            "who2007_commit"
        ]
        == (
            "7cfcdb39026e9a55de55732bc3cf14c82261bcf7"
        )
    )


def test_brazil_prematurity_policy_is_specific():
    policy = json.loads(
        (
            ROOT
            / "assets"
            / "reference"
            / "who-growth"
            / "BRAZIL_SISVAN.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    prematurity = policy[
        "prematurity"
    ]

    assert (
        prematurity[
            "specific_duration_guidance"
        ][
            "head_circumference"
        ]
        == (
            "use corrected age through "
            "18 months"
        )
    )

    assert (
        prematurity[
            "specific_duration_guidance"
        ][
            "weight"
        ]
        == (
            "use corrected age through "
            "24 months"
        )
    )


@pytest.mark.parametrize(
    (
        "indicator_name",
        "age_months",
        "z_score",
        "expected",
    ),
    [
        (
            "weight_for_age",
            24,
            -3.01,
            "severely_underweight",
        ),
        (
            "weight_for_age",
            24,
            -3.00,
            "underweight",
        ),
        (
            "weight_for_age",
            24,
            -2.00,
            None,
        ),
        (
            "length_height_for_age",
            48,
            -3.01,
            "severely_stunted",
        ),
        (
            "length_height_for_age",
            48,
            -2.01,
            "stunted",
        ),
        (
            "bmi_for_age",
            24,
            1.00,
            None,
        ),
        (
            "bmi_for_age",
            24,
            1.01,
            "possible_risk_overweight",
        ),
        (
            "bmi_for_age",
            24,
            2.01,
            "overweight",
        ),
        (
            "bmi_for_age",
            24,
            3.01,
            "obesity",
        ),
        (
            "bmi_for_age",
            100,
            -3.01,
            "severe_thinness",
        ),
        (
            "bmi_for_age",
            100,
            -2.01,
            "thinness",
        ),
        (
            "bmi_for_age",
            100,
            1.01,
            "overweight",
        ),
        (
            "bmi_for_age",
            100,
            2.01,
            "obesity",
        ),
    ],
)
def test_who_named_classification_boundaries(
    indicator_name,
    age_months,
    z_score,
    expected,
):
    from clinical_tools.growth import (
        _who_classification,
    )

    result = _who_classification(
        indicator=indicator_name,
        age_months=age_months,
        z_score=z_score,
    )

    if expected is None:
        assert result is None
    else:
        assert result is not None
        assert result["code"] == expected


def test_growth_requires_anthropometric_measurement():
    with pytest.raises(
        ValueError,
        match="At least one anthropometric",
    ):
        calculate_who_growth(
            sex="male",
            age_value=12,
            age_unit="months",
        )


def test_result_exposes_who_and_brazil_layers_separately():
    result = calculate_who_growth(
        sex="male",
        age_value=1001,
        age_unit="days",
        weight_kg=18,
        length_height_cm=120,
        measurement_position="height",
    )

    wfh = indicator(
        result,
        "weight_for_length_height",
    )

    assert (
        wfh[
            "classification_who"
        ][
            "code"
        ]
        == "wasted"
    )

    assert (
        wfh[
            "classification_br"
        ][
            "code"
        ]
        == "thinness"
    )
