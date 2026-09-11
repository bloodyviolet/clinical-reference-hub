import pytest

from clinical_tools.steadi import (
    CHAIR_STAND_THRESHOLDS,
    calculate_steadi_chair_stand_30s,
    calculate_steadi_four_stage_balance,
    calculate_steadi_orthostatic_bp,
    calculate_steadi_tug,
)


def _tug(
    **overrides,
):
    payload = {
        "time_seconds":
            10,
        "walking_aid_used":
            False,
        "standard_3m_protocol_confirmed":
            True,
    }

    payload.update(
        overrides
    )

    return calculate_steadi_tug(
        **payload
    )


def _chair(
    **overrides,
):
    payload = {
        "age_years":
            60,
        "sex":
            "male",
        "repetitions":
            14,
        "arms_required_to_stand":
            False,
        "standard_30_second_protocol_confirmed":
            True,
    }

    payload.update(
        overrides
    )

    return calculate_steadi_chair_stand_30s(
        **payload
    )


def _balance(
    **overrides,
):
    payload = {
        "side_by_side_seconds":
            10,
        "semi_tandem_seconds":
            10,
        "tandem_seconds":
            10,
        "one_leg_seconds":
            10,
        "assistive_device_used":
            False,
        "standard_four_stage_protocol_confirmed":
            True,
    }

    payload.update(
        overrides
    )

    return calculate_steadi_four_stage_balance(
        **payload
    )


def _ortho(
    **overrides,
):
    payload = {
        "supine_sbp_mm_hg":
            130,
        "supine_dbp_mm_hg":
            80,
        "supine_pulse_bpm":
            70,
        "standing_1m_sbp_mm_hg":
            125,
        "standing_1m_dbp_mm_hg":
            77,
        "standing_1m_pulse_bpm":
            76,
        "standing_3m_sbp_mm_hg":
            125,
        "standing_3m_dbp_mm_hg":
            77,
        "standing_3m_pulse_bpm":
            74,
        "lightheaded_or_dizzy":
            False,
        "standard_5_1_3_protocol_confirmed":
            True,
    }

    payload.update(
        overrides
    )

    return calculate_steadi_orthostatic_bp(
        **payload
    )


def test_tug_below_12_does_not_meet_increased_risk_threshold():
    result = _tug(
        time_seconds=11.99
    )

    assert result[
        "increased_fall_risk"
    ] is False

    assert result[
        "threshold_seconds"
    ] == 12

    assert result[
        "threshold_comparison"
    ] == ">="


def test_tug_exactly_12_meets_increased_risk_threshold():
    result = _tug(
        time_seconds=12
    )

    assert result[
        "increased_fall_risk"
    ] is True


def test_tug_usual_walking_aid_is_permitted():
    result = _tug(
        walking_aid_used=True
    )

    assert result[
        "walking_aid_allowed"
    ] is True

    assert result[
        "walking_aid_used"
    ] is True


def test_tug_does_not_infer_ivcf_or_national_sus_rule():
    result = _tug()

    assert result[
        "ivcf_four_meter_gait_inferred"
    ] is False

    assert result[
        "national_sus_threshold_applied"
    ] is False

    assert result[
        "automatic_cross_instrument_inference_applied"
    ] is False

    assert result[
        "synthetic_cross_instrument_score_applied"
    ] is False


def test_tug_requires_explicit_standard_protocol():
    with pytest.raises(
        ValueError,
        match="3-m / 10-ft",
    ):
        _tug(
            standard_3m_protocol_confirmed=False
        )


def test_tug_rejects_zero_time():
    with pytest.raises(
        ValueError,
        match="greater than",
    ):
        _tug(
            time_seconds=0
        )


@pytest.mark.parametrize(
    (
        "age",
        "sex",
        "threshold",
    ),
    (
        (60, "male", 14),
        (64, "female", 12),
        (65, "male", 12),
        (69, "female", 11),
        (70, "male", 12),
        (74, "female", 10),
        (75, "male", 11),
        (79, "female", 10),
        (80, "male", 10),
        (84, "female", 9),
        (85, "male", 8),
        (89, "female", 8),
        (90, "male", 7),
        (94, "female", 4),
    ),
)
def test_chair_stand_exact_reference_thresholds(
    age,
    sex,
    threshold,
):
    below = _chair(
        age_years=age,
        sex=sex,
        repetitions=threshold - 1,
    )

    exact = _chair(
        age_years=age,
        sex=sex,
        repetitions=threshold,
    )

    assert below[
        "below_average_threshold"
    ] == threshold

    assert below[
        "below_average"
    ] is True

    assert below[
        "increased_fall_risk"
    ] is True

    assert exact[
        "below_average"
    ] is False

    assert exact[
        "increased_fall_risk"
    ] is False


