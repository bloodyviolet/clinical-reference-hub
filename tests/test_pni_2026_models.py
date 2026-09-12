from datetime import date

import pytest

from pydantic import ValidationError

import schemas


ASSESSMENT_DATE = date(
    2026,
    9,
    11,
)


DOB = date(
    1990,
    1,
    1,
)


def dose(
    *,
    administration_date=date(
        2026,
        1,
        10,
    ),
    product_key="example-product",
):
    return schemas.PniDoseRecord(
        administration_date=administration_date,
        product_key=product_key,
        product_name="Example product",
        dose_number=1,
        dose_label="dose_1",
        documentation_source="official_registry",
    )


def context(
    **overrides,
):
    values = {
        "assessment_date":
            ASSESSMENT_DATE,

        "date_of_birth":
            DOB,

        "pregnancy_status":
            "not_applicable",
    }

    values.update(
        overrides
    )

    return schemas.PniAssessmentContext(
        **values
    )


def provenance(
    **overrides,
):
    values = {
        "rule_id":
            "PNI-TEST-001",

        "authority":
            "Ministério da Saúde / DPNI",

        "authority_rank":
            2,

        "source_title":
            "2026 test source",

        "source_url":
            "https://www.gov.br/saude/",

        "source_snapshot_date":
            ASSESSMENT_DATE,

        "rule_effective_from":
            date(
                2026,
                1,
                1,
            ),
    }

    values.update(
        overrides
    )

    return schemas.PniRuleProvenance(
        **values
    )


def rule_result(
    **overrides,
):
    values = {
        "vaccine_key":
            "example",

        "layer":
            "routine",

        "decision":
            "not_due_now",

        "assessment_date":
            ASSESSMENT_DATE,

        "provenance":
            provenance(),

        "interpretation_pt":
            "Resultado de teste.",

        "interpretation_en":
            "Test result.",
    }

    values.update(
        overrides
    )

    return schemas.PniRuleResult(
        **values
    )


def test_documented_zero_dose_is_distinct_from_unknown():
    zero = schemas.PniVaccineHistory(
        vaccine_key="hpv",
        history_state="documented_zero_dose",
    )

    unknown = schemas.PniVaccineHistory(
        vaccine_key="hpv",
        history_state="unknown",
    )

    assert (
        zero.history_state
        != unknown.history_state
    )

    assert zero.doses == []
    assert unknown.doses == []


def test_unknown_history_rejects_dose_records():
    with pytest.raises(
        ValidationError,
        match="unknown history",
    ):
        schemas.PniVaccineHistory(
            vaccine_key="hpv",
            history_state="unknown",
            doses=[
                dose(),
            ],
        )


def test_unknown_history_rejects_reported_prior_doses():
    with pytest.raises(
        ValidationError,
        match="unknown history",
    ):
        schemas.PniVaccineHistory(
            vaccine_key="hpv",
            history_state="unknown",
            reported_prior_doses_without_exact_dates=1,
        )


def test_documented_zero_rejects_prior_dose_evidence():
    with pytest.raises(
        ValidationError,
        match="zero-dose",
    ):
        schemas.PniVaccineHistory(
            vaccine_key="hpv",
            history_state="documented_zero_dose",
            doses=[
                dose(),
            ],
        )


def test_documented_doses_requires_exact_dated_dose():
    with pytest.raises(
        ValidationError,
        match="at least one dated dose",
    ):
        schemas.PniVaccineHistory(
            vaccine_key="hpv",
            history_state="documented_doses",
            reported_prior_doses_without_exact_dates=1,
        )


def test_documented_doses_accepts_exact_dose():
    history = schemas.PniVaccineHistory(
        vaccine_key="pneumococcal",
        history_state="documented_doses",
        doses=[
            dose(
                product_key="vpc10",
            ),
        ],
    )

    assert (
        history.doses[
            0
        ].product_key
        == "vpc10"
    )


def test_partial_record_can_preserve_undated_reported_doses():
    history = schemas.PniVaccineHistory(
        vaccine_key="pneumococcal",
        history_state="partial_record",
        reported_prior_doses_without_exact_dates=2,
    )

    assert (
        history.reported_prior_doses_without_exact_dates
        == 2
    )


def test_partial_record_requires_some_evidence():
    with pytest.raises(
        ValidationError,
        match="partial_record",
    ):
        schemas.PniVaccineHistory(
            vaccine_key="pneumococcal",
            history_state="partial_record",
        )


def test_dose_preserves_product_identity_for_transition_rules():
    record = dose(
        product_key="vpc20",
    )

    assert record.product_key == "vpc20"

    assert (
        record.administration_date
        == date(
            2026,
            1,
            10,
        )
    )


