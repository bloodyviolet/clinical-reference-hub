from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parents[1]

SOURCE_PATH = (
    ROOT
    / "data"
    / "clinical-sources"
    / "serial_trends.json"
)

DOC_PATH = (
    ROOT
    / "docs"
    / "SERIAL_TRENDS_ARCHITECTURE_VERIFICATION.md"
)

GOVERNANCE_PATH = (
    ROOT
    / "data"
    / "brazil_clinical_harmonization.json"
)


def source():
    return json.loads(
        SOURCE_PATH.read_text(
            encoding="utf-8"
        )
    )


def governance():
    return json.loads(
        GOVERNANCE_PATH.read_text(
            encoding="utf-8"
        )
    )


def test_serial_trends_architecture_artifacts_exist():
    assert SOURCE_PATH.is_file()
    assert DOC_PATH.is_file()


def test_item11_dossier_identity_and_role():
    data = source()

    assert data["schema_version"] == 1
    assert data["item"] == 11
    assert data["feature"] == "Serial trends"

    assert (
        data["implementation_status"]
        == "architecture_review_complete_implementation_pending"
    )

    assert (
        data["dossier_role"]
        == "architecture_and_safety_boundary_not_new_scoring_authority"
    )


def test_serial_trends_create_no_new_clinical_model():
    authority = source()[
        "authority_model"
    ]

    assert (
        authority[
            "new_numeric_clinical_model"
        ]
        is False
    )

    assert (
        authority[
            "new_clinical_formula"
        ]
        is False
    )

    assert (
        authority[
            "new_clinical_threshold"
        ]
        is False
    )

    assert (
        authority[
            "new_prognostic_model"
        ]
        is False
    )

    assert (
        authority[
            "reuse_existing_tool_source_authority"
        ]
        is True
    )

    assert (
        authority[
            "brazil_context_must_be_preserved"
        ]
        is True
    )


def test_serial_trends_are_ephemeral_and_non_patient_linked():
    persistence = source()[
        "persistence_contract"
    ]

    privacy = source()[
        "privacy_contract"
    ]

    assert (
        persistence["lifetime"]
        == "current_page_runtime_only"
    )

    assert (
        persistence["storage"]
        == "javascript_memory_only"
    )

    for key in (
        "server_persistence",
        "browser_persistence",
        "sqlite_storage",
        "local_storage",
        "session_storage",
        "indexed_db",
        "service_worker_storage",
        "database_migration_required",
        "new_api_storage_route_required",
    ):
        assert persistence[key] is False

    for key in (
        "patient_identifier",
        "encounter_identifier",
        "person_identifier",
        "free_text_subject_identifier",
        "free_text_clinical_note",
        "patient_record_system_created",
        "longitudinal_health_record_created",
    ):
        assert privacy[key] is False

    assert privacy["reload_clears_series"] is True


def test_observation_envelope_preserves_request_result_and_source():
    contract = source()[
        "observation_envelope_contract"
    ]

    assert contract[
        "required_fields"
    ] == [
        "instrument_key",
        "observed_at",
        "captured_at",
        "request_snapshot",
        "result_snapshot",
        "execution_source",
    ]

    assert (
        contract[
            "observed_at"
        ][
            "source"
        ]
        == "explicit_user_input"
    )

    assert (
        contract[
            "observed_at"
        ][
            "format"
        ]
        == "rfc3339_offset_aware"
    )

    assert (
        contract[
            "observed_at"
        ][
            "timezone_offset_required"
        ]
        is True
    )

    assert (
        contract[
            "observed_at"
        ][
            "may_default_from_capture_time"
        ]
        is False
    )

    assert (
        contract[
            "request_snapshot"
        ][
            "deep_copy_required"
        ]
        is True
    )

    assert (
        contract[
            "result_snapshot"
        ][
            "deep_copy_required"
        ]
        is True
    )

    assert (
        contract[
            "result_snapshot"
        ][
            "preserve_canonical_shape"
        ]
        is True
    )

    assert (
        contract[
            "execution_source"
        ][
            "allowed_values"
        ]
        == [
            "api",
            "offline",
        ]
    )


def test_series_preserves_instrument_independence():
    contract = source()[
        "series_contract"
    ]

    assert (
        contract[
            "one_series_one_instrument"
        ]
        is True
    )

    assert (
        contract[
            "instrument_mixing"
        ]
        is False
    )

    assert (
        contract[
            "cross_instrument_axis"
        ]
        is False
    )

    assert (
        contract[
            "cross_instrument_synthetic_score"
        ]
        is False
    )

    assert (
        contract[
            "gcs_gcsp_four_must_remain_independent"
        ]
        is True
    )


