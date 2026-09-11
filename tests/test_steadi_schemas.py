from __future__ import annotations

import pytest
from pydantic import ValidationError

import schemas

from clinical_tools.steadi import (
    STEADI_CHAIR_STAND_METADATA,
    STEADI_FOUR_STAGE_METADATA,
    STEADI_ORTHOSTATIC_BP_METADATA,
    STEADI_TUG_METADATA,
    calculate_steadi_chair_stand_30s,
    calculate_steadi_four_stage_balance,
    calculate_steadi_orthostatic_bp,
    calculate_steadi_tug,
)


def test_all_four_metadata_contracts_validate():
    for metadata in (
        STEADI_TUG_METADATA,
        STEADI_CHAIR_STAND_METADATA,
        STEADI_FOUR_STAGE_METADATA,
        STEADI_ORTHOSTATIC_BP_METADATA,
    ):
        validated = (
            schemas
            .ClinicalToolMetadataResponse
            .model_validate(
                metadata
            )
        )

        assert (
            validated.brazil_applicability_status
            == "no_national_variant_identified"
        )

        assert (
            validated.final_brazil_review_status
            == "pass"
        )

        assert (
            validated.canonical_language
            == "en-US"
        )

        assert (
            validated.translation_status_en
            == "official_original"
        )

        assert (
            validated.translation_status_pt
            == "local_translation"
        )


def test_tug_typed_response_matches_core():
    result = calculate_steadi_tug(
        time_seconds=12,
        walking_aid_used=True,
        standard_3m_protocol_confirmed=True,
    )

    typed = (
        schemas.SteadiTUGResponse
        .model_validate(
            result
        )
    )

    assert typed.time_seconds == 12
    assert typed.increased_fall_risk is True
    assert typed.walking_aid_used is True


def test_tug_input_rejects_zero_time():
    with pytest.raises(
        ValidationError,
    ):
        schemas.SteadiTUGInput(
            time_seconds=0,
            walking_aid_used=False,
            standard_3m_protocol_confirmed=True,
        )


def test_chair_input_has_no_upper_age_cap():
    payload = (
        schemas.SteadiChairStand30sInput(
            age_years=125,
            sex="female",
            repetitions=1,
            arms_required_to_stand=False,
            standard_30_second_protocol_confirmed=True,
        )
    )

    assert payload.age_years == 125


def test_chair_typed_response_allows_no_classification_above_94():
    result = (
        calculate_steadi_chair_stand_30s(
            age_years=125,
            sex="female",
            repetitions=1,
            arms_required_to_stand=False,
            standard_30_second_protocol_confirmed=True,
        )
    )

    typed = (
        schemas
        .SteadiChairStand30sResponse
        .model_validate(
            result
        )
    )

    assert typed.age_years == 125

    assert (
        typed.reference_classification_available
        is False
    )

    assert typed.reference_age_band is None
    assert typed.below_average_threshold is None
    assert typed.below_average is None
    assert typed.increased_fall_risk is None
    assert typed.cutoff_extrapolated is False


def test_chair_exact_threshold_not_below_average():
    result = (
        calculate_steadi_chair_stand_30s(
            age_years=60,
            sex="male",
            repetitions=14,
            arms_required_to_stand=False,
            standard_30_second_protocol_confirmed=True,
        )
    )

    typed = (
        schemas
        .SteadiChairStand30sResponse
        .model_validate(
            result
        )
    )

    assert typed.below_average_threshold == 14
    assert typed.below_average is False
    assert typed.increased_fall_risk is False


def test_balance_optional_later_stages_support_early_stop():
    payload = (
        schemas.SteadiFourStageBalanceInput(
            side_by_side_seconds=8,
            semi_tandem_seconds=None,
            tandem_seconds=None,
            one_leg_seconds=None,
            assistive_device_used=False,
            standard_four_stage_protocol_confirmed=True,
        )
    )

    assert payload.side_by_side_seconds == 8
    assert payload.semi_tandem_seconds is None


