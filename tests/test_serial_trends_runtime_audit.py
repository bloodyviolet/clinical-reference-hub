from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import pytest


ROOT = Path(
    __file__
).resolve().parents[1]

RUNTIME_PATH = (
    ROOT
    / "assets"
    / "serial-trends-runtime.js"
)

CONTRACT_PATH = (
    ROOT
    / "data"
    / "clinical-sources"
    / "serial_trends_runtime_contract.json"
)

JS_AUDIT_PATH = (
    ROOT
    / "tests"
    / "serial_trends_runtime_audit.js"
)

ARCHITECTURE_PATH = (
    ROOT
    / "data"
    / "clinical-sources"
    / "serial_trends.json"
)

REGISTRY_PATH = (
    ROOT
    / "data"
    / "clinical-sources"
    / "serial_trends_instrument_registry.json"
)

GOVERNANCE_PATH = (
    ROOT
    / "data"
    / "brazil_clinical_harmonization.json"
)


EXPECTED_RUNTIME_SHA256 = (
    "aa29106e2caa20eff1104ba853ecc59d0dc752ec18c5a272a2b0dfa06fe5f2b4"
)

EXPECTED_JS_AUDIT_SHA256 = (
    "0d3a8d62ef985f637896727418a30eaf6183f4d0819c08fa521b3a48ba16f8a7"
)

EXPECTED_CONTRACT_SHA256 = (
    "bbbda784fd6fd1e19b9eb41fd820f93febae772f7ba1f7af2fbcc88ea34347d4"
)


def load_json(path: Path):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def sha256(path: Path):
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def test_qualified_runtime_artifact_hashes():
    assert RUNTIME_PATH.is_file()
    assert CONTRACT_PATH.is_file()
    assert JS_AUDIT_PATH.is_file()

    assert (
        sha256(RUNTIME_PATH)
        == EXPECTED_RUNTIME_SHA256
    )

    assert (
        sha256(JS_AUDIT_PATH)
        == EXPECTED_JS_AUDIT_SHA256
    )

    assert (
        sha256(CONTRACT_PATH)
        == EXPECTED_CONTRACT_SHA256
    )


def test_runtime_contract_preserves_ephemeral_boundary():
    contract = load_json(
        CONTRACT_PATH
    )

    assert contract[
        "qualification_status"
    ] == "runtime_semantics_candidate"

    persistence = contract[
        "persistence"
    ]

    assert (
        persistence[
            "memory_only"
        ]
        is True
    )

    for key in (
        "local_storage",
        "session_storage",
        "indexed_db",
        "service_worker_storage",
        "server_storage",
    ):
        assert (
            persistence[key]
            is False
        )


def test_runtime_contract_preserves_time_semantics():
    contract = load_json(
        CONTRACT_PATH
    )

    time = contract[
        "time"
    ]

    assert (
        time[
            "observed_at_source"
        ]
        == "explicit_user_input"
    )

    assert (
        time[
            "observed_at_format"
        ]
        == "rfc3339_offset_aware"
    )

    assert (
        time[
            "naive_datetime_allowed"
        ]
        is False
    )

    assert (
        time[
            "date_only_allowed"
        ]
        is False
    )

    assert (
        time[
            "future_observation_allowed"
        ]
        is False
    )

    assert (
        time[
            "captured_at_source"
        ]
        == "browser_clock"
    )

    assert (
        time[
            "captured_at_format"
        ]
        == "rfc3339_utc"
    )

    assert (
        time[
            "captured_at_defines_clinical_order"
        ]
        is False
    )

    assert (
        time[
            "equal_instants_form_tie_group"
        ]
        is True
    )

    assert (
        time[
            "tie_breaker_has_clinical_meaning"
        ]
        is False
    )


