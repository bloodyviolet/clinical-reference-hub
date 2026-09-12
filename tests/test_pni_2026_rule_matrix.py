from pathlib import Path
from urllib.parse import urlparse
import json


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


MATRIX_PATH = (
    ROOT
    / "data"
    / "clinical-sources"
    / "pni_2026_rule_matrix.json"
)


HARMONIZATION_PATH = (
    ROOT
    / "data"
    / "brazil_clinical_harmonization.json"
)


DOC_PATH = (
    ROOT
    / "docs"
    / "PNI_2026_RULE_MATRIX.md"
)


def matrix():
    return json.loads(
        MATRIX_PATH.read_text(
            encoding="utf-8"
        )
    )


def harmonization():
    return json.loads(
        HARMONIZATION_PATH.read_text(
            encoding="utf-8"
        )
    )


EXPECTED_KEYS = [
    "dtpa",
    "vvsr",
    "hepatitis_b",
    "bcg",
    "pentavalent",
    "ipv",
    "rotavirus",
    "pneumococcal_20",
    "pneumococcal_10",
    "meningococcal_c",
    "influenza",
    "covid19",
    "yellow_fever",
    "meningococcal_acwy",
    "mmr",
    "dtp",
    "varicella",
    "hepatitis_a",
    "hpv4",
    "dengue",
    "dt",
]


EXPECTED_GAPS = [
    "bcg_scar_or_nodule_as_vaccination_evidence",
    "birth_weight_grams",
    "breastfeeding_status",
    "current_pregnancy_episode",
    "disease_event_date",
    "exposure_event_date",
    "maternal_hbsag_status",
    "prior_disease_history",
    "recommendation_layer:travel_or_area_risk",
    "travel_date",
    "travel_destination",
]


def by_key():
    return {
        item[
            "vaccine_key"
        ]:
        item
        for item
        in matrix()[
            "baseline_vaccines"
        ]
    }


def by_overlay():
    return {
        item[
            "overlay_id"
        ]:
        item
        for item
        in matrix()[
            "known_2026_overlays"
        ]
    }


def test_matrix_is_explicitly_not_engine_implementation():
    data = matrix()

    assert (
        data[
            "matrix_status"
        ]
        == "locked_engine_implementation_blocked"
    )

    assert (
        data[
            "does_not_encode_all_granular_dose_branches"
        ]
        is True
    )

    assert (
        data[
            "rule_engine_implementation_allowed"
        ]
        is False
    )


def test_exact_21_baseline_vaccine_families():
    vaccines = (
        matrix()[
            "baseline_vaccines"
        ]
    )

    assert len(
        vaccines
    ) == 21

    assert [
        item[
            "baseline_order"
        ]
        for item
        in vaccines
    ] == list(
        range(
            1,
            22,
        )
    )

    assert [
        item[
            "vaccine_key"
        ]
        for item
        in vaccines
    ] == EXPECTED_KEYS


def test_every_baseline_rule_family_id_is_unique():
    ids = [
        item[
            "baseline_rule_family_id"
        ]
        for item
        in matrix()[
            "baseline_vaccines"
        ]
    ]

    assert len(
        ids
    ) == len(
        set(ids)
    )


def test_every_baseline_rule_remains_unimplemented():
    for item in matrix()[
        "baseline_vaccines"
    ]:
        assert (
            item[
                "engine_rule_implemented"
            ]
            is False
        )


def test_every_baseline_family_requires_assessment_date():
    for item in matrix()[
        "baseline_vaccines"
    ]:
        assert (
            "assessment_date"
            in item[
                "required_input_domains"
            ]
        )


def test_every_baseline_family_retains_source_section_number():
    for (
        expected,
        item,
    ) in enumerate(
        matrix()[
            "baseline_vaccines"
        ],
        start=1,
    ):
        assert (
            item[
                "normative_section_number"
            ]
            == expected
        )

        assert (
            item[
                "normative_pdf_page_index_start"
            ]
            >= 1
        )


def test_history_sensitive_families_include_history_input():
    for item in matrix()[
        "baseline_vaccines"
    ]:
        if item[
            "history_sensitive"
        ]:
            assert (
                "vaccination_history"
                in item[
                    "required_input_domains"
                ]
            )


def test_vpc20_and_vpc10_are_product_history_sensitive():
    vaccines = by_key()

    assert (
        vaccines[
            "pneumococcal_20"
        ][
            "product_history_sensitive"
        ]
        is True
    )

    assert (
        vaccines[
            "pneumococcal_10"
        ][
            "product_history_sensitive"
        ]
        is True
    )


def test_influenza_keeps_routine_and_seasonal_layers_distinct():
    influenza = by_key()[
        "influenza"
    ]

    assert influenza[
        "recommendation_layers"
    ] == [
        "routine",
        "seasonal_strategy",
    ]


