from datetime import date

import pytest
from pydantic import ValidationError

import schemas

from clinical_tools.pni_2026 import (
    evaluate_pni_hpv4_routine,
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
        vaccine_key="hpv4",
        history_state=state,
        doses=doses or [],
    )


def dose(
    administration_date,
):
    return schemas.PniDoseRecord(
        administration_date=administration_date,
        product_key="hpv4",
        documentation_source="official_registry",
    )


def evaluate(
    *,
    date_of_birth=date(
        2017,
        9,
        11,
    ),
    pregnancy_status="not_applicable",
    history_value=None,
    safety="screened_no_concern",
):
    result = evaluate_pni_hpv4_routine(
        assessment_date=ASSESSMENT_DATE,
        date_of_birth=date_of_birth,
        pregnancy_status=pregnancy_status,
        history=history_value,
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
        pni_2026.HPV4_ROUTINE_RULE_ID
        == "PNI26-HPV4-ROUTINE-9-14-001"
    )


def test_day_before_ninth_birthday_is_not_due():
    result = evaluate(
        date_of_birth=date(
            2017,
            9,
            12,
        ),
    )

    assert (
        result[
            "decision"
        ]
        == "not_due_now"
    )


def test_exact_ninth_birthday_documented_zero_recommends_now():
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


def test_day_before_fifteenth_birthday_remains_routine():
    result = evaluate(
        date_of_birth=date(
            2011,
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


def test_exact_fifteenth_birthday_is_not_routine_layer():
    result = evaluate(
        date_of_birth=date(
            2011,
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

    assert (
        "resgate"
        in result[
            "interpretation_pt"
        ].lower()
    )

    assert (
        "rescue"
        in result[
            "interpretation_en"
        ].lower()
    )


def test_documented_routine_age_dose_satisfies_one_dose_schedule():
    dob = date(
        2015,
        1,
        1,
    )

    result = evaluate(
        date_of_birth=dob,
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    date(
                        2024,
                        1,
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


def test_pre_age_nine_hpv_dose_routes_special_review():
    dob = date(
        2015,
        1,
        1,
    )

    result = evaluate(
        date_of_birth=dob,
        history_value=history(
            "documented_doses",
            doses=[
                dose(
                    date(
                        2023,
                        1,
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
        == "special_pathway_review"
    )


def test_missing_history_in_routine_window_requires_history():
    result = evaluate(
        history_value=None,
    )

    assert (
        result[
            "decision"
        ]
        == "history_required"
    )


def test_unknown_history_is_not_documented_zero():
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


def test_partial_history_requires_reconciliation():
    # Normalized PniVaccineHistory deliberately rejects an
    # evidence-free partial record. Preserve that model invariant.
    with pytest.raises(
        ValidationError,
        match=(
            "partial_record requires some known or reported "
            "dose evidence"
        ),
    ):
        history(
            "partial_record",
            doses=[],
        )

    # The Python rule core is also defensive if an unvalidated
    # mapping reaches it directly: partial history still fails
    # closed instead of becoming documented zero-dose history.
    result = evaluate(
        history_value={
            "vaccine_key":
                "hpv4",

            "history_state":
                "partial_record",

            "doses":
                [],
        },
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



def test_unknown_pregnancy_status_requires_context_when_due():
    result = evaluate(
        pregnancy_status="unknown",
        history_value=history(
            "documented_zero_dose"
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
        "pregnancy_status",
    ]


def test_pregnancy_routes_special_review():
    result = evaluate(
        pregnancy_status="pregnant",
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


def test_not_pregnant_due_person_can_recommend():
    result = evaluate(
        pregnancy_status="not_pregnant",
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


def test_pregnancy_not_applicable_due_person_can_recommend():
    result = evaluate(
        pregnancy_status="not_applicable",
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


def test_unscreened_due_dose_does_not_auto_recommend():
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


def test_no_spacing_interval_is_invented():
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


def test_future_dose_is_rejected():
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
        vaccine_key="hepatitis_a",
        history_state="documented_zero_dose",
    )

    with pytest.raises(
        ValueError,
        match="vaccine_key=hpv4",
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
        == "PNI26-HPV4-ROUTINE-9-14-001"
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
            "date_of_birth":
                date(
                    2017,
                    9,
                    12,
                ),
        },
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
                    "documented_zero_dose"
                ),
            "pregnancy_status":
                "pregnant",
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
            "date_of_birth":
                date(
                    2011,
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
