from datetime import date
from pathlib import Path
import json

import pytest
from pydantic import ValidationError

import schemas

from clinical_tools import pni_2026


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


SOURCE_PATH = (
    ROOT
    / "data"
    / "clinical-sources"
    / "pni_2026_bcg_model_gap_remediation.json"
)


GENERAL_GAP_PATH = (
    ROOT
    / "data"
    / "clinical-sources"
    / "pni_2026_model_gap_remediation.json"
)


GOV_PATH = (
    ROOT
    / "data"
    / "brazil_clinical_harmonization.json"
)


DOC_PATH = (
    ROOT
    / "docs"
    / "PNI_2026_BCG_MODEL_GAP_REMEDIATION.md"
)


def base_context(
    **kwargs,
):
    values = {
        "assessment_date":
            date(
                2026,
                9,
                11,
            ),

        "date_of_birth":
            date(
                2026,
                9,
                1,
            ),
    }

    values.update(
        kwargs
    )

    return schemas.PniAssessmentContext(
        **values
    )


def test_current_weight_field_exists_in_pni_context():
    assert (
        "current_weight_grams"
        in schemas
        .PniAssessmentContext
        .model_fields
    )


def test_birth_and_current_weight_are_distinct_facts():
    result = base_context(
        birth_weight_grams=1700,
        current_weight_grams=2300,
    )

    assert (
        result.birth_weight_grams
        == 1700
    )

    assert (
        result.current_weight_grams
        == 2300
    )


def test_current_weight_below_threshold_is_representable():
    result = base_context(
        birth_weight_grams=2500,
        current_weight_grams=1950,
    )

    assert (
        result.birth_weight_grams
        == 2500
    )

    assert (
        result.current_weight_grams
        == 1950
    )


def test_current_weight_is_optional_when_unknown():
    result = base_context(
        birth_weight_grams=1800,
    )

    assert (
        result.current_weight_grams
        is None
    )


@pytest.mark.parametrize(
    "value",
    [
        0,
        -1,
        -2000,
    ],
)
def test_current_weight_must_be_positive(
    value,
):
    with pytest.raises(
        ValidationError,
    ):
        base_context(
            current_weight_grams=value,
        )


def test_source_contract_uses_current_2000g_threshold():
    data = json.loads(
        SOURCE_PATH.read_text(
            encoding="utf-8"
        )
    )

    rule = data[
        "source_rule"
    ]

    assert (
        rule[
            "defer_if_current_weight_below_grams"
        ]
        == 2000
    )

    assert (
        rule[
            "resume_when_current_weight_reaches_grams"
        ]
        == 2000
    )

    assert (
        rule[
            "threshold_is_current_weight"
        ]
        is True
    )


def test_birth_weight_substitution_is_forbidden():
    data = json.loads(
        SOURCE_PATH.read_text(
            encoding="utf-8"
        )
    )

    assert (
        data[
            "model_problem_discovered"
        ][
            "birth_weight_can_substitute_for_current_weight"
        ]
        is False
    )

    assert (
        data[
            "remediation"
        ][
            "current_weight_is_inferred"
        ]
        is False
    )


def test_general_gap_dossier_records_post_lock_remediation():
    data = json.loads(
        GENERAL_GAP_PATH.read_text(
            encoding="utf-8"
        )
    )

    gap = data[
        "resolved_model_gaps"
    ][
        "current_weight_grams"
    ]

    assert (
        gap[
            "birth_weight_substitution_allowed"
        ]
        is False
    )

    assert (
        gap[
            "current_weight_inference_allowed"
        ]
        is False
    )

    assert (
        data[
            "post_lock_model_gap_state"
        ]
        == "complete_after_BH8E6A2"
    )


def test_governance_records_model_remediation_after_rule_transition():
    data = json.loads(
        GOV_PATH.read_text(
            encoding="utf-8"
        )
    )

    item8 = data[
        "future_items"
    ][
        "8"
    ]

    # The model-gap remediation remains complete after the
    # child-routine evaluator is added.
    assert (
        item8[
            "bcg_model_gap_state"
        ]
        == "current_weight_remediated"
    )

    assert (
        item8[
            "bcg_current_weight_field"
        ]
        == (
            "PniAssessmentContext."
            "current_weight_grams"
        )
    )

    assert (
        item8[
            "bcg_birth_weight_may_substitute_for_current_weight"
        ]
        is False
    )

    assert (
        item8[
            "bcg_current_weight_may_be_inferred"
        ]
        is False
    )

    assert (
        item8[
            "bcg_weight_threshold_grams"
        ]
        == 2000
    )

    # Governance must now reflect the legitimate transition
    # from model-remediation-only state to a partial BCG-family
    # implementation.
    assert (
        "bcg_child_routine"
        in item8[
            "implemented_rule_subfamilies"
        ]
    )

    assert (
        item8[
            "partial_rule_families"
        ][
            "bcg"
        ]
        == [
            "child_routine",
        ]
    )

    assert (
        item8[
            "bcg_child_rule_state"
        ]
        == "python_core_implemented_targeted_qc_pending"
    )

    assert (
        item8[
            "bcg_localization_state"
        ]
        == "pt_br_en_gb_locked"
    )

    assert hasattr(
        pni_2026,
        "evaluate_pni_bcg_child_routine",
    )

    # Model remediation did not imply completion of the whole
    # BCG family; special pathways remain explicitly deferred.
    assert (
        "hanseniasis"
        in item8[
            "deferred_rule_families"
        ][
            "bcg"
        ]
    )



def test_document_states_live_weight_boundary():
    text = DOC_PATH.read_text(
        encoding="utf-8"
    ).lower()

    for phrase in (
        "current-weight threshold",
        "birth weight",
        "current_weight_grams",
        "2,000 g",
        "must never",
        "does not implement bcg",
    ):
        assert phrase in text