def test_hpv_keeps_routine_rescue_and_special_layers_distinct():
    hpv = by_key()[
        "hpv4"
    ]

    assert hpv[
        "recommendation_layers"
    ] == [
        "routine",
        "rescue_strategy",
        "special_condition",
    ]


def test_mmr_and_varicella_have_outbreak_layer():
    vaccines = by_key()

    assert (
        "outbreak_or_blocking"
        in vaccines[
            "mmr"
        ][
            "recommendation_layers"
        ]
    )

    assert (
        "outbreak_or_blocking"
        in vaccines[
            "varicella"
        ][
            "recommendation_layers"
        ]
    )


def test_exact_model_gap_union_is_locked():
    assert (
        matrix()[
            "model_gap_inputs"
        ]
        == EXPECTED_GAPS
    )

    assert (
        matrix()[
            "model_gap_remediation_required"
        ]
        is True
    )


def test_pregnancy_episode_gap_is_explicit_for_dtpa_and_vvsr():
    vaccines = by_key()

    for key in (
        "dtpa",
        "vvsr",
    ):
        assert (
            "current_pregnancy_episode"
            in vaccines[
                key
            ][
                "model_gap_inputs"
            ]
        )


def test_hepatitis_b_exposes_maternal_hbsag_gap():
    assert (
        "maternal_hbsag_status"
        in by_key()[
            "hepatitis_b"
        ][
            "model_gap_inputs"
        ]
    )


def test_bcg_exposes_birth_weight_and_non_dose_evidence_gaps():
    gaps = (
        by_key()[
            "bcg"
        ][
            "model_gap_inputs"
        ]
    )

    assert (
        "birth_weight_grams"
        in gaps
    )

    assert (
        "bcg_scar_or_nodule_as_vaccination_evidence"
        in gaps
    )


def test_yellow_fever_exposes_travel_layer_gap():
    gaps = (
        by_key()[
            "yellow_fever"
        ][
            "model_gap_inputs"
        ]
    )

    assert (
        "travel_destination"
        in gaps
    )

    assert (
        "travel_date"
        in gaps
    )

    assert (
        "recommendation_layer:travel_or_area_risk"
        in gaps
    )


def test_varicella_exposes_disease_and_exposure_gaps():
    gaps = (
        by_key()[
            "varicella"
        ][
            "model_gap_inputs"
        ]
    )

    assert (
        "prior_disease_history"
        in gaps
    )

    assert (
        "exposure_event_date"
        in gaps
    )


def test_dengue_exposes_disease_date_and_breastfeeding_gaps():
    gaps = (
        by_key()[
            "dengue"
        ][
            "model_gap_inputs"
        ]
    )

    assert (
        "prior_disease_history"
        in gaps
    )

    assert (
        "disease_event_date"
        in gaps
    )

    assert (
        "breastfeeding_status"
        in gaps
    )


def test_exact_eight_known_2026_overlays():
    overlays = (
        matrix()[
            "known_2026_overlays"
        ]
    )

    assert len(
        overlays
    ) == 8

    ids = [
        item[
            "overlay_id"
        ]
        for item
        in overlays
    ]

    assert len(
        ids
    ) == len(
        set(ids)
    )


def test_vpc20_transition_preserves_month_precision():
    overlay = by_overlay()[
        "PNI26-PNEUMO-VPC20-TRANSITION-01"
    ]

    assert (
        overlay[
            "effective_from"
        ]
        == "2026-06"
    )

    assert (
        overlay[
            "effective_from_precision"
        ]
        == "month"
    )

    assert (
        overlay[
            "exact_day_asserted"
        ]
        is False
    )

    assert (
        overlay[
            "product_history_required"
        ]
        is True
    )


def test_hpv_rescue_has_explicit_2026_end_date():
    overlay = by_overlay()[
        "PNI26-HPV-RESCUE-15-19-03"
    ]

    assert (
        overlay[
            "routine_age_domain"
        ]
        == "9_to_14_years"
    )

    assert (
        overlay[
            "rescue_age_domain"
        ]
        == "15_to_19_years"
    )

    assert (
        overlay[
            "effective_until"
        ]
        == "2026-12-31"
    )

    assert (
        overlay[
            "routine_and_rescue_must_remain_distinct"
        ]
        is True
    )


def test_influenza_strategy_is_not_universalized_to_north():
    overlay = by_overlay()[
        "PNI26-INFLUENZA-SEASONAL-NE-CO-S-SE-04"
    ]

    assert overlay[
        "regions"
    ] == [
        "Northeast",
        "Central-West",
        "South",
        "Southeast",
    ]

    assert (
        overlay[
            "effective_from"
        ]
        == "2026-03-28"
    )

    assert (
        overlay[
            "effective_until"
        ]
        == "2026-05-30"
    )

    assert (
        overlay[
            "universalize_to_north_region"
        ]
        is False
    )


