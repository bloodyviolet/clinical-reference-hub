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
    / "oxygenation_brazil_2026.json"
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
        if item["item"] == 4
    )


def test_source_dossier_exists_and_is_pending_metadata_only():
    assert SOURCE_PATH.is_file()

    data = source()

    assert (
        data[
            "implementation_status"
        ]
        == "metadata_integration_complete"
    )

    assert (
        data[
            "harmonization_implementation_complete"
        ]
        is True
    )

    assert (
        data[
            "bh4b_metadata_status"
        ]
        == "pass"
    )

    assert (
        data[
            "bh4b_visible_provenance_status"
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
        == "no_national_variant_identified"
    )


def test_no_brazil_generic_pf_or_sf_variant_identified():
    data = source()

    assert (
        data[
            "national_generic_pf_variant_identified"
        ]
        is False
    )

    assert (
        data[
            "national_generic_sf_variant_identified"
        ]
        is False
    )


def test_no_formal_sus_global_ards_adoption_identified():
    assert (
        source()[
            "formal_sus_global_ards_adoption_identified"
        ]
        is False
    )


def test_current_ministry_source_supersedes_old_surveillance_guide():
    current = source()[
        "current_brazil_respiratory_surveillance"
    ]

    assert (
        current[
            "document"
        ]
        == "Nota Técnica nº 11/2026-CGCOVID/DEDT/SVSA/MS"
    )

    assert (
        current[
            "publication_date"
        ]
        == "2026-08-19"
    )

    assert (
        "supersedes"
        in current
        or "Supersedes"
        in current.get(
            "supersedes",
            "",
        )
    )

    assert (
        "SpO2 <=94%"
        in current[
            "current_srag_definition_finding"
        ]
    )


def test_srag_surveillance_is_not_reinterpreted_as_ards_math():
    finding = source()[
        "current_brazil_respiratory_surveillance"
    ][
        "oxygenation_engine_implication"
    ]

    assert (
        "not a replacement P/F or S/F formula"
        in finding
    )

    assert (
        "not a generic ARDS oxygenation definition"
        in finding
    )


def test_base_calculation_policy_requires_no_math_change():
    policy = source()[
        "base_calculation_policy"
    ]

    assert (
        policy[
            "pf_formula_change_required"
        ]
        is False
    )

    assert (
        policy[
            "sf_formula_change_required"
        ]
        is False
    )

    assert (
        policy[
            "fio2_input_contract_change_required"
        ]
        is False
    )

    assert (
        policy[
            "ards_auto_classification_allowed"
        ]
        is False
    )

    assert (
        policy[
            "sf_spo2_97_caution_change_required"
        ]
        is False
    )


def test_negative_finding_is_explicitly_bounded():
    policy = source()[
        "negative_finding_policy"
    ].lower()

    assert (
        "authoritative source corpus"
        in policy
    )

    assert (
        "not a claim"
        in policy
    )


def test_item4_remains_metadata_remediation_only():
    item = audit_item()

    assert (
        item[
            "brazil_applicability_status"
        ]
        == "no_national_variant_identified"
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
            "formal_sus_global_ards_adoption_identified"
        ]
        is False
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
            "bh4b_metadata_status"
        ]
        == "pass"
    )

    assert (
        item[
            "bh4b_visible_provenance_status"
        ]
        == "pass"
    )

    assert (
        item[
            "final_brazil_review_status"
        ]
        == "pass"
    )
