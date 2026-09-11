from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parents[1]

AUDIT_PATH = (
    ROOT
    / "data"
    / "brazil_clinical_harmonization.json"
)

POLICY_PATH = (
    ROOT
    / "docs"
    / "V2_BRAZIL_CLINICAL_HARMONIZATION_POLICY.md"
)

REPORT_PATH = (
    ROOT
    / "docs"
    / "V2_BRAZIL_RETROACTIVE_AUDIT_ITEMS_1_6.md"
)


def audit():
    return json.loads(
        AUDIT_PATH.read_text(
            encoding="utf-8"
        )
    )


def test_brazil_governance_artifacts_exist():
    assert AUDIT_PATH.is_file()
    assert POLICY_PATH.is_file()
    assert REPORT_PATH.is_file()


def test_all_accepted_v2_items_have_brazil_review():
    data = audit()

    items = {
        item["item"]: item
        for item in data["items"]
    }

    assert set(items) == {
        1,
        2,
        3,
        4,
        5,
        6,
    }

    allowed = set(
        data["status_vocabulary"]
    )

    for item in items.values():
        assert (
            item[
                "brazil_applicability_status"
            ]
            in allowed
        )

        assert item[
            "brazil_sources"
        ]

        assert item[
            "required_actions"
        ]

        assert item[
            "scope_pt"
        ]

        assert item[
            "scope_en"
        ]


def test_news2_validated_brazilian_harmonization_is_complete():
    item = next(
        value
        for value in audit()["items"]
        if value["item"] == 1
    )

    assert (
        item[
            "brazil_applicability_status"
        ]
        == "validated_brazilian_adaptation"
    )

    assert (
        item[
            "remediation_required"
        ]
        is False
    )

    assert (
        item[
            "final_brazil_review_status"
        ]
        == "pass"
    )

    assert item[
        "remediation_completed"
    ]

    findings = " ".join(
        item[
            "brazil_sources"
        ][0][
            "key_findings"
        ]
    )

    assert (
        "Royal College of Physicians"
        in findings
    )


def test_renal_national_variant_harmonization_is_complete():
    item = next(
        value
        for value in audit()["items"]
        if value["item"] == 2
    )

    assert (
        item[
            "brazil_applicability_status"
        ]
        == "national_variant"
    )

    assert (
        item[
            "national_sus_mandate_identified"
        ]
        is True
    )

    assert (
        item[
            "brazil_differs_from_international_numeric_rules"
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
            "final_brazil_review_status"
        ]
        == "pass"
    )

    assert (
        item[
            "bh2b_core_status"
        ]
        == "pass"
    )

    assert (
        item[
            "bh2b_ui_status"
        ]
        == "pass"
    )

    assert (
        item[
            "implementation_blocked"
        ]
        is False
    )

    assert (
        item[
            "literal_pcdt_equation_implementation_blocked"
        ]
        is True
    )

    assert item[
        "remediation_completed"
    ]

    assert any(
        "11/2024"
        in source.get(
            "document",
            "",
        )
        for source in item[
            "brazil_sources"
        ]
    )


def test_context_specific_rules_cannot_become_universal():
    data = audit()

    hemo = next(
        item
        for item in data["items"]
        if item["item"] == 3
    )

    metabolic = next(
        item
        for item in data["items"]
        if item["item"] == 5
    )

    assert (
        hemo[
            "brazil_applicability_status"
        ]
        == "complementary_brazil_guidance"
    )

    assert (
        metabolic[
            "brazil_applicability_status"
        ]
        == "complementary_brazil_guidance"
    )

    assert any(
        "universal"
        in action.lower()
        for action in hemo[
            "required_actions"
        ]
    )

    assert any(
        "automatically"
        in action.lower()
        for action in metabolic[
            "required_actions"
        ]
    )


def test_oxygenation_records_no_generic_national_variant():
    item = next(
        value
        for value in audit()["items"]
        if value["item"] == 4
    )

    assert (
        item[
            "brazil_applicability_status"
        ]
        == "no_national_variant_identified"
    )

    assert (
        item[
            "brazil_differs_from_international_numeric_rules"
        ]
        is False
    )


def test_growth_is_already_harmonized():
    item = next(
        value
        for value in audit()["items"]
        if value["item"] == 6
    )

    assert (
        item[
            "brazil_applicability_status"
        ]
        == "national_standard"
    )

    assert (
        item[
            "remediation_required"
        ]
        is False
    )

    assert (
        item[
            "final_brazil_review_status"
        ]
        == "pass"
    )


def test_item7_is_blocked_until_brazil_review():
    data = audit()

    item7 = data[
        "future_items"
    ][
        "7"
    ]

    assert (
        item7[
            "implementation_state"
        ]
        == "blocked_pending_brazil_review"
    )

    assert (
        data[
            "release_gate"
        ][
            "prospective_from_item"
        ]
        == 7
    )


def test_policy_contains_release_gate_language():
    text = POLICY_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "No v2 feature may be marked final"
        in text
    )

    assert (
        "applies retrospectively to Items 1–6"
        in text
    )

    assert (
        "Items 7 onward"
        in text
    )