def test_runtime_contract_preserves_snapshot_boundary():
    snapshot = load_json(
        CONTRACT_PATH
    )[
        "snapshot"
    ]

    assert (
        snapshot[
            "json_only"
        ]
        is True
    )

    assert (
        snapshot[
            "deep_copy_required"
        ]
        is True
    )

    assert (
        snapshot[
            "deep_freeze_required"
        ]
        is True
    )

    assert (
        snapshot[
            "request_reconstruction_allowed"
        ]
        is False
    )

    assert (
        snapshot[
            "result_recalculation_allowed"
        ]
        is False
    )


def test_runtime_contract_preserves_series_boundary():
    series = load_json(
        CONTRACT_PATH
    )[
        "series"
    ]

    assert (
        series[
            "one_series_one_instrument"
        ]
        is True
    )

    assert (
        series[
            "duplicate_observations_allowed"
        ]
        is True
    )

    assert (
        series[
            "automatic_deduplication"
        ]
        is False
    )

    assert (
        series[
            "cross_instrument_merge"
        ]
        is False
    )

    assert (
        series[
            "runtime_key_is_clinical_identity"
        ]
        is False
    )

    assert (
        series[
            "runtime_key_is_persistent"
        ]
        is False
    )


def test_runtime_contract_preserves_registry_rendering_boundary():
    rendering = load_json(
        CONTRACT_PATH
    )[
        "rendering"
    ]

    assert (
        rendering[
            "registry_only"
        ]
        is True
    )

    assert (
        rendering[
            "numeric_auto_discovery"
        ]
        is False
    )

    assert (
        rendering[
            "plot_only_registered_fields"
        ]
        is True
    )

    assert (
        rendering[
            "null_plot_policy"
        ]
        == "gap"
    )

    assert (
        rendering[
            "nt_plot_policy"
        ]
        == "gap"
    )

    assert (
        rendering[
            "connect_points"
        ]
        is False
    )

    assert (
        rendering[
            "interpolation"
        ]
        is False
    )

    assert (
        rendering[
            "forecasting"
        ]
        is False
    )


def test_runtime_contract_preserves_execution_source():
    source = load_json(
        CONTRACT_PATH
    )[
        "execution_source"
    ]

    assert set(
        source[
            "allowed"
        ]
    ) == {
        "api",
        "offline",
    }

    assert source[
        "required"
    ] is True

    assert source[
        "visible"
    ] is True


def test_runtime_matches_architecture_and_registry_history():
    architecture = load_json(
        ARCHITECTURE_PATH
    )

    registry = load_json(
        REGISTRY_PATH
    )

    governance = load_json(
        GOVERNANCE_PATH
    )

    assert (
        architecture[
            "implementation_status"
        ]
        == "architecture_review_complete_implementation_pending"
    )

    assert (
        registry[
            "registry_status"
        ]
        == "instrument_registry_qualified_implementation_pending"
    )

    current = governance[
        "future_items"
    ][
        "11"
    ][
        "implementation_state"
    ]

    # Runtime qualification is downstream of both
    # historical prerequisite artifacts. Later Item 11
    # states must not require rewriting those artifacts.
    assert (
        current
        != architecture[
            "implementation_status"
        ]
    )

    assert (
        current
        != registry[
            "registry_status"
        ]
    )

    assert (
        governance[
            "release_gate"
        ][
            "final_recheck_required_before_v2_release"
        ]
        is True
    )


def test_qualified_js_runtime_audit_executes():
    try:
        completed = subprocess.run(
            [
                "node",
                str(JS_AUDIT_PATH),
                str(RUNTIME_PATH),
                str(CONTRACT_PATH),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        pytest.fail(
            "node executable unavailable"
        )

    output = (
        completed.stdout
        + completed.stderr
    )

    assert (
        "serial_trends_runtime_qc:"
        in output
    )

    assert (
        "memory-only isolation PASS"
        in output
    )

    assert (
        "serial_trends_registry_snapshot_qc:"
        in output
    )

    assert (
        "store authorization PASS"
        in output
    )
