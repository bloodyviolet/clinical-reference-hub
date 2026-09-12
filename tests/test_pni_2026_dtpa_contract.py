from datetime import date
from pathlib import Path
import json

import pytest
from pydantic import ValidationError

import schemas

from clinical_tools import pni_2026
from clinical_tools.pni_history import (
    normalize_diphtheria_tetanus_toxoid_history,
)


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


CONTRACT_PATH = (
    ROOT
    / "data"
    / "clinical-sources"
    / "pni_2026_dtpa_maternal_contract.json"
)


HARMONIZATION_PATH = (
    ROOT
    / "data"
    / "brazil_clinical_harmonization.json"
)


DOC_PATH = (
    ROOT
    / "docs"
    / "PNI_2026_DTPA_MATERNAL_CONTRACT.md"
)


def contract():
    return json.loads(
        CONTRACT_PATH.read_text(
            encoding="utf-8"
        )
    )



def test_contract_is_locked_and_maternal_engine_is_implemented():
    data = contract()

    assert (
        data[
            "contract_status"
        ]
        == "locked_engine_implemented_maternal_only"
    )

    assert (
        data[
            "engine_implemented"
        ]
        is True
    )

    assert (
        data[
            "implementation_scope"
        ]
        == "maternal_pregnancy_and_postpartum_only"
    )

    assert (
        data[
            "occupational_dtpa_branches_implemented"
        ]
        is False
    )

    assert hasattr(
        pni_2026,
        "evaluate_pni_dtpa_maternal_routine",
    )



def test_pregnancy_rule_starts_at_week_20_each_pregnancy():
    rule = contract()[
        "pregnancy_rule"
    ]

    assert (
        rule[
            "minimum_gestational_week"
        ]
        == 20
    )

    assert (
        rule[
            "dose_each_pregnancy"
        ]
        == 1
    )

    assert (
        rule[
            "current_pregnancy_identity_required_for_repeat_suppression"
        ]
        is True
    )


def test_postpartum_rule_is_bounded_to_45_days_if_missed():
    rule = contract()[
        "postpartum_rule"
    ]

    assert (
        rule[
            "eligible_only_if_missed_during_pregnancy"
        ]
        is True
    )

    assert (
        rule[
            "maximum_postpartum_days"
        ]
        == 45
    )

    assert (
        rule[
            "recent_pregnancy_identity_required"
        ]
        is True
    )


def test_basic_series_target_is_three_dt_toxoid_exposures():
    rule = contract()[
        "basic_series_rule"
    ]

    assert (
        rule[
            "target_dt_toxoid_exposures"
        ]
        == 3
    )


def test_interval_contract_preserves_60_vs_30():
    interval = contract()[
        "interval_rule"
    ]

    assert (
        interval[
            "recommended_days"
        ]
        == 60
    )

    assert (
        interval[
            "exceptional_minimum_days"
        ]
        == 30
    )

    assert (
        interval[
            "exceptional_minimum_is_routine"
        ]
        is False
    )

    assert (
        interval[
            "exceptional_minimum_requires_explicit_authorization"
        ]
        is True
    )

    assert (
        interval[
            "exceptional_minimum_requires_risk_benefit_assessment"
        ]
        is True
    )


def test_early_current_pregnancy_dtpa_does_not_invent_repeat_rule():
    rule = contract()[
        "prior_current_pregnancy_dtpa_rule"
    ]

    assert (
        rule[
            "dose_before_week_20_repeat_rule_found_in_reviewed_source"
        ]
        is False
    )

    assert (
        rule[
            "dose_before_week_20_action"
        ]
        == "special_pathway_review"
    )

    assert (
        rule[
            "missing_gestational_age_at_administration_action"
        ]
        == "context_required"
    )


def test_dtpa_history_gate_requires_both_safe_flags():
    gate = contract()[
        "history_gate"
    ]

    assert (
        gate[
            "requires_safe_for_interval_evaluation"
        ]
        is True
    )

    assert (
        gate[
            "requires_safe_for_basic_series_count"
        ]
        is True
    )

    assert (
        gate[
            "partial_history_action"
        ]
        == "history_required"
    )


def test_calendar_due_is_not_administration_safety_clearance():
    safety = contract()[
        "administration_safety_boundary"
    ]

    assert (
        safety[
            "calendar_due_means_safe_to_administer"
        ]
        is False
    )

    assert (
        safety[
            "safety_screen_required_before_automatic_recommend_now"
        ]
        is True
    )

    assert safety[
        "safety_screen_states"
    ] == [
        "not_screened",
        "screened_no_concern",
        "screened_concern",
    ]

    assert (
        safety[
            "not_screened_action"
        ]
        == "context_required"
    )

    assert (
        safety[
            "screened_concern_action"
        ]
        == "special_pathway_review"
    )


