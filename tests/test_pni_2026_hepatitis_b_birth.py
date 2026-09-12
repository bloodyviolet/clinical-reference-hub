from datetime import date, timedelta

import pytest

import schemas

from clinical_tools.pni_2026 import (
    evaluate_pni_hepatitis_b_birth_routine,
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
        vaccine_key="hepatitis_b",
        history_state=state,
        doses=doses or [],
    )


def dose(
    administration_date,
):
    return schemas.PniDoseRecord(
        administration_date=administration_date,
        product_key="hepatitis_b",
        documentation_source="official_registry",
    )


def evaluate(
    *,
    date_of_birth=ASSESSMENT_DATE,
    maternal_hbsag_status="negative",
    history_value=None,
    special_codes=None,
    safety="screened_no_concern",
):
    result = evaluate_pni_hepatitis_b_birth_routine(
        assessment_date=ASSESSMENT_DATE,
        date_of_birth=date_of_birth,
        maternal_hbsag_status=maternal_hbsag_status,
        history=history_value,
        special_condition_codes=special_codes,
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
        pni_2026.HEPATITIS_B_BIRTH_RULE_ID
        == "PNI26-HB-BIRTH-ROUTINE-001"
    )


def test_birth_day_zero_dose_negative_maternal_status_recommends_now():
    result = evaluate(
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


def test_positive_maternal_hbsag_routes_perinatal_pathway():
    result = evaluate(
        maternal_hbsag_status="positive",
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )

    assert (
        "imunoglobulina"
        in result[
            "interpretation_pt"
        ].lower()
    )

    assert (
        "immune globulin"
        in result[
            "interpretation_en"
        ].lower()
    )


def test_positive_maternal_status_not_suppressed_by_documented_birth_dose():
    result = evaluate(
        maternal_hbsag_status="positive",
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    ASSESSMENT_DATE
                ),
            ],
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_unknown_maternal_hbsag_routes_review_without_inventing_hbig():
    result = evaluate(
        maternal_hbsag_status="unknown_or_unavailable",
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )

    assert (
        "não inferir automaticamente"
        in result[
            "interpretation_pt"
        ].lower()
    )

    assert (
        "do not automatically infer"
        in result[
            "interpretation_en"
        ].lower()
    )


def test_missing_maternal_status_in_active_window_routes_review():
    result = evaluate(
        maternal_hbsag_status=None,
        history_value=history(
            "documented_zero_dose"
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )

    assert (
        "não deve ser atrasada"
        in result[
            "interpretation_pt"
        ].lower()
    )

    assert (
        "should not be delayed"
        in result[
            "interpretation_en"
        ].lower()
    )


def test_day_before_one_month_birthday_remains_active():
    dob = date(
        2026,
        8,
        12,
    )

    result = evaluate(
        date_of_birth=dob,
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


def test_exact_one_month_birthday_remains_active():
    dob = date(
        2026,
        8,
        11,
    )

    result = evaluate(
        date_of_birth=dob,
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


def test_day_after_one_month_birthday_closes_birth_dose_layer():
    dob = date(
        2026,
        8,
        10,
    )

    result = evaluate(
        date_of_birth=dob,
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

    assert (
        "pentavalente"
        in result[
            "interpretation_pt"
        ].lower()
    )

    assert (
        "pentavalent"
        in result[
            "interpretation_en"
        ].lower()
    )


def test_month_clamping_for_january_31_birth():
    assessment = date(
        2027,
        2,
        28,
    )

    result = evaluate_pni_hepatitis_b_birth_routine(
        assessment_date=assessment,
        date_of_birth=date(
            2027,
            1,
            31,
        ),
        maternal_hbsag_status="negative",
        history=schemas.PniVaccineHistory(
            vaccine_key="hepatitis_b",
            history_state="documented_zero_dose",
        ),
        administration_safety_screen_state="screened_no_concern",
    )

    assert (
        result[
            "decision"
        ]
        == "recommend_now"
    )


def test_documented_birth_window_dose_satisfies_layer():
    result = evaluate(
        date_of_birth=date(
            2026,
            8,
            20,
        ),
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    date(
                        2026,
                        8,
                        20,
                    )
                ),
            ],
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "not_due_now"
    )


def test_historical_birth_window_dose_remains_recognizable_after_window():
    result = evaluate(
        date_of_birth=date(
            2026,
            7,
            1,
        ),
        maternal_hbsag_status="negative",
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    date(
                        2026,
                        7,
                        1,
                    )
                ),
            ],
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "not_due_now"
    )


def test_late_hepatitis_b_dose_does_not_retroactively_become_birth_dose():
    result = evaluate(
        date_of_birth=date(
            2026,
            7,
            1,
        ),
        maternal_hbsag_status="negative",
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    date(
                        2026,
                        9,
                        1,
                    )
                ),
            ],
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "not_applicable"
    )


def test_missing_history_inside_active_window_requires_history():
    result = evaluate(
        history_value=None,
    )

    assert (
        result[
            "decision"
        ]
        == "history_required"
    )


def test_unknown_history_is_not_zero_dose():
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


def test_special_condition_routes_out_of_routine():
    result = evaluate(
        history_value=history(
            "documented_zero_dose"
        ),
        special_codes=[
            "renal_chronic_condition",
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


def test_pentavalent_history_is_not_accepted_as_birth_dose_history():
    wrong = schemas.PniVaccineHistory(
        vaccine_key="pentavalent",
        history_state="documented_doses",
        doses=[
            schemas.PniDoseRecord(
                administration_date=ASSESSMENT_DATE,
                product_key="pentavalent",
                documentation_source="official_registry",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match="vaccine_key=hepatitis_b",
    ):
        evaluate(
            history_value=wrong,
        )


def test_future_hepatitis_b_dose_is_rejected():
    with pytest.raises(
        ValueError,
        match="cannot follow assessment_date",
    ):
        evaluate(
            history_value=history(
                "documented_doses",
                doses=[
                    dose(
                        ASSESSMENT_DATE
                        + timedelta(
                            days=1,
                        )
                    ),
                ],
            ),
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
        == "PNI26-HB-BIRTH-ROUTINE-001"
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
            "maternal_hbsag_status":
                "positive",
            "history_value":
                history(
                    "documented_zero_dose"
                ),
        },
        {
            "maternal_hbsag_status":
                "unknown_or_unavailable",
            "history_value":
                history(
                    "documented_zero_dose"
                ),
        },
        {
            "maternal_hbsag_status":
                None,
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
            "date_of_birth":
                date(
                    2026,
                    8,
                    10,
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