def test_balance_schema_rejects_stage_over_10():
    with pytest.raises(
        ValidationError,
    ):
        schemas.SteadiFourStageBalanceInput(
            side_by_side_seconds=10,
            semi_tandem_seconds=10,
            tandem_seconds=10.1,
            one_leg_seconds=None,
            assistive_device_used=False,
            standard_four_stage_protocol_confirmed=True,
        )


def test_balance_typed_response_preserves_no_device_contract():
    result = (
        calculate_steadi_four_stage_balance(
            side_by_side_seconds=10,
            semi_tandem_seconds=10,
            tandem_seconds=9,
            one_leg_seconds=None,
            assistive_device_used=False,
            standard_four_stage_protocol_confirmed=True,
        )
    )

    typed = (
        schemas
        .SteadiFourStageBalanceResponse
        .model_validate(
            result
        )
    )

    assert typed.assistive_device_allowed is False
    assert typed.assistive_device_used is False
    assert typed.increased_fall_risk is True


def test_orthostatic_typed_response_preserves_5_1_3_contract():
    result = (
        calculate_steadi_orthostatic_bp(
            supine_sbp_mm_hg=130,
            supine_dbp_mm_hg=80,
            supine_pulse_bpm=70,
            standing_1m_sbp_mm_hg=110,
            standing_1m_dbp_mm_hg=80,
            standing_1m_pulse_bpm=76,
            standing_3m_sbp_mm_hg=130,
            standing_3m_dbp_mm_hg=70,
            standing_3m_pulse_bpm=74,
            lightheaded_or_dizzy=False,
            standard_5_1_3_protocol_confirmed=True,
        )
    )

    typed = (
        schemas
        .SteadiOrthostaticBPResponse
        .model_validate(
            result
        )
    )

    assert (
        typed.standing_measurement_minutes
        == (
            1,
            3,
        )
    )

    assert typed.systolic_drop_threshold_mm_hg == 20
    assert typed.diastolic_drop_threshold_mm_hg == 10

    assert (
        typed.abnormal_steadi_orthostatic_assessment
        is True
    )


def test_all_typed_responses_forbid_cross_instrument_synthesis():
    results = (
        schemas.SteadiTUGResponse.model_validate(
            calculate_steadi_tug(
                time_seconds=10,
                walking_aid_used=False,
                standard_3m_protocol_confirmed=True,
            )
        ),

        schemas.SteadiChairStand30sResponse.model_validate(
            calculate_steadi_chair_stand_30s(
                age_years=60,
                sex="male",
                repetitions=14,
                arms_required_to_stand=False,
                standard_30_second_protocol_confirmed=True,
            )
        ),

        schemas.SteadiFourStageBalanceResponse.model_validate(
            calculate_steadi_four_stage_balance(
                side_by_side_seconds=10,
                semi_tandem_seconds=10,
                tandem_seconds=10,
                one_leg_seconds=10,
                assistive_device_used=False,
                standard_four_stage_protocol_confirmed=True,
            )
        ),

        schemas.SteadiOrthostaticBPResponse.model_validate(
            calculate_steadi_orthostatic_bp(
                supine_sbp_mm_hg=130,
                supine_dbp_mm_hg=80,
                supine_pulse_bpm=70,
                standing_1m_sbp_mm_hg=125,
                standing_1m_dbp_mm_hg=77,
                standing_1m_pulse_bpm=76,
                standing_3m_sbp_mm_hg=125,
                standing_3m_dbp_mm_hg=77,
                standing_3m_pulse_bpm=74,
                lightheaded_or_dizzy=False,
                standard_5_1_3_protocol_confirmed=True,
            )
        ),
    )

    for result in results:
        assert (
            result
            .national_sus_threshold_applied
            is False
        )

        assert (
            result
            .automatic_cross_instrument_inference_applied
            is False
        )

        assert (
            result
            .synthetic_cross_instrument_score_applied
            is False
        )