def test_assessment_date_cannot_precede_birth():
    with pytest.raises(
        ValidationError,
        match="cannot precede",
    ):
        context(
            assessment_date=date(
                1989,
                12,
                31,
            ),
        )


def test_pregnancy_context_can_preserve_gestational_week():
    result = context(
        pregnancy_status="pregnant",
        gestational_age_weeks=28,
    )

    assert (
        result.gestational_age_weeks
        == 28
    )


def test_gestational_week_requires_explicit_pregnancy():
    with pytest.raises(
        ValidationError,
        match="requires pregnancy_status=pregnant",
    ):
        context(
            pregnancy_status="not_pregnant",
            gestational_age_weeks=20,
        )


def test_pregnancy_and_postpartum_cannot_coexist():
    with pytest.raises(
        ValidationError,
        match="cannot coexist",
    ):
        context(
            pregnancy_status="pregnant",
            gestational_age_weeks=30,
            postpartum_days=10,
        )


def test_context_preserves_explicit_special_and_epidemiologic_codes():
    result = context(
        occupational_groups=[
            "health_worker",
        ],
        special_condition_codes=[
            "explicit_condition",
        ],
        epidemiologic_context_codes=[
            "explicit_exposure",
        ],
        federative_unit="PE",
        municipality="Recife",
    )

    assert result.occupational_groups == [
        "health_worker",
    ]

    assert result.special_condition_codes == [
        "explicit_condition",
    ]

    assert result.epidemiologic_context_codes == [
        "explicit_exposure",
    ]


def test_request_defaults_to_routine_layer_only():
    request = schemas.PniAssessmentRequest(
        context=context(),
    )

    assert request.requested_layers == [
        "routine",
    ]


def test_request_can_explicitly_select_distinct_layers():
    request = schemas.PniAssessmentRequest(
        context=context(),
        requested_layers=[
            "routine",
            "seasonal_strategy",
            "rescue_strategy",
            "special_condition",
        ],
    )

    assert request.requested_layers == [
        "routine",
        "seasonal_strategy",
        "rescue_strategy",
        "special_condition",
    ]


def test_request_rejects_duplicate_layers():
    with pytest.raises(
        ValidationError,
        match="must not contain duplicates",
    ):
        schemas.PniAssessmentRequest(
            context=context(),
            requested_layers=[
                "routine",
                "routine",
            ],
        )


def test_request_rejects_duplicate_vaccine_histories():
    history = schemas.PniVaccineHistory(
        vaccine_key="hpv",
        history_state="unknown",
    )

    with pytest.raises(
        ValidationError,
        match="duplicate vaccine history",
    ):
        schemas.PniAssessmentRequest(
            context=context(),
            histories=[
                history,
                history,
            ],
        )


def test_provenance_preserves_effective_dates():
    result = provenance(
        rule_effective_from=date(
            2026,
            6,
            1,
        ),
        rule_effective_until=date(
            2026,
            12,
            31,
        ),
    )

    assert (
        result.rule_effective_from
        == date(
            2026,
            6,
            1,
        )
    )

    assert (
        result.rule_effective_until
        == date(
            2026,
            12,
            31,
        )
    )


def test_provenance_rejects_reversed_effective_window():
    with pytest.raises(
        ValidationError,
        match="cannot precede",
    ):
        provenance(
            rule_effective_from=date(
                2026,
                12,
                31,
            ),
            rule_effective_until=date(
                2026,
                6,
                1,
            ),
        )


def test_future_recommendation_requires_date():
    with pytest.raises(
        ValidationError,
        match="requires recommended_date",
    ):
        rule_result(
            decision="future_recommendation",
        )


def test_history_required_decision_requires_explicit_flag():
    with pytest.raises(
        ValidationError,
        match="history_required decision",
    ):
        rule_result(
            decision="history_required",
            history_required=False,
        )


def test_context_required_decision_requires_missing_context():
    with pytest.raises(
        ValidationError,
        match="missing_context",
    ):
        rule_result(
            decision="context_required",
        )


def test_recommended_and_minimum_intervals_are_separate():
    result = rule_result(
        decision="future_recommendation",
        recommended_date=date(
            2026,
            10,
            11,
        ),
        recommended_interval_days=30,
        minimum_interval_days=21,
        minimum_interval_applied=False,
    )

    assert (
        result.recommended_interval_days
        == 30
    )

    assert (
        result.minimum_interval_days
        == 21
    )

    assert (
        result.minimum_interval_applied
        is False
    )


def test_minimum_interval_applied_requires_minimum_interval():
    with pytest.raises(
        ValidationError,
        match="requires minimum_interval_days",
    ):
        rule_result(
            minimum_interval_applied=True,
        )


def test_minimum_interval_cannot_exceed_recommended_interval():
    with pytest.raises(
        ValidationError,
        match="cannot exceed recommended",
    ):
        rule_result(
            recommended_interval_days=21,
            minimum_interval_days=30,
        )


