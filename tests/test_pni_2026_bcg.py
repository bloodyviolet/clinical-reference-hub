from datetime import date, timedelta

import pytest

import schemas

from clinical_tools.pni_2026 import (
    evaluate_pni_bcg_child_routine,
)


ASSESSMENT_DATE = date(
    2026,
    9,
    11,
)


def history(
    state,
    *,
    doses=None,
):
    return schemas.PniVaccineHistory(
        vaccine_key="bcg",
        history_state=state,
        doses=doses or [],
    )


def dose(
    administration_date,
):
    return schemas.PniDoseRecord(
        administration_date=administration_date,
        product_key="bcg",
        documentation_source="official_registry",
    )


def evidence(
    *,
    record=None,
    scar=None,
    nodule=None,
):
    return schemas.PniBcgVaccinationEvidence(
        vaccination_record_present=record,
        scar_present=scar,
        palpable_nodule_present=nodule,
    )


def evaluate(
    *,
    date_of_birth=date(
        2026,
        8,
        1,
    ),
    history_value=None,
    current_weight_grams=None,
    evidence_value=None,
    special_codes=None,
    epidemiologic_codes=None,
    safety="screened_no_concern",
):
    result = evaluate_pni_bcg_child_routine(
        assessment_date=ASSESSMENT_DATE,
        date_of_birth=date_of_birth,
        history=history_value,
        current_weight_grams=current_weight_grams,
        bcg_vaccination_evidence=evidence_value,
        special_condition_codes=special_codes,
        epidemiologic_context_codes=epidemiologic_codes,
        administration_safety_screen_state=safety,
    )

    validated = (
        schemas
        .PniRuleResult
        .model_validate(
            result
        )
    )

    assert validated.interpretation_pt.strip()
    assert validated.interpretation_en.strip()

    assert (
        validated.interpretation_pt
        != validated.interpretation_en
    )

    assert (
        validated.special_condition_inferred
        is False
    )

    assert (
        validated.synthetic_score_applied
        is False
    )

    return result


def test_rule_id_is_stable():
    from clinical_tools import pni_2026

    assert (
        pni_2026.BCG_CHILD_ROUTINE_RULE_ID
        == "PNI26-BCG-CHILD-ROUTINE-001"
    )


def test_newborn_zero_dose_requires_current_weight():
    result = evaluate(
        date_of_birth=ASSESSMENT_DATE,
        history_value=history(
            "documented_zero_dose"
        ),
        current_weight_grams=None,
    )

    assert (
        result[
            "decision"
        ]
        == "context_required"
    )

    assert result[
        "missing_context"
    ] == [
        "current_weight_grams",
    ]


def test_newborn_1999g_is_deferred():
    result = evaluate(
        date_of_birth=ASSESSMENT_DATE,
        history_value=history(
            "documented_zero_dose"
        ),
        current_weight_grams=1999,
    )

    assert (
        result[
            "decision"
        ]
        == "not_due_now"
    )


def test_newborn_exact_2000g_recommends_when_safe():
    result = evaluate(
        date_of_birth=ASSESSMENT_DATE,
        history_value=history(
            "documented_zero_dose"
        ),
        current_weight_grams=2000,
    )

    assert (
        result[
            "decision"
        ]
        == "recommend_now"
    )


def test_newborn_2001g_recommends_when_safe():
    result = evaluate(
        date_of_birth=ASSESSMENT_DATE,
        history_value=history(
            "documented_zero_dose"
        ),
        current_weight_grams=2001,
    )

    assert (
        result[
            "decision"
        ]
        == "recommend_now"
    )


def test_day_27_still_uses_newborn_weight_gate():
    dob = (
        ASSESSMENT_DATE
        - timedelta(
            days=27,
        )
    )

    result = evaluate(
        date_of_birth=dob,
        history_value=history(
            "documented_zero_dose"
        ),
        current_weight_grams=1999,
    )

    assert (
        result[
            "decision"
        ]
        == "not_due_now"
    )


def test_day_28_no_longer_requires_newborn_weight_context():
    dob = (
        ASSESSMENT_DATE
        - timedelta(
            days=28,
        )
    )

    result = evaluate(
        date_of_birth=dob,
        history_value=history(
            "documented_zero_dose"
        ),
        current_weight_grams=None,
    )

    assert (
        result[
            "decision"
        ]
        == "recommend_now"
    )


def test_sub_2000g_outside_neonatal_period_routes_review():
    dob = (
        ASSESSMENT_DATE
        - timedelta(
            days=40,
        )
    )

    result = evaluate(
        date_of_birth=dob,
        history_value=history(
            "documented_zero_dose"
        ),
        current_weight_grams=1900,
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_day_before_fifth_birthday_remains_routine():
    result = evaluate(
        date_of_birth=date(
            2021,
            9,
            12,
        ),
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "recommend_now"
    )


def test_exact_fifth_birthday_is_not_routine_layer():
    result = evaluate(
        date_of_birth=date(
            2021,
            9,
            11,
        ),
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "not_applicable"
    )


@pytest.mark.parametrize(
    "evidence_value",
    [
        evidence(
            record=True,
        ),
        evidence(
            scar=True,
        ),
        evidence(
            nodule=True,
        ),
    ],
)
def test_each_positive_bcg_evidence_type_satisfies_routine_rule(
    evidence_value,
):
    result = evaluate(
        history_value=history(
            "unknown"
        ),
        evidence_value=evidence_value,
    )

    assert (
        result[
            "decision"
        ]
        == "not_due_now"
    )


def test_documented_dose_satisfies_even_when_scar_is_absent():
    result = evaluate(
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    date(
                        2026,
                        8,
                        1,
                    )
                ),
            ],
        ),
        evidence_value=evidence(
            scar=False,
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "not_due_now"
    )


