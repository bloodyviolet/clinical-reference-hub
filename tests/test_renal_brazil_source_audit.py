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
    / "renal_brazil_2026.json"
)


def source():
    return json.loads(
        SOURCE_PATH.read_text(
            encoding="utf-8"
        )
    )


def test_current_renal_brazil_source_dossier_exists():
    assert SOURCE_PATH.is_file()

    data = source()

    assert (
        data[
            "implementation_status"
        ]
        == (
            "safe_context_implemented_"
            "literal_equation_blocked"
        )
    )


def test_pcdt_is_recorded_as_national_sus_source():
    pcdt = source()[
        "national_sus_pcdt"
    ]

    assert (
        pcdt[
            "national_character"
        ]
        is True
    )

    assert (
        pcdt[
            "must_be_used_by_sus_managers"
        ]
        is True
    )

    assert (
        "11"
        in pcdt["portaria"]
    )

    assert (
        pcdt[
            "current_annex_update"
        ]
        == "2025-02-07"
    )


def test_pcdt_race_constants_are_transcribed_not_implemented():
    formula = source()[
        "national_sus_pcdt"
    ][
        "printed_formula_transcription"
    ]

    assert formula["A"] == {
        "black_female": 166,
        "black_male": 163,
        "non_black_female": 144,
        "non_black_male": 141,
    }

    assert formula["B"] == {
        "female": 0.7,
        "male": 0.9,
    }

    assert (
        source()[
            "bh2b_gate"
        ]
        == (
            "pass_safe_context_integration"
        )
    )


def test_reference_2009_branch_is_sex_specific():
    branch = source()[
        "reference_equation_qc"
    ][
        "high_creatinine_transition"
    ]

    assert (
        branch[
            "female_mg_dl"
        ]
        == 0.7
    )

    assert (
        branch[
            "male_mg_dl"
        ]
        == 0.9
    )


def test_all_four_source_conflicts_are_durable():
    conflicts = {
        item["id"]: item
        for item in source()[
            "verified_source_conflicts"
        ]
    }

    assert set(conflicts) == {
        "PCDT-EQ-AGE-01",
        "PCDT-EQ-CREAT-02",
        "PCDT-RAC-300-03",
        "PCDT-RACE-SBN-04",
    }

    assert (
        conflicts[
            "PCDT-EQ-AGE-01"
        ][
            "severity"
        ]
        == "critical"
    )

    assert (
        conflicts[
            "PCDT-EQ-CREAT-02"
        ][
            "severity"
        ]
        == "critical"
    )


def test_sbn_sbpc_consensus_prefers_2021_race_free():
    consensus = source()[
        "brazilian_specialty_consensus"
    ]

    assert (
        "CKD-EPI 2021 creatinine"
        in consensus[
            "adult_preferred_equations"
        ]
    )

    race_position = (
        consensus[
            "race_correction_position"
        ]
        .lower()
    )

    assert (
        "race correction"
        in race_position
    )

    assert (
        "do not use"
        in race_position
    )


def test_rac_exact_300_is_recorded_as_ambiguity():
    conflict = next(
        value
        for value in source()[
            "verified_source_conflicts"
        ]
        if (
            value["id"]
            == "PCDT-RAC-300-03"
        )
    )

    assert (
        "300"
        in conflict[
            "ambiguity"
        ]
    )

    assert (
        "A2"
        in conflict[
            "current_app_rule"
        ]
    )


def test_aki_is_already_numerically_brazil_aligned():
    aki = source()[
        "aki_brazil_alignment"
    ]

    assert (
        aki[
            "uses_kdigo_2012"
        ]
        is True
    )

    assert (
        aki[
            "numeric_remediation_required"
        ]
        is False
    )

    assert (
        aki[
            "metadata_remediation_required"
        ]
        is True
    )


def test_bh2b_rules_forbid_silent_race_based_replacement():
    rules = " ".join(
        source()[
            "bh2b_implementation_rules"
        ]
    ).lower()

    assert (
        "preserve ckd-epi 2021"
        in rules
    )

    assert (
        "infer race"
        in rules
    )

    assert (
        "phenotype"
        in rules
    )

    assert (
        "proxy"
        in rules
    )

    assert (
        "do not ask the application"
        in rules
    )

    assert (
        "pcdt separately"
        in rules
    )