def test_special_condition_is_never_marked_as_inferred():
    result = rule_result(
        layer="special_condition",
        decision="special_pathway_review",
    )

    assert (
        result.special_condition_inferred
        is False
    )


def test_rule_result_has_no_synthetic_score():
    result = rule_result()

    assert (
        result.synthetic_score_applied
        is False
    )


def test_assessment_response_keeps_layers_separate():
    response = schemas.PniAssessmentResponse(
        tool="brazil_pni_2026",
        assessment_date=ASSESSMENT_DATE,
        source_snapshot_date=ASSESSMENT_DATE,
        requested_layers=[
            "routine",
            "rescue_strategy",
        ],
        results=[
            rule_result(
                layer="routine",
            ),
            rule_result(
                layer="rescue_strategy",
                decision="context_required",
                missing_context=[
                    "vaccination_history",
                ],
            ),
        ],
    )

    assert (
        response.routine_strategy_layers_merged
        is False
    )

    assert (
        response.special_condition_inference_applied
        is False
    )

    assert (
        response.synthetic_score_applied
        is False
    )


def _json_schema_enum_values(
    root_schema,
    node,
):
    """
    Resolve enum values regardless of whether Pydantic emits a Literal
    inline or through $ref / allOf / anyOf.
    """

    if "enum" in node:
        return node["enum"]

    if "$ref" in node:
        reference = node["$ref"]

        prefix = "#/$defs/"

        assert reference.startswith(
            prefix
        )

        definition_name = reference[
            len(prefix):
        ]

        return _json_schema_enum_values(
            root_schema,
            root_schema[
                "$defs"
            ][
                definition_name
            ],
        )

    for key in (
        "allOf",
        "anyOf",
        "oneOf",
    ):
        for candidate in node.get(
            key,
            []
        ):
            try:
                return _json_schema_enum_values(
                    root_schema,
                    candidate,
                )
            except AssertionError:
                pass

    raise AssertionError(
        f"no enum found in schema node: {node!r}"
    )


def _pni_schema_enum_values(
    root_schema,
    node,
):
    """
    Return enum values regardless of whether Pydantic emits
    a Literal inline or through $ref/allOf/anyOf/oneOf.
    """

    if "enum" in node:
        return node["enum"]

    if "$ref" in node:
        reference = node["$ref"]

        prefix = "#/$defs/"

        if not reference.startswith(
            prefix
        ):
            raise AssertionError(
                f"unsupported schema reference: {reference}"
            )

        definition_name = reference[
            len(prefix):
        ]

        return _pni_schema_enum_values(
            root_schema,
            root_schema[
                "$defs"
            ][
                definition_name
            ],
        )

    for composition_key in (
        "allOf",
        "anyOf",
        "oneOf",
    ):
        for candidate in node.get(
            composition_key,
            []
        ):
            try:
                return _pni_schema_enum_values(
                    root_schema,
                    candidate,
                )
            except AssertionError:
                continue

    raise AssertionError(
        f"no enum found in schema node: {node!r}"
    )


def test_json_schema_exposes_explicit_history_state_enum():
    schema = (
        schemas
        .PniVaccineHistory
        .model_json_schema()
    )

    node = schema[
        "properties"
    ][
        "history_state"
    ]

    values = _pni_schema_enum_values(
        schema,
        node,
    )

    assert values == [
        "documented_zero_dose",
        "documented_doses",
        "partial_record",
        "unknown",
    ]



def test_json_schema_exposes_six_separate_recommendation_layers():
    schema = (
        schemas
        .PniAssessmentRequest
        .model_json_schema()
    )

    node = schema[
        "properties"
    ][
        "requested_layers"
    ][
        "items"
    ]

    values = _pni_schema_enum_values(
        schema,
        node,
    )

    assert values == [
        "routine",
        "seasonal_strategy",
        "rescue_strategy",
        "outbreak_or_blocking",
        "travel_or_area_risk",
        "special_condition",
    ]





def test_bh8d_pregnancy_episode_key_links_context_and_dose():
    current = context(
        pregnancy_status="pregnant",
        gestational_age_weeks=28,
        pregnancy_episode_key="pregnancy-2026-A",
    )

    historical_dose = schemas.PniDoseRecord(
        administration_date=date(
            2026,
            8,
            1,
        ),
        pregnancy_episode_key="pregnancy-2026-A",
        product_key="vvsr",
        documentation_source="official_registry",
    )

    assert (
        current.pregnancy_episode_key
        == historical_dose.pregnancy_episode_key
    )


def test_bh8d_pregnancy_episode_key_requires_pregnancy():
    with pytest.raises(
        ValidationError,
        match="pregnancy_episode_key requires",
    ):
        context(
            pregnancy_status="not_pregnant",
            pregnancy_episode_key="invalid",
        )