def test_chair_stand_reference_table_constant_is_exact():
    assert CHAIR_STAND_THRESHOLDS == {
        "60-64": {
            "minimum_age": 60,
            "maximum_age": 64,
            "male": 14,
            "female": 12,
        },
        "65-69": {
            "minimum_age": 65,
            "maximum_age": 69,
            "male": 12,
            "female": 11,
        },
        "70-74": {
            "minimum_age": 70,
            "maximum_age": 74,
            "male": 12,
            "female": 10,
        },
        "75-79": {
            "minimum_age": 75,
            "maximum_age": 79,
            "male": 11,
            "female": 10,
        },
        "80-84": {
            "minimum_age": 80,
            "maximum_age": 84,
            "male": 10,
            "female": 9,
        },
        "85-89": {
            "minimum_age": 85,
            "maximum_age": 89,
            "male": 8,
            "female": 8,
        },
        "90-94": {
            "minimum_age": 90,
            "maximum_age": 94,
            "male": 7,
            "female": 4,
        },
    }


@pytest.mark.parametrize(
    "age",
    (
        95,
        100,
        125,
    ),
)
def test_chair_stand_does_not_extrapolate_above_age_94(
    age,
):
    result = _chair(
        age_years=age,
        repetitions=1,
    )

    assert result[
        "reference_age_band"
    ] is None

    assert result[
        "below_average_threshold"
    ] is None

    assert result[
        "reference_classification_available"
    ] is False

    assert result[
        "below_average"
    ] is None

    assert result[
        "increased_fall_risk"
    ] is None

    assert result[
        "cutoff_extrapolated"
    ] is False


def test_chair_stand_arms_required_forces_recorded_zero():
    result = _chair(
        repetitions=9,
        arms_required_to_stand=True,
    )

    assert result[
        "observed_repetitions_input"
    ] == 9

    assert result[
        "test_stopped_due_to_arm_use"
    ] is True

    assert result[
        "recorded_repetitions"
    ] == 0

    assert result[
        "below_average"
    ] is True


def test_chair_stand_rejects_age_below_reference_population():
    with pytest.raises(
        ValueError,
        match="60",
    ):
        _chair(
            age_years=59
        )


@pytest.mark.parametrize(
    "sex",
    (
        "men",
        "women",
        "other",
        "",
    ),
)
def test_chair_stand_rejects_noncontract_reference_sex(
    sex,
):
    with pytest.raises(
        ValueError,
        match="male.*female",
    ):
        _chair(
            sex=sex
        )


def test_chair_stand_requires_standard_30_second_protocol():
    with pytest.raises(
        ValueError,
        match="30-second",
    ):
        _chair(
            standard_30_second_protocol_confirmed=False
        )


def test_chair_stand_never_applies_national_sus_threshold():
    result = _chair()

    assert result[
        "national_sus_threshold_applied"
    ] is False

    assert result[
        "automatic_cross_instrument_inference_applied"
    ] is False

    assert result[
        "synthetic_cross_instrument_score_applied"
    ] is False


def test_four_stage_full_tandem_10_seconds_is_not_increased_risk():
    result = _balance()

    assert result[
        "tandem_held_10_seconds"
    ] is True

    assert result[
        "increased_fall_risk"
    ] is False

    assert result[
        "last_stage_attempted"
    ] == "one_leg"


def test_four_stage_tandem_below_10_is_increased_risk():
    result = _balance(
        tandem_seconds=9.99,
        one_leg_seconds=None,
    )

    assert result[
        "tandem_held_10_seconds"
    ] is False

    assert result[
        "increased_fall_risk"
    ] is True

    assert result[
        "last_stage_attempted"
    ] == "tandem"


def test_four_stage_failure_at_easier_stage_stops_test():
    result = _balance(
        side_by_side_seconds=8,
        semi_tandem_seconds=None,
        tandem_seconds=None,
        one_leg_seconds=None,
    )

    assert result[
        "last_stage_attempted"
    ] == "side_by_side"

    assert result[
        "increased_fall_risk"
    ] is True


def test_four_stage_rejects_later_stage_after_early_failure():
    with pytest.raises(
        ValueError,
        match="Later.*positions",
    ):
        _balance(
            side_by_side_seconds=8,
            semi_tandem_seconds=4,
            tandem_seconds=None,
            one_leg_seconds=None,
        )


def test_four_stage_requires_next_stage_after_success():
    with pytest.raises(
        ValueError,
        match="semi_tandem_seconds is required",
    ):
        _balance(
            side_by_side_seconds=10,
            semi_tandem_seconds=None,
            tandem_seconds=None,
            one_leg_seconds=None,
        )


def test_four_stage_one_leg_result_does_not_change_tandem_threshold():
    result = _balance(
        one_leg_seconds=0
    )

    assert result[
        "tandem_held_10_seconds"
    ] is True

    assert result[
        "increased_fall_risk"
    ] is False


def test_four_stage_rejects_assistive_device():
    with pytest.raises(
        ValueError,
        match="does not permit.*assistive device",
    ):
        _balance(
            assistive_device_used=True
        )