def test_absent_scar_alone_does_not_trigger_revaccination():
    result = evaluate(
        history_value=history(
            "unknown"
        ),
        evidence_value=evidence(
            scar=False,
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "history_required"
    )


def test_all_assessed_absent_does_not_equal_documented_zero():
    result = evaluate(
        history_value=history(
            "unknown"
        ),
        evidence_value=evidence(
            record=False,
            scar=False,
            nodule=False,
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "history_required"
    )


def test_explicit_zero_plus_all_absent_can_recommend():
    result = evaluate(
        history_value=history(
            "documented_zero_dose"
        ),
        evidence_value=evidence(
            record=False,
            scar=False,
            nodule=False,
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "recommend_now"
    )


def test_explicit_zero_conflicting_with_positive_evidence_requires_reconciliation():
    result = evaluate(
        history_value=history(
            "documented_zero_dose"
        ),
        evidence_value=evidence(
            scar=True,
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "history_required"
    )


def test_unknown_history_without_positive_evidence_requires_history():
    result = evaluate(
        history_value=history(
            "unknown"
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "history_required"
    )


def test_missing_history_requires_history():
    result = evaluate(
        history_value=None,
    )

    assert (
        result[
            "decision"
        ]
        == "history_required"
    )


def test_special_condition_context_routes_out_of_routine():
    result = evaluate(
        history_value=history(
            "documented_zero_dose"
        ),
        special_codes=[
            "hiv_exposure",
        ],
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_epidemiologic_context_routes_out_of_routine():
    result = evaluate(
        history_value=history(
            "documented_zero_dose"
        ),
        epidemiologic_codes=[
            "household_hanseniasis_contact",
        ],
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_special_context_not_suppressed_by_prior_routine_dose():
    result = evaluate(
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    date(
                        2026,
                        8,
                        1,
                    )
                ),
            ],
        ),
        epidemiologic_codes=[
            "household_hanseniasis_contact",
        ],
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_unscreened_due_dose_requires_context():
    result = evaluate(
        history_value=history(
            "documented_zero_dose"
        ),
        safety="not_screened",
    )

    assert (
        result[
            "decision"
        ]
        == "context_required"
    )


def test_safety_concern_routes_special_review():
    result = evaluate(
        history_value=history(
            "documented_zero_dose"
        ),
        safety="screened_concern",
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_no_inter_vaccine_spacing_is_invented():
    result = evaluate(
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert (
        result[
            "recommended_interval_days"
        ]
        is None
    )

    assert (
        result[
            "minimum_interval_days"
        ]
        is None
    )

    assert (
        result[
            "minimum_interval_applied"
        ]
        is False
    )


def test_birth_weight_is_not_an_evaluator_input():
    import inspect

    parameters = (
        inspect
        .signature(
            evaluate_pni_bcg_child_routine
        )
        .parameters
    )

    assert (
        "current_weight_grams"
        in parameters
    )

    assert (
        "birth_weight_grams"
        not in parameters
    )


def test_future_bcg_dose_is_rejected():
    with pytest.raises(
        ValueError,
        match="cannot follow assessment_date",
    ):
        evaluate(
            history_value=history(
                "documented_doses",
                doses=[
                    dose(
                        date(
                            2026,
                            9,
                            12,
                        )
                    ),
                ],
            ),
        )


def test_wrong_vaccine_history_is_rejected():
    wrong = schemas.PniVaccineHistory(
        vaccine_key="hpv4",
        history_state="documented_zero_dose",
    )

    with pytest.raises(
        ValueError,
        match="vaccine_key=bcg",
    ):
        evaluate(
            history_value=wrong,
        )


def test_provenance_is_national_2026():
    result = evaluate(
        history_value=history(
            "documented_zero_dose"
        ),
    )

    provenance = result[
        "provenance"
    ]

    assert (
        provenance[
            "rule_id"
        ]
        == "PNI26-BCG-CHILD-ROUTINE-001"
    )

    assert (
        provenance[
            "authority"
        ]
        == "Ministério da Saúde / SVSA / DPNI"
    )

    assert (
        provenance[
            "source_snapshot_date"
        ]
        == date(
            2026,
            9,
            11,
        )
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "history_value":
                history(
                    "documented_zero_dose"
                ),
        },
        {
            "history_value":
                history(
                    "unknown"
                ),
        },
        {
            "history_value":
                history(
                    "documented_doses",
                    doses=[
                        dose(
                            date(
                                2026,
                                8,
                                1,
                            )
                        ),
                    ],
                ),
        },
        {
            "history_value":
                history(
                    "documented_zero_dose"
                ),
            "safety":
                "not_screened",
        },
        {
            "history_value":
                history(
                    "documented_zero_dose"
                ),
            "special_codes":
                [
                    "special_condition",
                ],
        },
        {
            "date_of_birth":
                date(
                    2021,
                    9,
                    11,
                ),
            "history_value":
                history(
                    "documented_zero_dose"
                ),
        },
    ],
)
def test_representative_results_are_bilingual(
    kwargs,
):
    result = evaluate(
        **kwargs
    )

    assert (
        len(
            result[
                "interpretation_pt"
            ]
        )
        > 20
    )

    assert (
        len(
            result[
                "interpretation_en"
            ]
        )
        > 20
    )

    assert (
        result[
            "interpretation_pt"
        ]
        != result[
            "interpretation_en"
        ]
    )
