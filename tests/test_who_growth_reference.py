from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "reference"
    / "who-growth"
)


def load(
    name: str,
):
    return json.loads(
        (
            ROOT / name
        ).read_text(
            encoding="utf-8"
        )
    )


def sha256(
    path: Path,
) -> str:
    h = hashlib.sha256()

    with path.open("rb") as fh:
        for chunk in iter(
            lambda: fh.read(1024 * 1024),
            b"",
        ):
            h.update(chunk)

    return h.hexdigest()


def test_who_2006_daily_table_domains():
    names = (
        "who2006_weight_for_age.json",
        "who2006_length_height_for_age.json",
        "who2006_bmi_for_age.json",
        "who2006_head_circumference_for_age.json",
    )

    for name in names:
        data = load(name)

        assert len(data) == 3654

        assert {
            row["sex"]
            for row in data
        } == {1, 2}

        ages = {
            row["age"]
            for row in data
        }

        assert min(ages) == 0
        assert max(ages) == 1826

        assert len(ages) == 1827


def test_who_2006_weight_length_height_domains():
    wfl = load(
        "who2006_weight_for_length.json"
    )

    wfh = load(
        "who2006_weight_for_height.json"
    )

    assert len(wfl) == 1302
    assert len(wfh) == 1102

    assert min(
        row["length"]
        for row in wfl
    ) == 45

    assert max(
        row["length"]
        for row in wfl
    ) == 110

    assert min(
        row["height"]
        for row in wfh
    ) == 65

    assert max(
        row["height"]
        for row in wfh
    ) == 120


def test_who_2007_table_domains_and_sentinels():
    wfa = load(
        "who2007_weight_for_age.json"
    )

    hfa = load(
        "who2007_height_for_age.json"
    )

    bfa = load(
        "who2007_bmi_for_age.json"
    )

    assert len(wfa) == 124
    assert len(hfa) == 340
    assert len(bfa) == 340

    assert min(
        row["age"]
        for row in wfa
    ) == 60

    assert max(
        row["age"]
        for row in wfa
    ) == 121

    assert min(
        row["age"]
        for row in hfa
    ) == 60

    assert max(
        row["age"]
        for row in hfa
    ) == 229

    assert min(
        row["age"]
        for row in bfa
    ) == 60

    assert max(
        row["age"]
        for row in bfa
    ) == 229


def test_current_who_upstream_pins_recorded():
    sources = load(
        "SOURCES.json"
    )

    upstream = sources[
        "upstream_verification"
    ]

    assert (
        upstream["anthro"][
            "verified_head"
        ]
        == (
            "b776d8a12b1c97369c748b561159fd2ec4f4db58"
        )
    )

    assert (
        upstream["anthroplus"][
            "verified_head"
        ]
        == (
            "7cfcdb39026e9a55de55732bc3cf14c82261bcf7"
        )
    )

    assert (
        upstream["anthro"][
            "pin_is_current_head"
        ]
        is True
    )

    assert (
        upstream["anthroplus"][
            "pin_is_current_head"
        ]
        is True
    )


def test_manifest_hashes_match_normalized_files():
    sources = load(
        "SOURCES.json"
    )

    for entry in sources[
        "normalized_files"
    ]:
        path = (
            ROOT
            / entry["filename"]
        )

        assert path.is_file()

        assert (
            sha256(path)
            == entry["sha256"]
        )


def test_brazil_policy_uses_who_numerics():
    policy = load(
        "BRAZIL_SISVAN.json"
    )

    assert (
        policy[
            "interpretation_priority"
        ][
            "numerical_reference"
        ]
        == "WHO"
    )

    assert (
        policy[
            "interpretation_priority"
        ][
            "brazilian_clinical_label"
        ]
        == (
            "Ministério da Saúde / SISVAN"
        )
    )


def test_brazil_under5_bmi_has_risk_overweight_band():
    policy = load(
        "BRAZIL_SISVAN.json"
    )

    bands = policy[
        "classifications"
    ][
        "under_5"
    ][
        "weight_for_length_height"
    ]

    risk = next(
        band
        for band in bands
        if band["code"]
        == "risk_overweight"
    )

    assert risk["z_min"] == 1
    assert risk["z_min_inclusive"] is False
    assert risk["z_max"] == 2
    assert risk["z_max_inclusive"] is True


def test_brazil_5plus_bmi_uses_overweight_not_risk_band():
    policy = load(
        "BRAZIL_SISVAN.json"
    )

    bands = policy[
        "classifications"
    ][
        "age_5_to_under_10"
    ][
        "bmi_for_age"
    ]

    codes = {
        band["code"]
        for band in bands
    }

    assert "risk_overweight" not in codes
    assert "overweight" in codes
    assert "obesity" in codes
    assert "severe_obesity" in codes


def test_brazil_head_circumference_and_prematurity_policy():
    policy = load(
        "BRAZIL_SISVAN.json"
    )

    assert (
        policy[
            "head_circumference"
        ][
            "brazil_routine_monitoring"
        ]
        == "birth through 24 months"
    )

    assert (
        policy[
            "prematurity"
        ][
            "growth_age_basis"
        ]
        == "corrected_age"
    )

    assert (
        policy[
            "prematurity"
        ][
            "vaccination_age_basis"
        ]
        == "chronological_age"
    )


def test_no_silent_who2007_extrapolation_policy():
    policy = load(
        "BRAZIL_SISVAN.json"
    )

    assert (
        policy[
            "age_policy"
        ][
            "who2007_native_lms_domain"
        ]
        == "60 <= age_months < 229"
    )

    assert any(
        "Do not extrapolate"
        in item
        for item in policy[
            "release_gates"
        ]
    )


def test_growth_attribution_files_are_bundled():
    notice = ROOT / "NOTICE.txt"
    license_file = ROOT / "GPL-3.0.txt"

    assert notice.is_file()
    assert license_file.is_file()

    notice_text = notice.read_text(
        encoding="utf-8"
    )

    license_text = license_file.read_text(
        encoding="utf-8",
        errors="replace",
    )

    assert (
        "WorldHealthOrganization/anthro"
        in notice_text
    )

    assert (
        "WorldHealthOrganization/anthroplus"
        in notice_text
    )

    assert (
        "does not endorse Clinical Reference Hub"
        in notice_text
    )

    assert (
        "GNU GENERAL PUBLIC LICENSE"
        in license_text
    )


def test_growth_redistribution_manifest_hashes():
    sources = load(
        "SOURCES.json"
    )

    redistribution = sources[
        "redistribution"
    ]

    assert (
        redistribution[
            "no_who_endorsement"
        ]
        is True
    )

    assert (
        redistribution[
            "who_emblem_used"
        ]
        is False
    )

    assert (
        redistribution[
            "upstream_package_license_declarations"
        ][
            "anthro"
        ]
        == "GPL-3"
    )

    assert (
        redistribution[
            "upstream_package_license_declarations"
        ][
            "anthroplus"
        ]
        == "GPL (>= 3)"
    )

    for entry in redistribution[
        "bundled_files"
    ]:
        path = ROOT / entry["filename"]

        assert path.is_file()

        assert (
            sha256(path)
            == entry["sha256"]
        )


def test_growth_attribution_document_exists():
    path = (
        ROOT.parents[2]
        / "docs"
        / "WHO_GROWTH_ATTRIBUTION.md"
    )

    assert path.is_file()

    text = path.read_text(
        encoding="utf-8"
    )

    assert (
        "WHO Child Growth Standards 2006"
        in text
    )

    assert (
        "WHO Growth Reference 2007"
        in text
    )

    assert (
        "must not imply WHO endorsement"
        in text
    )