def test_dose_can_preserve_gestational_age_at_administration():
    record = schemas.PniDoseRecord(
        administration_date=date(
            2026,
            8,
            1,
        ),
        gestational_age_weeks_at_administration=22,
        pregnancy_episode_key="P1",
        product_key="dtpa",
        documentation_source="official_registry",
    )

    assert (
        record.gestational_age_weeks_at_administration
        == 22
    )


def test_dose_rejects_impossible_gestational_week():
    with pytest.raises(
        ValidationError,
    ):
        schemas.PniDoseRecord(
            administration_date=date(
                2026,
                8,
                1,
            ),
            gestational_age_weeks_at_administration=46,
            pregnancy_episode_key="P1",
            product_key="dtpa",
            documentation_source="official_registry",
        )


def test_toxoid_normalizer_carries_gestational_age_provenance():
    history = schemas.PniVaccineHistory(
        vaccine_key="dtpa",
        history_state="documented_doses",
        doses=[
            schemas.PniDoseRecord(
                administration_date=date(
                    2026,
                    8,
                    1,
                ),
                gestational_age_weeks_at_administration=22,
                pregnancy_episode_key="P1",
                product_key="dtpa",
                documentation_source="official_registry",
            ),
        ],
    )

    result = (
        normalize_diphtheria_tetanus_toxoid_history(
            assessment_date=date(
                2026,
                9,
                11,
            ),
            histories=[
                history,
            ],
            history_scope="complete",
        )
    )

    validated = (
        schemas
        .PniAntigenHistorySummary
        .model_validate(
            result
        )
    )

    assert (
        validated.exposures[
            0
        ].gestational_age_weeks_at_administration
        == 22
    )


def test_postpartum_episode_key_requires_postpartum_context():
    with pytest.raises(
        ValidationError,
        match="requires postpartum_days",
    ):
        schemas.PniAssessmentContext(
            assessment_date=date(
                2026,
                9,
                11,
            ),
            date_of_birth=date(
                1990,
                1,
                1,
            ),
            pregnancy_status="not_pregnant",
            postpartum_pregnancy_episode_key="P1",
        )


def test_postpartum_episode_key_is_valid_with_postpartum_days():
    result = schemas.PniAssessmentContext(
        assessment_date=date(
            2026,
            9,
            11,
        ),
        date_of_birth=date(
            1990,
            1,
            1,
        ),
        pregnancy_status="not_pregnant",
        postpartum_days=10,
        postpartum_pregnancy_episode_key="P1",
    )

    assert (
        result.postpartum_pregnancy_episode_key
        == "P1"
    )


def test_postpartum_episode_key_cannot_coexist_with_active_pregnancy():
    with pytest.raises(
        ValidationError,
        match="pregnancy and postpartum context cannot coexist",
    ):
        schemas.PniAssessmentContext(
            assessment_date=date(
                2026,
                9,
                11,
            ),
            date_of_birth=date(
                1990,
                1,
                1,
            ),
            pregnancy_status="pregnant",
            gestational_age_weeks=30,
            postpartum_days=10,
            postpartum_pregnancy_episode_key="P1",
        )


def test_simultaneous_vaccine_boundary_does_not_invent_general_spacing():
    boundary = contract()[
        "simultaneous_vaccine_boundary"
    ]

    assert (
        boundary[
            "interval_with_other_non_dt_toxoid_vaccines_required"
        ]
        is False
    )

    assert (
        boundary[
            "dt_toxoid_interval_logic_is_not_a_general_vaccine_spacing_rule"
        ]
        is True
    )



def test_living_governance_records_partial_dtpa_implementation():
    data = json.loads(
        HARMONIZATION_PATH.read_text(
            encoding="utf-8"
        )
    )

    item8 = data[
        "future_items"
    ][
        "8"
    ]

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

    # Whole-family completion is intentionally NOT claimed.
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
            "partial_rule_families"
        ][
            "dtpa"
        ]
        == [
            "maternal_routine",
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

    assert (
        item8[
            "dtpa_exceptional_minimum_interval_may_be_inferred"
        ]
        is False
    )

    assert (
        item8[
            "dtpa_calendar_due_equals_safe_to_administer"
        ]
        is False
    )



def test_contract_document_records_safety_boundaries():
    document = DOC_PATH.read_text(
        encoding="utf-8"
    ).lower()

    for phrase in (
        "60 days",
        "thirty days is an exceptional minimum",
        "special_pathway_review",
        "postpartum",
        "calendar-due is not equivalent",
        "does not diagnose contraindications",
    ):
        assert (
            phrase
            in document
        )