def test_four_stage_rejects_stage_time_above_10():
    with pytest.raises(
        ValueError,
        match="cannot exceed",
    ):
        _balance(
            tandem_seconds=10.1
        )


def test_four_stage_requires_standard_protocol():
    with pytest.raises(
        ValueError,
        match="4-Stage Balance",
    ):
        _balance(
            standard_four_stage_protocol_confirmed=False
        )


def test_four_stage_preserves_instrument_boundaries():
    result = _balance()

    assert result[
        "assistive_device_allowed"
    ] is False

    assert result[
        "eyes_open_required"
    ] is True

    assert result[
        "national_sus_threshold_applied"
    ] is False

    assert result[
        "automatic_cross_instrument_inference_applied"
    ] is False

    assert result[
        "synthetic_cross_instrument_score_applied"
    ] is False


def test_orthostatic_normal_readings_are_not_abnormal():
    result = _ortho()

    assert result[
        "abnormal_steadi_orthostatic_assessment"
    ] is False

    assert result[
        "systolic_threshold_met"
    ] is False

    assert result[
        "diastolic_threshold_met"
    ] is False


def test_orthostatic_exact_20_systolic_drop_is_abnormal():
    result = _ortho(
        standing_1m_sbp_mm_hg=110,
    )

    assert result[
        "systolic_drop_1m_mm_hg"
    ] == 20

    assert result[
        "systolic_threshold_met"
    ] is True

    assert result[
        "abnormal_steadi_orthostatic_assessment"
    ] is True


def test_orthostatic_exact_10_diastolic_drop_is_abnormal():
    result = _ortho(
        standing_3m_dbp_mm_hg=70,
    )

    assert result[
        "diastolic_drop_3m_mm_hg"
    ] == 10

    assert result[
        "diastolic_threshold_met"
    ] is True

    assert result[
        "abnormal_steadi_orthostatic_assessment"
    ] is True


def test_orthostatic_subthreshold_drops_remain_normal():
    result = _ortho(
        standing_1m_sbp_mm_hg=110.1,
        standing_1m_dbp_mm_hg=70.1,
        standing_3m_sbp_mm_hg=110.1,
        standing_3m_dbp_mm_hg=70.1,
    )

    assert result[
        "maximum_systolic_drop_mm_hg"
    ] == pytest.approx(
        19.9
    )

    assert result[
        "maximum_diastolic_drop_mm_hg"
    ] == pytest.approx(
        9.9
    )

    assert result[
        "abnormal_steadi_orthostatic_assessment"
    ] is False


def test_orthostatic_symptoms_alone_make_assessment_abnormal():
    result = _ortho(
        lightheaded_or_dizzy=True
    )

    assert result[
        "systolic_threshold_met"
    ] is False

    assert result[
        "diastolic_threshold_met"
    ] is False

    assert result[
        "abnormal_steadi_orthostatic_assessment"
    ] is True


def test_orthostatic_uses_both_one_and_three_minute_readings():
    result = _ortho(
        standing_1m_sbp_mm_hg=125,
        standing_3m_sbp_mm_hg=105,
    )

    assert result[
        "systolic_drop_1m_mm_hg"
    ] == 5

    assert result[
        "systolic_drop_3m_mm_hg"
    ] == 25

    assert result[
        "maximum_systolic_drop_mm_hg"
    ] == 25

    assert result[
        "systolic_threshold_met"
    ] is True


def test_orthostatic_rejects_unconfirmed_timing_protocol():
    with pytest.raises(
        ValueError,
        match="5-minute.*1-minute.*3-minute",
    ):
        _ortho(
            standard_5_1_3_protocol_confirmed=False
        )


def test_orthostatic_rejects_sbp_below_dbp():
    with pytest.raises(
        ValueError,
        match="systolic blood pressure.*lower",
    ):
        _ortho(
            standing_1m_sbp_mm_hg=60,
            standing_1m_dbp_mm_hg=70,
        )


def test_orthostatic_has_no_pulse_threshold_or_falls_score():
    result = _ortho(
        standing_1m_pulse_bpm=120,
        standing_3m_pulse_bpm=50,
    )

    assert (
        "pulse_threshold"
        not in result
    )

    assert result[
        "fall_risk_classification_applied"
    ] is False

    assert result[
        "national_sus_threshold_applied"
    ] is False

    assert result[
        "automatic_cross_instrument_inference_applied"
    ] is False

    assert result[
        "synthetic_cross_instrument_score_applied"
    ] is False


@pytest.mark.parametrize(
    "calculator",
    (
        _tug,
        _chair,
        _balance,
        _ortho,
    ),
)
def test_every_steadi_engine_is_explicitly_complementary(
    calculator,
):
    result = calculator()

    assert result[
        "source_role"
    ] == "complementary_international_guidance"

    assert result[
        "national_sus_threshold_applied"
    ] is False

    assert result[
        "automatic_cross_instrument_inference_applied"
    ] is False

    assert result[
        "synthetic_cross_instrument_score_applied"
    ] is False
