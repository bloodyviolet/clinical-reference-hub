from __future__ import annotations

import hashlib
import json
from pathlib import Path

import main


ROOT = Path(
    __file__
).resolve().parents[1]

REGISTRY_PATH = (
    ROOT
    / "data"
    / "clinical-sources"
    / "serial_trends_instrument_registry.json"
)

ARCHITECTURE_PATH = (
    ROOT
    / "data"
    / "clinical-sources"
    / "serial_trends.json"
)

GOVERNANCE_PATH = (
    ROOT
    / "data"
    / "brazil_clinical_harmonization.json"
)

EXPECTED_REGISTRY_SHA256 = (
    "5b53d89bfb88a844f6baf0a3d9202d7565ab6f63737f5a000d79340b5dd8bf54"
)


def registry():
    return json.loads(
        REGISTRY_PATH.read_text(
            encoding="utf-8"
        )
    )


def architecture():
    return json.loads(
        ARCHITECTURE_PATH.read_text(
            encoding="utf-8"
        )
    )


def governance():
    return json.loads(
        GOVERNANCE_PATH.read_text(
            encoding="utf-8"
        )
    )


def openapi():
    return main.app.openapi()


def test_registry_artifact_identity_and_hash():
    assert REGISTRY_PATH.is_file()

    actual = hashlib.sha256(
        REGISTRY_PATH.read_bytes()
    ).hexdigest()

    assert actual == EXPECTED_REGISTRY_SHA256

    data = registry()

    assert data["schema_version"] == 1
    assert data["item"] == 11
    assert data["feature"] == "Serial trends"

    assert (
        data["registry_status"]
        == "instrument_registry_qualified_implementation_pending"
    )


def test_registry_exactly_covers_all_current_post_tool_routes():
    spec = openapi()

    routes = {
        path
        for path, operations
        in spec["paths"].items()
        if (
            path.startswith(
                "/api/v1/tools/"
            )
            and "post" in operations
        )
    }

    registered = {
        item["route"]
        for item
        in registry()["instruments"]
    }

    assert len(routes) == 18
    assert len(registered) == 18
    assert registered == routes

    keys = [
        item["key"]
        for item
        in registry()["instruments"]
    ]

    assert len(keys) == len(set(keys))


def test_all_instruments_are_explicitly_table_enabled():
    items = registry()["instruments"]

    assert len(items) == 18

    assert all(
        item["table_enabled"] is True
        for item in items
    )

    assert all(
        "summary_fields" in item
        for item in items
    )

    assert all(
        "component_fields" in item
        for item in items
    )

    assert all(
        "context_fields" in item
        for item in items
    )

    assert all(
        "plot_groups" in item
        for item in items
    )


def test_global_contract_forbids_automatic_inference():
    contract = registry()[
        "global_contract"
    ]

    assert (
        contract[
            "numeric_auto_discovery"
        ]
        is False
    )

    assert (
        contract[
            "ordinal_auto_plot"
        ]
        is False
    )

    assert (
        contract[
            "threshold_auto_plot"
        ]
        is False
    )

    assert (
        contract[
            "reference_constant_auto_plot"
        ]
        is False
    )

    assert (
        contract[
            "connect_points"
        ]
        is False
    )

    assert contract[
        "interpolation"
    ] is False

    assert contract[
        "smoothing"
    ] is False

    assert contract[
        "regression"
    ] is False

    assert contract[
        "forecasting"
    ] is False

    assert (
        contract[
            "automatic_direction_interpretation"
        ]
        is False
    )

    assert (
        contract[
            "cross_instrument_plot"
        ]
        is False
    )


def test_registry_coverage_matches_qualified_counts():
    items = registry()[
        "instruments"
    ]

    table_enabled = [
        item
        for item in items
        if item["table_enabled"]
    ]

    plot_enabled = [
        item
        for item in items
        if item["plot_groups"]
    ]

    plot_excluded = [
        item
        for item in items
        if not item["plot_groups"]
    ]

    group_count = sum(
        len(item["plot_groups"])
        for item in items
    )

    field_count = sum(
        len(group["fields"])
        for item in items
        for group in item["plot_groups"]
    )

    assert len(table_enabled) == 18
    assert len(plot_enabled) == 17
    assert len(plot_excluded) == 1

    assert (
        plot_excluded[0]["key"]
        == "brazil_caderneta_falls"
    )

    assert group_count == 43
    assert field_count == 69


def test_caderneta_count_is_not_promoted_to_longitudinal_score():
    data = {
        item["key"]: item
        for item in registry()[
            "instruments"
        ]
    }

    caderneta = data[
        "brazil_caderneta_falls"
    ]

    assert caderneta[
        "plot_groups"
    ] == []

    assert (
        "validated weighted longitudinal score"
        in caderneta[
            "plot_exclusion_reason"
        ]
    )


def test_specific_ordinal_dynamic_unit_and_object_exclusions():
    data = {
        item["key"]: item
        for item in registry()[
            "instruments"
        ]
    }

    assert (
        "response.stage"
        in data[
            "kdigo_aki"
        ][
            "plot_excluded_fields"
        ]
    )

    assert (
        "request.acr"
        in data[
            "ckd_classification"
        ][
            "plot_excluded_fields"
        ]
    )

    assert (
        "response.indicators.*"
        in data[
            "who_growth"
        ][
            "plot_excluded_fields"
        ]
    )


def test_gcs_gcsp_four_preserve_components():
    data = {
        item["key"]: item
        for item in registry()[
            "instruments"
        ]
    }

    assert len(
        data["gcs"][
            "component_fields"
        ]
    ) == 3

    assert len(
        data["gcs_p"][
            "component_fields"
        ]
    ) >= 4

    assert len(
        data["four_score"][
            "component_fields"
        ]
    ) == 4


def test_plot_groups_are_discrete_and_nulls_are_gaps():
    for instrument in registry()[
        "instruments"
    ]:
        group_ids = []

        for group in instrument[
            "plot_groups"
        ]:
            assert (
                group["render"]
                == "discrete_points"
            )

            assert (
                group[
                    "connect_points"
                ]
                is False
            )

            assert (
                group[
                    "null_policy"
                ]
                == "gap"
            )

            assert group["unit"]
            assert group["fields"]

            group_ids.append(
                group["group_id"]
            )

        assert len(
            group_ids
        ) == len(
            set(group_ids)
        )


def test_architecture_dossier_remains_historical_after_registry_state():
    source = architecture()
    gov = governance()

    assert (
        source[
            "implementation_status"
        ]
        == "architecture_review_complete_implementation_pending"
    )

    assert (
        gov[
            "future_items"
        ][
            "11"
        ][
            "implementation_state"
        ]
        == "instrument_registry_qualified_implementation_pending"
    )

    assert (
        gov[
            "release_gate"
        ][
            "final_recheck_required_before_v2_release"
        ]
        is True
    )
