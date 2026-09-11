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
    / "hemodynamics_brazil_2026.json"
)


def source():
    return json.loads(
        SOURCE_PATH.read_text(
            encoding="utf-8"
        )
    )


def test_source_dossier_exists():
    assert SOURCE_PATH.is_file()

    data = source()

    assert (
        data[
            "implementation_status"
        ]
        == "context_integration_complete"
    )

    assert (
        data[
            "harmonization_implementation_complete"
        ]
        is True
    )

    assert (
        data[
            "bh3b_core_status"
        ]
        == "pass"
    )

    assert (
        data[
            "bh3b_ui_status"
        ]
        == "pass"
    )

    assert (
        data[
            "final_brazil_review_status"
        ]
        == "pass"
    )


def test_generic_calculations_must_remain_neutral():
    policy = source()[
        "base_calculation_policy"
    ]

    assert (
        policy[
            "map_formula_change_required"
        ]
        is False
    )

    assert (
        policy[
            "shock_index_formula_change_required"
        ]
        is False
    )

    assert (
        policy[
            "modified_shock_index_formula_change_required"
        ]
        is False
    )

    assert (
        policy[
            "universal_threshold_classification_allowed"
        ]
        is False
    )


def test_septic_map_65_is_context_only():
    context = source()[
        "contexts"
    ][
        "septic_shock_map"
    ]

    assert (
        context[
            "threshold_mm_hg"
        ]
        == 65
    )

    assert (
        "explicit septic-shock context"
        in context[
            "software_rule"
        ]
    )

    assert (
        "universal"
        in context[
            "software_rule"
        ]
    )


def test_obstetric_si_09_is_context_only():
    context = source()[
        "contexts"
    ][
        "obstetric_hemorrhage_shock_index"
    ]

    assert (
        context[
            "threshold"
        ]
        == 0.9
    )

    assert (
        context[
            "operator_from_ministry_source"
        ]
        == ">"
    )

    assert (
        "explicit obstetric-haemorrhage"
        in context[
            "software_rule"
        ]
    )


def test_ebserh_is_not_promoted_to_national_standard():
    evidence = source()[
        "contexts"
    ][
        "obstetric_hemorrhage_shock_index"
    ][
        "implementation_corroboration"
    ]

    assert (
        evidence[
            "national_standard"
        ]
        is False
    )


def test_no_universal_msi_or_pulse_pressure_cutoff():
    findings = source()[
        "no_universal_variant_findings"
    ]

    assert (
        "No authoritative Brazilian universal Modified"
        in findings[
            "modified_shock_index"
        ]
    )

    assert (
        "No authoritative Brazilian universal pulse-pressure"
        in findings[
            "pulse_pressure"
        ]
    )


def test_bh3b_rules_preserve_generic_threshold_false():
    rules = " ".join(
        source()[
            "bh3b_implementation_rules"
        ]
    ).lower()

    assert (
        "threshold_classification_applied=false"
        in rules
    )

    assert (
        "do not automatically classify generic map"
        in rules
    )

    assert (
        "do not automatically classify generic shock index"
        in rules
    )

    assert (
        "do not invent a brazilian modified shock index"
        in rules
    )
