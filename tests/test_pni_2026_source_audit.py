from pathlib import Path
import json


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

SOURCE_PATH = (
    ROOT
    / "data"
    / "clinical-sources"
    / "pni_2026_brazil.json"
)

HARMONIZATION_PATH = (
    ROOT
    / "data"
    / "brazil_clinical_harmonization.json"
)

DOC_PATH = (
    ROOT
    / "docs"
    / "PNI_2026_BRAZIL_SOURCE_VERIFICATION.md"
)


def source():
    return json.loads(
        SOURCE_PATH.read_text(
            encoding="utf-8"
        )
    )


def harmonization():
    return json.loads(
        HARMONIZATION_PATH.read_text(
            encoding="utf-8"
        )
    )


def test_source_is_national_brazil_standard():
    data = source()

    assert (
        data[
            "source_role"
        ]
        == "national_brazil_standard"
    )

    assert (
        data[
            "brazil_applicability_status"
        ]
        == "national_standard"
    )


def test_source_snapshot_and_baseline_checkpoint():
    data = source()

    assert (
        data[
            "source_snapshot_date"
        ]
        == "2026-09-11"
    )

    assert (
        data[
            "baseline_checkpoint"
        ]
        == "433f89d04cc23ead88f1fd71bf35f13f97a73b4f"
    )


def test_primary_normative_source_has_21_vaccines():
    data = source()

    assert (
        data[
            "primary_normative_source"
        ][
            "baseline_vaccine_count"
        ]
        == 21
    )


def test_all_five_life_course_layers_are_present():
    layers = (
        source()[
            "technical_life_course_calendars"
        ]
    )

    assert set(
        layers
    ) == {
        "child",
        "pregnancy",
        "adolescent_and_young_person",
        "adult",
        "older_person",
    }


def test_source_freshness_is_mandatory():
    update = (
        source()[
            "continuous_update_sources"
        ]
    )

    assert (
        update[
            "source_freshness_required"
        ]
        is True
    )

    assert (
        update[
            "latest_registry_review_date"
        ]
        == "2026-09-11"
    )


def test_vpc20_transition_is_effective_date_sensitive():
    transition = (
        source()[
            "known_2026_midyear_or_time_limited_updates"
        ][
            "pneumococcal_vpc20_transition"
        ]
    )

    assert (
        transition[
            "effective_period_start"
        ]
        == "2026-06"
    )

    assert (
        transition[
            "current_schedule_cannot_be_derived_from_january_only"
        ]
        is True
    )

    assert (
        transition[
            "history_and_product_transition_relevant"
        ]
        is True
    )


def test_hpv_routine_and_rescue_are_separate():
    hpv = (
        source()[
            "known_2026_midyear_or_time_limited_updates"
        ][
            "hpv_rescue_15_to_19"
        ]
    )

    assert (
        hpv[
            "routine_age_domain"
        ]
        == "9_to_14_years"
    )

    assert (
        hpv[
            "rescue_age_domain"
        ]
        == "15_to_19_years"
    )

    assert (
        hpv[
            "strategy_end_date"
        ]
        == "2026-12-31"
    )

    assert (
        hpv[
            "routine_and_rescue_must_remain_distinct"
        ]
        is True
    )


def test_influenza_routine_and_strategy_layers_are_separate():
    influenza = (
        source()[
            "known_2026_midyear_or_time_limited_updates"
        ][
            "influenza_2026"
        ]
    )

    assert influenza[
        "routine_groups"
    ] == [
        "children_6_months_to_under_6_years",
        "pregnant_people",
        "people_age_60_or_older",
    ]

    assert (
        influenza[
            "seasonal_strategy_includes_additional_priority_groups"
        ]
        is True
    )

    assert (
        influenza[
            "routine_and_campaign_groups_must_remain_distinct"
        ]
        is True
    )


def test_pregnancy_week_context_examples_are_locked():
    pregnancy = (
        source()[
            "pregnancy_examples_requiring_context"
        ]
    )

    assert (
        pregnancy[
            "dtpa"
        ][
            "from_gestational_week"
        ]
        == 20
    )

    assert (
        pregnancy[
            "dtpa"
        ][
            "each_pregnancy"
        ]
        is True
    )

    assert (
        pregnancy[
            "maternal_rsv_vaccine"
        ][
            "from_gestational_week"
        ]
        == 28
    )

    assert (
        pregnancy[
            "maternal_rsv_vaccine"
        ][
            "each_pregnancy"
        ]
        is True
    )