def test_incomplete_states_remain_visible_without_numeric_coercion():
    contract = source()[
        "incomplete_state_contract"
    ]

    assert contract[
        "nt_must_be_preserved"
    ] is True

    assert contract[
        "null_must_be_preserved"
    ] is True

    assert (
        contract[
            "non_evaluable_observation_must_be_preserved"
        ]
        is True
    )

    assert (
        contract[
            "numeric_coercion_of_nt"
        ]
        is False
    )

    assert (
        contract[
            "numeric_coercion_of_null"
        ]
        is False
    )

    assert (
        contract[
            "non_numeric_plot_value"
        ]
        is None
    )


def test_visualisation_requires_explicit_field_registry():
    contract = source()[
        "visualisation_contract"
    ]

    assert (
        contract[
            "chronological_table_required"
        ]
        is True
    )

    assert (
        contract[
            "table_must_preserve_component_values"
        ]
        is True
    )

    assert (
        contract[
            "numeric_field_auto_discovery_allowed"
        ]
        is False
    )

    assert (
        contract[
            "qualified_plot_field_registry_required"
        ]
        is True
    )

    for key in (
        "interpolation_allowed",
        "smoothing_allowed",
        "regression_allowed",
        "forecasting_allowed",
        "automatic_slope_interpretation_allowed",
        "automatic_improvement_deterioration_label_allowed",
        "cross_instrument_plot_allowed",
    ):
        assert contract[key] is False


def test_instrument_registry_is_required_before_browser_implementation():
    contract = source()[
        "instrument_registry_contract"
    ]

    assert (
        contract[
            "current_post_tool_route_count_at_review"
        ]
        == 18
    )

    assert (
        contract[
            "automatic_all_tool_opt_in"
        ]
        is False
    )

    assert (
        contract[
            "explicit_instrument_registry_required_before_ui_implementation"
        ]
        is True
    )

    assert (
        contract[
            "explicit_display_field_registry_required_before_plotting"
        ]
        is True
    )

    assert (
        contract[
            "registry_must_define_new_clinical_thresholds"
        ]
        if "registry_must_define_new_clinical_thresholds" in contract
        else False
    ) is False

    assert (
        contract[
            "registry_must_not_define_new_clinical_thresholds"
        ]
        is True
    )

    assert (
        contract[
            "registry_must_not_define_new_prognosis"
        ]
        is True
    )


def test_brazil_context_is_preserved():
    contract = source()[
        "brazil_context_contract"
    ]

    assert (
        contract[
            "existing_brazil_context_fields_must_be_preserved"
        ]
        is True
    )

    assert (
        contract[
            "existing_brazil_applicability_must_not_be_reclassified"
        ]
        is True
    )

    assert (
        contract[
            "international_and_brazilian_authority_roles_must_not_be_collapsed"
        ]
        is True
    )

    assert (
        contract[
            "trend_layer_may_not_promote_contextual_rule_to_universal_rule"
        ]
        is True
    )

    assert (
        contract[
            "release_source_recheck_required"
        ]
        is True
    )


def test_architecture_tranche_does_not_implement_runtime_layers():
    boundaries = source()[
        "implementation_boundaries"
    ]

    assert (
        boundaries[
            "architecture_dossier_this_tranche"
        ]
        is True
    )

    assert (
        boundaries[
            "governance_state_transition_this_tranche"
        ]
        is True
    )

    for key in (
        "clinical_core_this_tranche",
        "schemas_this_tranche",
        "api_this_tranche",
        "browser_this_tranche",
        "ui_this_tranche",
        "pwa_this_tranche",
        "database_this_tranche",
        "migration_this_tranche",
        "instrument_registry_this_tranche",
        "plot_field_registry_this_tranche",
        "patient_identity_this_tranche",
    ):
        assert boundaries[key] is False


def test_item11_governance_has_advanced_from_initial_constraint():
    data = source()
    governance_data = governance()

    lifecycle = data[
        "governance_lifecycle"
    ]

    item11 = governance_data[
        "future_items"
    ][
        "11"
    ]

    assert (
        item11["feature"]
        == "Serial trends"
    )

    assert (
        item11[
            "implementation_state"
        ]
        != lifecycle[
            "initial_state"
        ]
    )

    assert (
        item11[
            "implementation_state"
        ]
        in {
            lifecycle[
                "architecture_qualified_state"
            ],
            lifecycle[
                "implementation_complete_state"
            ],
        }
    )

    assert (
        governance_data[
            "release_gate"
        ][
            "final_recheck_required_before_v2_release"
        ]
        is True
    )