def test_bh8d_maternal_hbsag_unknown_is_not_negative():
    result = context(
        maternal_hbsag_status="unknown_or_unavailable",
    )

    assert (
        result.maternal_hbsag_status
        != "negative"
    )


def test_bh8d_birth_weight_is_preserved_without_arbitrary_upper_cap():
    result = context(
        birth_weight_grams=1999,
    )

    assert (
        result.birth_weight_grams
        == 1999
    )


def test_bh8d_bcg_evidence_preserves_unknown_vs_absent():
    evidence = schemas.PniBcgVaccinationEvidence(
        vaccination_record_present=None,
        scar_present=False,
        palpable_nodule_present=None,
    )

    assert (
        evidence.scar_present
        is False
    )

    assert (
        evidence.vaccination_record_present
        is None
    )


def test_bh8d_empty_bcg_evidence_is_rejected():
    with pytest.raises(
        ValidationError,
        match="at least one assessed",
    ):
        schemas.PniBcgVaccinationEvidence()


def test_bh8d_documented_and_reported_disease_are_distinct():
    documented = schemas.PniDiseaseEvent(
        disease_key="dengue",
        event_date=date(
            2026,
            1,
            1,
        ),
        evidence_source="documented",
    )

    reported = schemas.PniDiseaseEvent(
        disease_key="dengue",
        event_date=None,
        evidence_source="patient_or_caregiver_report",
    )

    assert (
        documented.evidence_source
        != reported.evidence_source
    )

    assert (
        reported.event_date
        is None
    )


def test_bh8d_future_disease_event_is_rejected():
    with pytest.raises(
        ValidationError,
        match="disease event_date",
    ):
        context(
            disease_history=[
                schemas.PniDiseaseEvent(
                    disease_key="dengue",
                    event_date=date(
                        2026,
                        9,
                        12,
                    ),
                    evidence_source="documented",
                ),
            ],
        )


def test_bh8d_future_exposure_event_is_rejected():
    with pytest.raises(
        ValidationError,
        match="exposure event_date",
    ):
        context(
            exposure_events=[
                schemas.PniExposureEvent(
                    exposure_key="varicella_contact",
                    event_date=date(
                        2026,
                        9,
                        12,
                    ),
                    evidence_source="patient_or_caregiver_report",
                ),
            ],
        )


def test_bh8d_breastfeeding_is_separate_from_pregnancy():
    result = context(
        pregnancy_status="not_pregnant",
        breastfeeding=schemas.PniBreastfeedingContext(
            status="breastfeeding",
            youngest_breastfed_child_date_of_birth=date(
                2026,
                6,
                1,
            ),
        ),
    )

    assert (
        result.breastfeeding.status
        == "breastfeeding"
    )

    assert (
        result.pregnancy_status
        == "not_pregnant"
    )


def test_bh8d_non_breastfeeding_rejects_child_dob():
    with pytest.raises(
        ValidationError,
        match="requires breastfeeding status",
    ):
        schemas.PniBreastfeedingContext(
            status="not_breastfeeding",
            youngest_breastfed_child_date_of_birth=date(
                2026,
                6,
                1,
            ),
        )


def test_bh8d_future_breastfed_child_birth_is_rejected():
    with pytest.raises(
        ValidationError,
        match="cannot follow assessment_date",
    ):
        context(
            breastfeeding=schemas.PniBreastfeedingContext(
                status="breastfeeding",
                youngest_breastfed_child_date_of_birth=date(
                    2026,
                    9,
                    12,
                ),
            ),
        )


def test_bh8d_travel_context_preserves_destination_and_dates():
    travel = schemas.PniTravelContext(
        destination_country="Brazil",
        destination_federative_unit="SP",
        destination_municipality="Campinas",
        departure_date=date(
            2026,
            10,
            1,
        ),
        return_date=date(
            2026,
            10,
            10,
        ),
    )

    assert (
        travel.destination_federative_unit
        == "SP"
    )

    assert (
        travel.departure_date
        == date(
            2026,
            10,
            1,
        )
    )


def test_bh8d_travel_return_cannot_precede_departure():
    with pytest.raises(
        ValidationError,
        match="cannot precede",
    ):
        schemas.PniTravelContext(
            destination_country="Brazil",
            destination_federative_unit="SP",
            departure_date=date(
                2026,
                10,
                10,
            ),
            return_date=date(
                2026,
                10,
                1,
            ),
        )


def test_bh8d_travel_area_risk_is_distinct_request_layer():
    request = schemas.PniAssessmentRequest(
        context=context(),
        requested_layers=[
            "routine",
            "travel_or_area_risk",
        ],
    )

    assert request.requested_layers == [
        "routine",
        "travel_or_area_risk",
    ]
