import pytest

from clinical_tools.falls_function import (
    CADERNETA_FALLS_ITEM_KEYS,
    calculate_caderneta_falls_checkup,
    calculate_ivcf20,
)


def _falls(**overrides):
    payload = {
        "age_years": 60,
        "fall_previous_year": False,
        "cane_or_walker_recommended": False,
        "unsteady_while_walking": False,
        "uses_furniture_for_support": False,
        "concern_about_falling": False,
        "needs_hands_to_rise_from_chair": False,
        "difficulty_stepping_onto_curb": False,
        "toilet_urgency": False,
        "reduced_foot_sensation": False,
        "medication_dizziness_or_fatigue": False,
        "sleep_or_mood_medication": False,
        "sadness_or_depressed_mood": False,
    }
    payload.update(overrides)
    return calculate_caderneta_falls_checkup(
        **payload
    )


def _ivcf(**overrides):
    payload = {
        "age_years": 60,
        "self_rated_health_regular_or_poor": False,
        "stopped_shopping_due_health": False,
        "stopped_managing_money_due_health": False,
        "stopped_housework_due_health": False,
        "stopped_bathing_due_health": False,
        "forgetfulness_noted_by_others": False,
        "worsening_forgetfulness": False,
        "forgetfulness_impairs_daily_activity": False,
        "depressed_or_hopeless_last_month": False,
        "anhedonia_last_month": False,
        "unable_raise_arms_above_shoulders": False,
        "unable_handle_small_objects": False,
        "unintentional_weight_loss_criterion": False,
        "bmi_lt_22": False,
        "calf_circumference_lt_31_cm": False,
        "gait_4m_gt_5_seconds": False,
        "walking_difficulty_impairs_daily_activity": False,
        "two_or_more_falls_last_year": False,
        "urinary_or_fecal_incontinence": False,
        "vision_impairs_daily_activity": False,
        "hearing_impairs_daily_activity": False,
        "five_or_more_chronic_conditions": False,
        "five_or_more_daily_medications": False,
        "hospitalized_last_six_months": False,
    }
    payload.update(overrides)
    return calculate_ivcf20(
        **payload
    )


def test_caderneta_has_exactly_12_items():
    assert len(
        CADERNETA_FALLS_ITEM_KEYS
    ) == 12
    assert len(
        set(CADERNETA_FALLS_ITEM_KEYS)
    ) == 12


def test_caderneta_no_positive_answer():
    result = _falls()

    assert result["positive_items_count"] == 0
    assert result["positive_items"] == []
    assert result["assessment_indicated"] is False

    assert result["any_yes_rule_applied"] is True
    assert result["weighted_score_applied"] is False
    assert result["foreign_weighted_score_imported"] is False
    assert result["fall_risk_classification_applied"] is False
    assert result["automatic_ivcf_inference_applied"] is False
    assert (
        result["synthetic_cross_instrument_score_applied"]
        is False
    )


@pytest.mark.parametrize(
    "field",
    CADERNETA_FALLS_ITEM_KEYS,
)
def test_caderneta_any_single_yes_indicates_assessment(
    field,
):
    result = _falls(
        **{
            field: True,
        }
    )

    assert result["positive_items_count"] == 1
    assert result["positive_items"] == [field]
    assert result["assessment_indicated"] is True


def test_caderneta_all_yes_is_count_not_weighted_score():
    result = _falls(
        **{
            key: True
            for key in CADERNETA_FALLS_ITEM_KEYS
        }
    )

    assert result["positive_items_count"] == 12
    assert result["assessment_indicated"] is True
    assert result["weighted_score_applied"] is False


@pytest.mark.parametrize(
    ("age", "expected"),
    (
        (60, 0),
        (74, 0),
        (75, 1),
        (84, 1),
        (85, 3),
        (120, 3),
    ),
)
def test_ivcf_age_boundaries(
    age,
    expected,
):
    result = _ivcf(
        age_years=age
    )

    assert (
        result["dimension_scores"]["age"]
        == expected
    )


def test_ivcf_zero_is_low_and_annual():
    result = _ivcf()

    assert result["total_score"] == 0
    assert result["classification_code"] == "low"
    assert result["reapplication_months_minimum"] == 12
    assert result["reapply_after_sentinel_event"] is True
    assert result["complete_assessment_required"] is True


def test_ivcf_instrumental_adl_is_capped_at_four():
    result = _ivcf(
        stopped_shopping_due_health=True,
        stopped_managing_money_due_health=True,
        stopped_housework_due_health=True,
    )

    assert (
        result["dimension_scores"]["instrumental_adl"]
        == 4
    )
    assert result["total_score"] == 4


def test_ivcf_cognition_weights_are_one_one_two():
    result = _ivcf(
        forgetfulness_noted_by_others=True,
        worsening_forgetfulness=True,
        forgetfulness_impairs_daily_activity=True,
    )

    assert (
        result["dimension_scores"]["cognition"]
        == 4
    )
    assert result["total_score"] == 4


