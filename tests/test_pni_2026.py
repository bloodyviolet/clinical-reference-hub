from datetime import date

import pytest

import schemas

from clinical_tools import pni_2026


ASSESSMENT_DATE = date(
    2026,
    9,
    11,
)


def history(
    state,
    *,
    doses=None,
    undated=0,
):
    return schemas.PniVaccineHistory(
        vaccine_key="vvsr",
        history_state=state,
        doses=doses or [],
        reported_prior_doses_without_exact_dates=undated,
    )


def dose(
    *,
    administration_date=date(
        2026,
        8,
        1,
    ),
    episode="pregnancy-current",
):
    return schemas.PniDoseRecord(
        administration_date=administration_date,
        pregnancy_episode_key=episode,
        product_key="vvsr",
        product_name="VVSR",
        dose_number=1,
        documentation_source="official_registry",
    )


def evaluate(
    **overrides,
):
    values = {
        "assessment_date":
            ASSESSMENT_DATE,

        "pregnancy_status":
            "pregnant",

        "gestational_age_weeks":
            28,

        "pregnancy_episode_key":
            "pregnancy-current",

        "history":
            history(
                "documented_zero_dose"
            ),
    }

    values.update(
        overrides
    )

    result = (
        pni_2026
        .evaluate_pni_vvsr_routine(
            **values
        )
    )

    schemas.PniRuleResult.model_validate(
        result
    )

    return result


def test_vvsr_rule_id_is_stable():
    assert (
        pni_2026.VVSR_RULE_ID
        == "PNI26-VVSR-PREG-ROUTINE-001"
    )


def test_nonpregnant_is_not_applicable():
    result = evaluate(
        pregnancy_status="not_pregnant",
        gestational_age_weeks=None,
        pregnancy_episode_key=None,
        history=None,
    )

    assert (
        result[
            "decision"
        ]
        == "not_applicable"
    )


def test_unknown_pregnancy_status_requires_context():
    result = evaluate(
        pregnancy_status="unknown",
        gestational_age_weeks=None,
        pregnancy_episode_key=None,
        history=None,
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
        "pregnancy_status",
    ]


def test_missing_gestational_age_requires_context():
    result = evaluate(
        gestational_age_weeks=None,
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
        "gestational_age_weeks",
    ]


def test_before_week_28_is_not_due_now():
    result = evaluate(
        gestational_age_weeks=27,
        history=None,
    )

    assert (
        result[
            "decision"
        ]
        == "not_due_now"
    )


def test_exact_week_28_documented_zero_dose_recommends_now():
    result = evaluate(
        gestational_age_weeks=28,
    )

    assert (
        result[
            "decision"
        ]
        == "recommend_now"
    )


def test_no_maternal_age_input_or_restriction_is_applied():
    result = evaluate(
        gestational_age_weeks=40,
    )

    assert (
        result[
            "decision"
        ]
        == "recommend_now"
    )


def test_current_pregnancy_dose_means_not_due_now():
    result = evaluate(
        history=history(
            "documented_doses",
            doses=[
                dose(),
            ],
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "not_due_now"
    )


def test_current_pregnancy_dose_before_28_is_not_repeated():
    result = evaluate(
        gestational_age_weeks=25,
        history=history(
            "documented_doses",
            doses=[
                dose(
                    administration_date=date(
                        2026,
                        8,
                        1,
                    ),
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


def test_previous_pregnancy_dose_does_not_satisfy_current_pregnancy():
    result = evaluate(
        history=history(
            "documented_doses",
            doses=[
                dose(
                    episode="pregnancy-previous",
                ),
            ],
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "recommend_now"
    )


def test_unknown_history_requires_history_at_or_after_week_28():
    result = evaluate(
        history=history(
            "unknown"
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "history_required"
    )

    assert (
        result[
            "history_required"
        ]
        is True
    )


def test_partial_history_without_current_proof_requires_reconciliation():
    result = evaluate(
        history=history(
            "partial_record",
            undated=1,
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "history_required"
    )


def test_partial_history_with_exact_current_dose_is_sufficient():
    result = evaluate(
        history=history(
            "partial_record",
            doses=[
                dose(),
            ],
            undated=1,
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "not_due_now"
    )


def test_missing_history_requires_history_at_or_after_week_28():
    result = evaluate(
        history=None,
    )

    assert (
        result[
            "decision"
        ]
        == "history_required"
    )


def test_documented_doses_require_current_episode_identity():
    result = evaluate(
        pregnancy_episode_key=None,
        history=history(
            "documented_doses",
            doses=[
                dose(
                    episode="pregnancy-previous",
                ),
            ],
        ),
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
        "pregnancy_episode_key",
    ]


def test_unassigned_dose_episode_fails_closed_to_history_required():
    result = evaluate(
        history=history(
            "documented_doses",
            doses=[
                dose(
                    episode=None,
                ),
            ],
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "history_required"
    )


def test_future_dated_vvsr_dose_is_rejected():
    with pytest.raises(
        ValueError,
        match="cannot follow assessment_date",
    ):
        evaluate(
            history=history(
                "documented_doses",
                doses=[
                    dose(
                        administration_date=date(
                            2026,
                            9,
                            12,
                        ),
                    ),
                ],
            ),
        )


def test_wrong_vaccine_history_key_is_rejected():
    wrong = schemas.PniVaccineHistory(
        vaccine_key="dtpa",
        history_state="documented_zero_dose",
    )

    with pytest.raises(
        ValueError,
        match="vaccine_key=vvsr",
    ):
        evaluate(
            history=wrong,
        )


def test_invalid_gestational_week_is_rejected():
    with pytest.raises(
        ValueError,
        match="0 to 45",
    ):
        evaluate(
            gestational_age_weeks=46,
        )


def test_result_retains_national_provenance():
    result = evaluate()

    provenance = result[
        "provenance"
    ]

    assert (
        provenance[
            "rule_id"
        ]
        == "PNI26-VVSR-PREG-ROUTINE-001"
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


def test_no_minimum_interval_is_invented():
    result = evaluate()

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


def test_no_special_condition_inference_or_synthetic_score():
    result = evaluate()

    assert (
        result[
            "special_condition_inferred"
        ]
        is False
    )

    assert (
        result[
            "synthetic_score_applied"
        ]
        is False
    )



def test_vvsr_core_remains_available_after_dtpa_maternal_addition():
    assert hasattr(
        pni_2026,
        "evaluate_pni_vvsr_routine",
    )

    assert hasattr(
        pni_2026,
        "evaluate_pni_dtpa_maternal_routine",
    )

    assert (
        pni_2026.VVSR_RULE_ID
        == "PNI26-VVSR-PREG-ROUTINE-001"
    )
