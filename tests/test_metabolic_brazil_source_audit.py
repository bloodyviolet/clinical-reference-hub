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
    / "metabolic_brazil_2026.json"
)


AUDIT_PATH = (
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


def audit_item():
    data = json.loads(
        AUDIT_PATH.read_text(
            encoding="utf-8"
        )
    )

    return next(
        item
        for item in data["items"]
        if item["item"] == 5
    )


def test_source_dossier_exists_and_is_pending_implementation():
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
            "bh5b_core_status"
        ]
        == "pass"
    )

    assert (
        data[
            "bh5b_ui_status"
        ]
        == "pass"
    )

    assert (
        data[
            "final_brazil_review_status"
        ]
        == "pass"
    )

    assert (
        data[
            "brazil_applicability_status"
        ]
        == "complementary_brazil_guidance"
    )


def test_generic_metabolic_math_must_not_change():
    policy = source()[
        "base_calculation_policy"
    ]

    for key in (
        "general_anion_gap_change_required",
        "albumin_correction_change_required",
        "general_osmolality_change_required",
        "corrected_sodium_change_required",
        "winter_formula_change_required",
        "delta_ratio_change_required",
        "methanol_context_may_replace_general_formulas",
    ):
        assert policy[key] is False


def test_ministry_methanol_anion_gap_includes_potassium():
    formula = source()[
        "federal_sources"
    ][
        "ministry_saes_methanol_flowchart"
    ][
        "formula_table"
    ][
        "anion_gap"
    ]

    assert (
        formula["formula"]
        == "(Na + K) - (HCO3 + Cl)"
    )

    assert (
        formula[
            "potassium_included"
        ]
        is True
    )

    assert (
        formula[
            "input_unit"
        ]
        == "mmol/L"
    )


def test_generic_anion_gap_remains_potassium_free():
    generic = source()[
        "current_generic_engine"
    ]

    assert (
        generic[
            "anion_gap_formula"
        ]
        == "Na - (Cl + HCO3), potassium excluded"
    )


def test_osmolar_gap_requires_measured_osmolality():
    formula = source()[
        "federal_sources"
    ][
        "ministry_saes_methanol_flowchart"
    ][
        "formula_table"
    ][
        "osmolar_gap"
    ]

    assert (
        formula[
            "requires_measured_osmolality"
        ]
        is True
    )


def test_ministry_osmolality_uses_urea_and_mmol_domain():
    formula = source()[
        "federal_sources"
    ][
        "ministry_saes_methanol_flowchart"
    ][
        "formula_table"
    ][
        "calculated_osmolality"
    ]

    assert (
        formula[
            "uses_urea_not_bun"
        ]
        is True
    )

    assert (
        formula[
            "input_unit"
        ]
        == "mmol/L"
    )

    assert (
        "1.86"
        in formula[
            "formula"
        ]
    )


def test_ministry_thresholds_remain_contextual():
    context = source()[
        "federal_sources"
    ][
        "ministry_saes_methanol_flowchart"
    ][
        "diagnostic_context"
    ]

    assert (
        context[
            "anion_gap_increased_gt_meq_l"
        ]
        == 12
    )

    assert (
        context[
            "osmolar_gap_suspect_gt_mosm_kg"
        ]
        == 10
    )

    assert (
        context[
            "osmolar_gap_strongly_suggestive_gt_mosm_kg"
        ]
        == 25
    )

    assert (
        context[
            "normal_osmolar_gap_excludes_late_poisoning"
        ]
        is False
    )


def test_all_four_safety_conflicts_are_durable():
    conflicts = {
        item["id"]
        for item in source()[
            "verified_context_conflicts"
        ]
    }

    assert conflicts == {
        "MET-AG-K-01",
        "MET-OSM-UNIT-02",
        "MET-GO-MEASURED-03",
        "MET-DX-CONTEXT-04",
    }


def test_rules_forbid_automatic_diagnosis_and_unit_conflation():
    rules = " ".join(
        source()[
            "bh5b_implementation_rules"
        ]
    ).lower()

    assert (
        "never automatically select"
        in rules
    )

    assert (
        "measured osmolality"
        in rules
    )

    assert (
        "urea and bun"
        in rules
    )

    assert (
        "mmol/l and mg/dl"
        in rules
    )

    assert (
        "do not infer methanol poisoning"
        in rules
    )


def test_audit_item_is_high_priority_context_remediation():
    item = audit_item()

    assert (
        item[
            "brazil_applicability_status"
        ]
        == "complementary_brazil_guidance"
    )

    assert (
        item[
            "source_review_verified"
        ]
        is True
    )

    assert (
        item[
            "base_calculations_change_required"
        ]
        is False
    )

    assert (
        item[
            "contextual_formula_variant_identified"
        ]
        is True
    )

    assert (
        item[
            "methanol_context_must_be_explicit"
        ]
        is True
    )

    assert (
        item[
            "measured_osmolality_required_for_osmolar_gap"
        ]
        is True
    )

    assert (
        item[
            "unit_domain_conflict_verified"
        ]
        is True
    )

    assert (
        item[
            "remediation_required"
        ]
        is False
    )

    assert (
        item[
            "remediation_priority"
        ]
        == "none"
    )

    assert (
        item[
            "bh5b_core_status"
        ]
        == "pass"
    )

    assert (
        item[
            "bh5b_ui_status"
        ]
        == "pass"
    )

    assert (
        item[
            "final_brazil_review_status"
        ]
        == "pass"
    )
