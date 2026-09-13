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
    / "four_gcsp.json"
)

DOC_PATH = (
    ROOT
    / "docs"
    / "FOUR_GCSP_SOURCE_VERIFICATION.md"
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


def test_source_dossier_and_verification_document_exist():
    assert SOURCE_PATH.is_file()
    assert DOC_PATH.is_file()


def test_item10_source_review_is_complete_but_implementation_pending():
    data = source()

    assert (
        data["implementation_status"]
        == "source_review_complete_implementation_pending"
    )

    item10 = governance()[
        "future_items"
    ][
        "10"
    ]

    assert (
        item10["feature"]
        == "FOUR Score + GCS-P"
    )

    assert (
        item10["implementation_state"]
        == "source_review_complete_implementation_pending"
    )


def test_source_identities_are_pinned():
    data = source()[
        "sources"
    ]

    assert (
        data["gcsp_original"]["doi"]
        == "10.3171/2017.12.JNS172780"
    )

    assert (
        data["gcsp_original"]["pmid"]
        == "29631516"
    )

    assert (
        data["four_original"]["doi"]
        == "10.1002/ana.20611"
    )

    assert (
        data["four_original"]["pmid"]
        == "16178024"
    )

    assert (
        data[
            "four_brazil_validation"
        ]["doi"]
        == "10.1590/1980-265X-TCE-2021-0427pt"
    )

    assert (
        data[
            "four_brazil_validation"
        ]["sample_adults"]
        == 188
    )


def test_canonical_and_brazilian_authority_are_separated():
    sources = source()[
        "sources"
    ]

    assert (
        sources[
            "gcs_structured_approach"
        ]["role"]
        == "canonical_international"
    )

    assert (
        sources[
            "gcsp_original"
        ]["role"]
        == "canonical_peer_reviewed"
    )

    assert (
        sources[
            "brazil_ministry_gcs_p_context"
        ]["role"]
        == "brazilian_contextual_official"
    )

    assert (
        sources[
            "four_brazil_validation"
        ]["role"]
        == "brazilian_peer_reviewed_validation"
    )

    brazil = source()[
        "brazil_applicability"
    ]

    assert (
        brazil[
            "national_replacement_numeric_model_identified"
        ]
        is False
    )


def test_gcs_contract_preserves_nt_without_numeric_total():
    contract = source()[
        "gcs_contract"
    ]

    assert contract[
        "numeric_total_min"
    ] == 3

    assert contract[
        "numeric_total_max"
    ] == 15

    assert all(
        component[
            "nt_allowed"
        ]
        is True
        for component in contract[
            "components"
        ].values()
    )

    assert (
        contract[
            "direct_total_without_components_allowed"
        ]
        is False
    )

    assert "NT" in contract[
        "nt_rule"
    ]


def test_gcsp_contract():
    contract = source()[
        "gcsp_contract"
    ]

    assert (
        contract["formula"]
        == "GCS_total - pupil_reactivity_score"
    )

    assert contract[
        "pupil_reactivity_score"
    ] == {
        "zero_unreactive":
            0,
        "one_unreactive":
            1,
        "two_unreactive":
            2,
    }

    assert contract[
        "numeric_min"
    ] == 1

    assert contract[
        "numeric_max"
    ] == 15

    assert (
        contract[
            "requires_numeric_gcs_total"
        ]
        is True
    )

    assert (
        contract[
            "unknown_pupil_state_numeric_result"
        ]
        is False
    )

    assert (
        contract[
            "outcome_probability_tables_in_scope"
        ]
        is False
    )


def test_four_contract():
    contract = source()[
        "four_contract"
    ]

    assert set(
        contract[
            "domains"
        ]
    ) == {
        "eye",
        "motor",
        "brainstem",
        "respiration",
    }

    assert all(
        value == {
            "min":
                0,
            "max":
                4,
        }
        for value in contract[
            "domains"
        ].values()
    )

    assert contract[
        "numeric_total_min"
    ] == 0

    assert contract[
        "numeric_total_max"
    ] == 16

    assert (
        contract[
            "all_domains_required_for_numeric_total"
        ]
        is True
    )

    assert (
        contract[
            "derived_from_gcs"
        ]
        is False
    )

    assert (
        contract[
            "mortality_or_treatment_cutoff"
        ]
        is None
    )


def _gcs_total(
    eye,
    verbal,
    motor,
):
    values = (
        eye,
        verbal,
        motor,
    )

    if "NT" in values:
        return None

    assert (
        isinstance(
            eye,
            int,
        )
        and not isinstance(
            eye,
            bool,
        )
        and 1 <= eye <= 4
    )

    assert (
        isinstance(
            verbal,
            int,
        )
        and not isinstance(
            verbal,
            bool,
        )
        and 1 <= verbal <= 5
    )

    assert (
        isinstance(
            motor,
            int,
        )
        and not isinstance(
            motor,
            bool,
        )
        and 1 <= motor <= 6
    )

    return (
        eye
        + verbal
        + motor
    )


def _gcsp(
    gcs_total,
    prs,
):
    if (
        gcs_total is None
        or prs is None
    ):
        return None

    assert (
        isinstance(
            gcs_total,
            int,
        )
        and not isinstance(
            gcs_total,
            bool,
        )
        and 3 <= gcs_total <= 15
    )

    assert prs in {
        0,
        1,
        2,
    }

    result = (
        gcs_total
        - prs
    )

    assert 1 <= result <= 15

    return result


def _four_total(
    eye,
    motor,
    brainstem,
    respiration,
):
    values = (
        eye,
        motor,
        brainstem,
        respiration,
    )

    if any(
        value is None
        for value in values
    ):
        return None

    assert all(
        isinstance(
            value,
            int,
        )
        and not isinstance(
            value,
            bool,
        )
        and 0 <= value <= 4
        for value in values
    )

    return sum(
        values
    )


def test_reference_vectors_are_self_consistent():
    vectors = source()[
        "reference_vectors"
    ]

    assert len(
        vectors["gcs"]
    ) == 5

    assert len(
        vectors["gcsp"]
    ) == 6

    assert len(
        vectors["four"]
    ) == 5

    for vector in vectors[
        "gcs"
    ]:
        assert (
            _gcs_total(
                vector["eye"],
                vector["verbal"],
                vector["motor"],
            )
            == vector[
                "expected_total"
            ]
        )

    for vector in vectors[
        "gcsp"
    ]:
        assert (
            _gcsp(
                vector[
                    "gcs_total"
                ],
                vector[
                    "prs"
                ],
            )
            == vector[
                "expected"
            ]
        )

    for vector in vectors[
        "four"
    ]:
        assert (
            _four_total(
                vector["eye"],
                vector["motor"],
                vector[
                    "brainstem"
                ],
                vector[
                    "respiration"
                ],
            )
            == vector[
                "expected_total"
            ]
        )


def test_cross_instrument_safety_firewall():
    safety = source()[
        "safety_boundaries"
    ]

    assert (
        safety[
            "gcs_and_four_independent"
        ]
        is True
    )

    assert (
        safety[
            "gcsp_does_not_replace_gcs_components"
        ]
        is True
    )

    assert (
        safety[
            "pupil_findings_remain_visible"
        ]
        is True
    )

    assert (
        safety[
            "four_brainstem_findings_remain_visible"
        ]
        is True
    )

    assert (
        safety[
            "four_respiration_findings_remain_visible"
        ]
        is True
    )

    assert (
        safety[
            "synthetic_cross_instrument_score"
        ]
        is False
    )

    assert (
        safety[
            "invented_prognostic_threshold"
        ]
        is False
    )

    assert (
        safety[
            "pediatric_extension"
        ]
        == "out_of_scope_pending_separate_qualification"
    )


def test_this_tranche_does_not_claim_implementation():
    boundaries = source()[
        "implementation_boundaries"
    ]

    assert (
        boundaries[
            "authoritative_python_core_required"
        ]
        is True
    )

    assert (
        boundaries[
            "browser_only_authority_allowed"
        ]
        is False
    )

    assert (
        boundaries[
            "api_ui_pwa_this_tranche"
        ]
        is False
    )

    assert (
        boundaries[
            "clinical_core_this_tranche"
        ]
        is False
    )

    assert (
        boundaries[
            "legacy_browser_gcs_replacement_this_tranche"
        ]
        is False
    )


def test_verification_document_locks_clinical_boundaries():
    text = DOC_PATH.read_text(
        encoding="utf-8"
    )

    required = (
        "GCS-P = numeric GCS total - Pupil Reactivity Score",
        "no numeric GCS total is emitted when any component is `NT`",
        "numeric total therefore ranges from 0 through 16",
        "188 adults",
        "Do not combine GCS, GCS-P and FOUR into a synthetic",
        "Do not invent mortality, treatment or disposition cutoffs",
        "Pediatric extensions are outside this adult Item 10 contract",
        "does not create:",
        "a Python scoring implementation",
    )

    for marker in required:
        assert marker in text, marker
