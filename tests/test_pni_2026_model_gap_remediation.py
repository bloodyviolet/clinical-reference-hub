from pathlib import Path
import json

import schemas


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

REMEDIATION_PATH = (
    ROOT
    / "data"
    / "clinical-sources"
    / "pni_2026_model_gap_remediation.json"
)

MATRIX_PATH = (
    ROOT
    / "data"
    / "clinical-sources"
    / "pni_2026_rule_matrix.json"
)

HARMONIZATION_PATH = (
    ROOT
    / "data"
    / "brazil_clinical_harmonization.json"
)

DOC_PATH = (
    ROOT
    / "docs"
    / "PNI_2026_MODEL_GAP_REMEDIATION.md"
)


def remediation():
    return json.loads(
        REMEDIATION_PATH.read_text(
            encoding="utf-8"
        )
    )


def matrix():
    return json.loads(
        MATRIX_PATH.read_text(
            encoding="utf-8"
        )
    )


def harmonization():
    return json.loads(
        HARMONIZATION_PATH.read_text(
            encoding="utf-8"
        )
    )


def test_exact_bh8c_gap_set_is_resolved():
    # BH8C remains a historical extraction checkpoint:
    # exactly 11 gaps were identified there.
    old_gaps = set(
        matrix()[
            "model_gap_inputs"
        ]
    )

    data = remediation()

    resolved = set(
        data[
            "resolved_model_gaps"
        ]
    )

    assert len(
        old_gaps
    ) == 11

    # Every original BH8C gap must remain resolved.
    assert (
        old_gaps
        <= resolved
    )

    # BH8E6 discovered exactly one additional post-lock gap.
    assert (
        resolved
        - old_gaps
        == {
            "current_weight_grams",
        }
    )

    assert (
        data[
            "post_lock_model_gap_state"
        ]
        == "complete_after_BH8E6A2"
    )

    discoveries = data[
        "post_lock_gap_discoveries"
    ]

    assert any(
        entry.get(
            "gap"
        )
        == "current_weight_grams"
        and entry.get(
            "state"
        )
        == "remediated_BH8E6A2"
        for entry
        in discoveries
    )



def test_no_unresolved_model_gap_remains():
    data = remediation()

    assert (
        data[
            "remaining_unresolved_model_gaps"
        ]
        == []
    )

    assert (
        data[
            "remediation_status"
        ]
        == "complete_rule_implementation_pending"
    )


def test_pregnancy_episode_is_available_on_context_and_dose():
    context_schema = (
        schemas
        .PniAssessmentContext
        .model_json_schema()
    )

    dose_schema = (
        schemas
        .PniDoseRecord
        .model_json_schema()
    )

    assert (
        "pregnancy_episode_key"
        in context_schema[
            "properties"
        ]
    )

    assert (
        "pregnancy_episode_key"
        in dose_schema[
            "properties"
        ]
    )


def test_maternal_hbsag_is_structured_tri_state():
    schema = (
        schemas
        .PniAssessmentContext
        .model_json_schema()
    )

    serialized = json.dumps(
        schema[
            "properties"
        ][
            "maternal_hbsag_status"
        ],
        ensure_ascii=False,
    )

    for value in (
        "positive",
        "negative",
        "unknown_or_unavailable",
    ):
        assert value in serialized


def test_birth_weight_has_no_artificial_maximum():
    schema = (
        schemas
        .PniAssessmentContext
        .model_json_schema()
    )

    serialized = json.dumps(
        schema[
            "properties"
        ][
            "birth_weight_grams"
        ],
    )

    assert (
        '"maximum"'
        not in serialized
    )


def test_bcg_evidence_model_exists():
    assert hasattr(
        schemas,
        "PniBcgVaccinationEvidence",
    )


def test_disease_and_exposure_models_exist():
    assert hasattr(
        schemas,
        "PniDiseaseEvent",
    )

    assert hasattr(
        schemas,
        "PniExposureEvent",
    )


def test_breastfeeding_model_exists():
    assert hasattr(
        schemas,
        "PniBreastfeedingContext",
    )


def test_travel_model_exists():
    assert hasattr(
        schemas,
        "PniTravelContext",
    )


def test_travel_layer_is_now_explicit():
    schema = (
        schemas
        .PniAssessmentRequest
        .model_json_schema()
    )

    serialized = json.dumps(
        schema[
            "properties"
        ][
            "requested_layers"
        ],
    )

    assert (
        "travel_or_area_risk"
        in serialized
    )


def test_destination_does_not_encode_risk_classification():
    travel_schema = (
        schemas
        .PniTravelContext
        .model_json_schema()
    )

    properties = (
        travel_schema[
            "properties"
        ]
    )

    assert (
        "risk_area"
        not in properties
    )

    assert (
        "yellow_fever_risk"
        not in properties
    )


def test_living_governance_opens_only_fail_closed_rule_gate():
    item8 = (
        harmonization()[
            "future_items"
        ][
            "8"
        ]
    )

    assert (
        item8[
            "implementation_state"
        ]
        == "rule_implementation_in_progress"
    )

    assert (
        item8[
            "model_gap_remediation_state"
        ]
        == "complete"
    )

    assert (
        item8[
            "model_gap_remediation_required"
        ]
        is False
    )

    assert (
        item8[
            "unresolved_model_gap_inputs"
        ]
        == []
    )

    assert (
        item8[
            "rule_engine_implementation_allowed"
        ]
        is True
    )

    assert (
        item8[
            "rule_engine_gate"
        ]
        == "granular_rules_allowed_fail_closed_manual_review_required"
    )


def test_historical_matrix_remains_truthful_about_bh8c_gate():
    data = matrix()

    assert (
        data[
            "rule_engine_implementation_allowed"
        ]
        is False
    )

    assert (
        data[
            "model_gap_remediation_required"
        ]
        is True
    )


def test_manual_review_boundaries_are_preserved():
    text = "\n".join(
        remediation()[
            "manual_review_boundaries"
        ]
    ).lower()

    assert (
        "destination"
        in text
    )

    assert (
        "hbsag"
        in text
    )

    assert (
        "bcg"
        in text
    )

    assert (
        "reported"
        in text
    )

    assert (
        "special_pathway_review"
        in text
    )


def test_no_synthetic_vaccination_score():
    assert (
        remediation()[
            "synthetic_vaccination_score_allowed"
        ]
        is False
    )


def test_remediation_document_records_fail_closed_boundary():
    document = DOC_PATH.read_text(
        encoding="utf-8"
    )

    for phrase in (
        "Unknown/unavailable is not negative",
        "not infer that the destination is an official",
        "context_required",
        "special_pathway_review",
    ):
        assert (
            phrase
            in document
        )