def test_covid_product_note_does_not_invent_schedule_change():
    overlay = by_overlay()[
        "PNI26-COVID-LP8-1-OPERATIONAL-05"
    ]

    assert (
        overlay[
            "eligibility_or_schedule_change_asserted"
        ]
        is False
    )


def test_local_measles_dose_zero_is_geographically_bounded():
    overlay = by_overlay()[
        "PNI26-MMR-LOCAL-D0-SP-06"
    ]

    assert overlay[
        "scope"
    ] == "local_epidemiologic"

    assert set(
        overlay[
            "municipalities"
        ]
    ) == {
        "São Paulo/SP",
        "Guarulhos/SP",
        "São Bernardo do Campo/SP",
    }

    assert (
        overlay[
            "dose_zero"
        ]
        is True
    )

    assert (
        overlay[
            "valid_for_routine_series"
        ]
        is False
    )

    assert (
        overlay[
            "universalize_outside_named_municipalities"
        ]
        is False
    )


def test_rie_overlay_remains_special_condition_only():
    overlay = by_overlay()[
        "PNI26-RIE-HEXA-DTPA-07"
    ]

    assert (
        overlay[
            "layer"
        ]
        == "special_condition"
    )

    assert (
        overlay[
            "routine_calendar_replacement_asserted"
        ]
        is False
    )


def test_dengue_interchangeability_overlay_requires_product_history():
    overlay = by_overlay()[
        "PNI26-DENGUE-PRODUCT-INTERCHANGE-08"
    ]

    assert (
        overlay[
            "product_history_required"
        ]
        is True
    )

    assert (
        overlay[
            "different_manufacturer_revaccination_not_recommended"
        ]
        is True
    )


def test_all_matrix_urls_are_gov_br():
    urls = [
        matrix()[
            "primary_normative_source"
        ][
            "url"
        ],

        matrix()[
            "continuous_update_registry"
        ][
            "url"
        ],
    ]

    urls.extend(
        overlay[
            "source_url"
        ]
        for overlay
        in matrix()[
            "known_2026_overlays"
        ]
    )

    for url in urls:
        parsed = urlparse(
            url
        )

        assert (
            parsed.scheme
            == "https"
        )

        assert (
            parsed.hostname
            == "www.gov.br"
        )


def test_global_safety_contract_remains_fail_closed():
    safety = (
        matrix()[
            "safety_contract"
        ]
    )

    assert (
        safety[
            "age_only_engine_allowed"
        ]
        is False
    )

    assert (
        safety[
            "unknown_history_equals_zero_dose"
        ]
        is False
    )

    assert (
        safety[
            "routine_and_strategy_layers_may_merge"
        ]
        is False
    )

    assert (
        safety[
            "local_rules_may_be_universalized"
        ]
        is False
    )

    assert (
        safety[
            "special_condition_may_be_silently_inferred"
        ]
        is False
    )

    assert (
        safety[
            "synthetic_vaccination_score_allowed"
        ]
        is False
    )


def test_historical_matrix_block_and_living_remediation_state():
    data = matrix()

    # The BH8C extraction artifact truthfully records that
    # engine implementation was blocked when model gaps existed.
    assert (
        data[
            "rule_engine_implementation_allowed"
        ]
        is False
    )

    assert (
        data[
            "model_gap_remediation_required"
        ]
        is True
    )

    item8 = (
        harmonization()[
            "future_items"
        ][
            "8"
        ]
    )

    # Living governance advances after BH8D remediation.
    assert (
        item8[
            "implementation_state"
        ]
        == "rule_implementation_in_progress"
    )

    assert (
        item8[
            "rule_matrix_state"
        ]
        == "locked"
    )

    assert (
        item8[
            "baseline_vaccine_count"
        ]
        == 21
    )

    assert (
        item8[
            "known_2026_overlay_count"
        ]
        == 8
    )

    assert (
        item8[
            "model_gap_remediation_required"
        ]
        is False
    )

    assert (
        item8[
            "unresolved_model_gap_inputs"
        ]
        == []
    )

    assert (
        item8[
            "rule_engine_implementation_allowed"
        ]
        is True
    )



def test_rule_matrix_document_records_engine_block():
    document = DOC_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "Twenty-one baseline vaccine families"
        in document
    )

    assert (
        "Why engine implementation remains blocked"
        in document
    )

    assert (
        "current-pregnancy episode"
        in document.lower()
    )

    assert (
        "maternal hbsag status"
        in document.lower()
    )

    assert (
        "Birth weight"
        in document
    )

    assert (
        "travel_or_area_risk"
        in document
    )