@pytest.mark.parametrize(
    "field",
    (
        "unintentional_weight_loss_criterion",
        "bmi_lt_22",
        "calf_circumference_lt_31_cm",
        "gait_4m_gt_5_seconds",
    ),
)
def test_ivcf_any_aerobic_muscular_criterion_scores_two(
    field,
):
    result = _ivcf(
        **{
            field: True,
        }
    )

    assert (
        result["dimension_scores"][
            "aerobic_muscular_capacity"
        ]
        == 2
    )


def test_ivcf_aerobic_muscular_section_stays_capped_at_two():
    result = _ivcf(
        unintentional_weight_loss_criterion=True,
        bmi_lt_22=True,
        calf_circumference_lt_31_cm=True,
        gait_4m_gt_5_seconds=True,
    )

    assert (
        result["dimension_scores"][
            "aerobic_muscular_capacity"
        ]
        == 2
    )


@pytest.mark.parametrize(
    "field",
    (
        "five_or_more_chronic_conditions",
        "five_or_more_daily_medications",
        "hospitalized_last_six_months",
    ),
)
def test_ivcf_any_multiple_comorbidity_criterion_scores_four(
    field,
):
    result = _ivcf(
        **{
            field: True,
        }
    )

    assert (
        result["dimension_scores"][
            "multiple_comorbidities"
        ]
        == 4
    )


def test_ivcf_multiple_comorbidity_section_stays_capped_at_four():
    result = _ivcf(
        five_or_more_chronic_conditions=True,
        five_or_more_daily_medications=True,
        hospitalized_last_six_months=True,
    )

    assert (
        result["dimension_scores"][
            "multiple_comorbidities"
        ]
        == 4
    )


def test_ivcf_score_six_is_low():
    result = _ivcf(
        stopped_bathing_due_health=True,
    )

    assert result["total_score"] == 6
    assert result["classification_code"] == "low"
    assert result["reapplication_months_minimum"] == 12


def test_ivcf_score_seven_is_moderate():
    result = _ivcf(
        stopped_bathing_due_health=True,
        self_rated_health_regular_or_poor=True,
    )

    assert result["total_score"] == 7
    assert result["classification_code"] == "moderate"
    assert result["reapplication_months_minimum"] == 6


def test_ivcf_score_fourteen_is_moderate():
    result = _ivcf(
        stopped_bathing_due_health=True,
        stopped_shopping_due_health=True,
        depressed_or_hopeless_last_month=True,
        anhedonia_last_month=True,
    )

    assert result["total_score"] == 14
    assert result["classification_code"] == "moderate"


def test_ivcf_score_fifteen_is_high():
    result = _ivcf(
        stopped_bathing_due_health=True,
        stopped_shopping_due_health=True,
        depressed_or_hopeless_last_month=True,
        anhedonia_last_month=True,
        self_rated_health_regular_or_poor=True,
    )

    assert result["total_score"] == 15
    assert result["classification_code"] == "high"


def test_ivcf_all_positive_reaches_exact_maximum_40():
    result = _ivcf(
        age_years=85,
        self_rated_health_regular_or_poor=True,
        stopped_shopping_due_health=True,
        stopped_managing_money_due_health=True,
        stopped_housework_due_health=True,
        stopped_bathing_due_health=True,
        forgetfulness_noted_by_others=True,
        worsening_forgetfulness=True,
        forgetfulness_impairs_daily_activity=True,
        depressed_or_hopeless_last_month=True,
        anhedonia_last_month=True,
        unable_raise_arms_above_shoulders=True,
        unable_handle_small_objects=True,
        unintentional_weight_loss_criterion=True,
        bmi_lt_22=True,
        calf_circumference_lt_31_cm=True,
        gait_4m_gt_5_seconds=True,
        walking_difficulty_impairs_daily_activity=True,
        two_or_more_falls_last_year=True,
        urinary_or_fecal_incontinence=True,
        vision_impairs_daily_activity=True,
        hearing_impairs_daily_activity=True,
        five_or_more_chronic_conditions=True,
        five_or_more_daily_medications=True,
        hospitalized_last_six_months=True,
    )

    assert result["total_score"] == 40
    assert result["classification_code"] == "high"
    assert result["reapplication_months_minimum"] == 6


def test_ivcf_four_metre_gait_is_explicitly_not_tug():
    result = _ivcf(
        gait_4m_gt_5_seconds=True,
    )

    assert result["gait_4m_gt_5_seconds"] is True
    assert result["gait_4m_is_tug"] is False
    assert result["fall_risk_classification_applied"] is False
    assert result["automatic_caderneta_inference_applied"] is False
    assert (
        result["synthetic_cross_instrument_score_applied"]
        is False
    )


def test_brazil_older_person_tools_reject_age_below_60():
    with pytest.raises(
        ValueError,
        match="60 or greater",
    ):
        _falls(
            age_years=59
        )

    with pytest.raises(
        ValueError,
        match="60 or greater",
    ):
        _ivcf(
            age_years=59
        )


@pytest.mark.parametrize(
    "age",
    (
        121,
        125,
    ),
)
def test_ivcf_has_no_unsourced_upper_age_cap(
    age,
):
    result = _ivcf(
        age_years=age
    )

    assert result["age_years"] == age
    assert result["dimension_scores"]["age"] == 3
    assert result["total_score"] == 3