def test_engine_must_not_be_age_only():
    engine = (
        source()[
            "engine_architecture_requirements"
        ]
    )

    assert (
        engine[
            "age_only_due_list_allowed"
        ]
        is False
    )

    assert (
        engine[
            "vaccination_history_required_when_rule_depends_on_history"
        ]
        is True
    )

    assert (
        engine[
            "assessment_date_required"
        ]
        is True
    )

    assert (
        engine[
            "effective_date_versioning_required"
        ]
        is True
    )


def test_unknown_history_and_special_conditions_fail_closed():
    engine = (
        source()[
            "engine_architecture_requirements"
        ]
    )

    assert (
        engine[
            "unknown_history_must_remain_unknown_when_source_requires_history"
        ]
        is True
    )

    assert (
        engine[
            "automatic_inference_of_special_condition"
        ]
        is False
    )


def test_routine_strategy_and_special_layers_are_separate():
    engine = (
        source()[
            "engine_architecture_requirements"
        ]
    )

    assert (
        engine[
            "routine_and_strategy_layers_must_be_distinct"
        ]
        is True
    )

    assert (
        engine[
            "special_clinical_situation_layer_must_be_distinct"
        ]
        is True
    )

    assert (
        engine[
            "local_or_outbreak_rules_must_not_be_universalized"
        ]
        is True
    )


def test_recommended_and_minimum_intervals_are_distinct():
    assert (
        source()[
            "engine_architecture_requirements"
        ][
            "recommended_and_minimum_intervals_must_be_distinct"
        ]
        is True
    )


def test_no_synthetic_vaccination_score():
    assert (
        source()[
            "engine_architecture_requirements"
        ][
            "synthetic_vaccination_score_allowed"
        ]
        is False
    )


def test_exact_durable_boundary_ids():
    ids = [
        item["id"]
        for item in source()[
            "durable_boundaries"
        ]
    ]

    assert ids == [
        "PNI-SOURCE-FRESHNESS-01",
        "PNI-HISTORY-02",
        "PNI-UNKNOWN-HISTORY-03",
        "PNI-ROUTINE-STRATEGY-04",
        "PNI-SPECIAL-CONDITION-05",
        "PNI-INTERVALS-06",
        "PNI-EFFECTIVE-DATE-07",
        "PNI-HPV-RESCUE-08",
        "PNI-INFLUENZA-LAYERS-09",
        "PNI-PREGNANCY-CONTEXT-10",
        "PNI-LOCAL-EPIDEMIOLOGY-11",
        "PNI-NO-SYNTHETIC-SCORE-12",
    ]


def test_source_precedence_is_explicit():
    ranks = [
        entry["rank"]
        for entry in source()[
            "source_precedence"
        ]
    ]

    assert ranks == [
        1,
        2,
        3,
        4,
        5,
        6,
    ]


def test_harmonization_gate_matches_source_contract():
    item8 = (
        harmonization()[
            "future_items"
        ][
            "8"
        ]
    )

    assert (
        item8[
            "implementation_state"
        ]
        == "rule_implementation_in_progress"
    )

    assert (
        item8[
            "brazil_applicability_status"
        ]
        == "national_standard"
    )

    assert (
        item8[
            "engine_architecture"
        ]
        == "history_aware_effective_date_rule_engine"
    )

    assert (
        item8[
            "age_only_due_list_allowed"
        ]
        is False
    )

    assert (
        item8[
            "routine_strategy_merge_allowed"
        ]
        is False
    )

    assert (
        item8[
            "special_condition_silent_inference_allowed"
        ]
        is False
    )

    assert (
        item8[
            "synthetic_vaccination_score_allowed"
        ]
        is False
    )


def test_verification_document_contains_all_durable_boundaries():
    document = DOC_PATH.read_text(
        encoding="utf-8"
    )

    for boundary in (
        source()[
            "durable_boundaries"
        ]
    ):
        assert (
            boundary[
                "id"
            ]
            in document
        )
