from datetime import date

import schemas

from clinical_tools.pni_2026 import (
    DTP_CHILD_RULE_ID,
    evaluate_pni_dtp_child_routine,
)

from clinical_tools.pni_history import (
    normalize_dtp_child_history,
)


def history(
    key,
    dates=None,
    *,
    state=None,
    undated=0,
):
    dates = list(
        dates
        or []
    )

    if state is None:
        state = (
            "documented_doses"
            if dates
            else "documented_zero_dose"
        )

    return schemas.PniVaccineHistory(
        vaccine_key=key,
        history_state=state,
        doses=[
            schemas.PniDoseRecord(
                administration_date=value,
                product_key=key,
                documentation_source="official_registry",
            )
            for value in dates
        ],
        reported_prior_doses_without_exact_dates=undated,
    )


def normalize(
    *,
    dob,
    assessment,
    penta=None,
    dtp=None,
    scope="complete",
):
    if penta is None:
        penta = history(
            "pentavalent"
        )

    if dtp is None:
        dtp = history(
            "dtp"
        )

    return normalize_dtp_child_history(
        assessment_date=assessment,
        date_of_birth=dob,
        pentavalent_history=penta,
        dtp_history=dtp,
        history_scope=scope,
    )


def standard_penta(
    year=2024,
):
    return history(
        "pentavalent",
        [
            date(
                year,
                3,
                1,
            ),
            date(
                year,
                5,
                1,
            ),
            date(
                year,
                7,
                1,
            ),
        ],
    )


def evaluate(
    normalized,
    *,
    assessment,
    dob,
    special="screened_none",
    safety="screened_no_concern",
):
    result = evaluate_pni_dtp_child_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        dtp_history=normalized,
        special_condition_screen_state=special,
        administration_safety_screen_state=safety,
    )

    schemas.PniRuleResult.model_validate(
        result
    )

    return result


def test_rule_id():
    assert (
        DTP_CHILD_RULE_ID
        == "PNI26-DTP-CHILD-ROUTINE-001"
    )


def test_before_exact_15_months_not_due():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        3,
        31,
    )

    result = evaluate(
        normalize(
            dob=dob,
            assessment=assessment,
            penta=standard_penta(),
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == date(
        2025,
        4,
        1,
    )


def test_exact_15_months_valid_primary_recommend_r1():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        4,
        1,
    )

    result = evaluate(
        normalize(
            dob=dob,
            assessment=assessment,
            penta=standard_penta(),
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "recommend_now"

    assert result[
        "recommended_date"
    ] == assessment


def test_late_penta_d3_can_delay_r1_beyond_15_months():
    dob = date(
        2024,
        1,
        1,
    )

    penta = history(
        "pentavalent",
        [
            date(
                2024,
                7,
                1,
            ),
            date(
                2024,
                9,
                1,
            ),
            date(
                2024,
                11,
                1,
            ),
        ],
    )

    at15 = date(
        2025,
        4,
        1,
    )

    result = evaluate(
        normalize(
            dob=dob,
            assessment=at15,
            penta=penta,
        ),
        assessment=at15,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == date(
        2025,
        5,
        1,
    )


def test_exact_d3_plus_six_calendar_months_recommend_r1():
    dob = date(
        2024,
        1,
        1,
    )

    penta = history(
        "pentavalent",
        [
            date(
                2024,
                7,
                1,
            ),
            date(
                2024,
                9,
                1,
            ),
            date(
                2024,
                11,
                1,
            ),
        ],
    )

    assessment = date(
        2025,
        5,
        1,
    )

    result = evaluate(
        normalize(
            dob=dob,
            assessment=assessment,
            penta=penta,
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_incomplete_pentavalent_primary_series_does_not_invent_dtp():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        4,
        1,
    )

    result = evaluate(
        normalize(
            dob=dob,
            assessment=assessment,
            penta=history(
                "pentavalent",
                [
                    date(
                        2024,
                        3,
                        1,
                    ),
                    date(
                        2024,
                        5,
                        1,
                    ),
                ],
            ),
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] is None


def test_valid_r1_before_exact4y_waits_for_age4():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2027,
        12,
        31,
    )

    result = evaluate(
        normalize(
            dob=dob,
            assessment=assessment,
            penta=standard_penta(),
            dtp=history(
                "dtp",
                [
                    date(
                        2025,
                        4,
                        1,
                    ),
                ],
            ),
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == date(
        2028,
        1,
        1,
    )


def test_exact4y_with_valid_r1_recommend_r2():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2028,
        1,
        1,
    )

    result = evaluate(
        normalize(
            dob=dob,
            assessment=assessment,
            penta=standard_penta(),
            dtp=history(
                "dtp",
                [
                    date(
                        2025,
                        4,
                        1,
                    ),
                ],
            ),
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_late_r1_six_month_interval_can_delay_r2_beyond_age4():
    dob = date(
        2020,
        1,
        1,
    )

    assessment = date(
        2026,
        11,
        30,
    )

    result = evaluate(
        normalize(
            dob=dob,
            assessment=assessment,
            penta=standard_penta(
                2020
            ),
            dtp=history(
                "dtp",
                [
                    date(
                        2026,
                        6,
                        1,
                    ),
                ],
            ),
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] == date(
        2026,
        12,
        1,
    )


def test_exact_r1_plus_six_calendar_months_recommend_r2():
    dob = date(
        2020,
        1,
        1,
    )

    assessment = date(
        2026,
        12,
        1,
    )

    result = evaluate(
        normalize(
            dob=dob,
            assessment=assessment,
            penta=standard_penta(
                2020
            ),
            dtp=history(
                "dtp",
                [
                    date(
                        2026,
                        6,
                        1,
                    ),
                ],
            ),
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "recommend_now"


def test_late_r1_that_pushes_r2_past_age7_closes_DTP_opportunity():
    dob = date(
        2020,
        1,
        1,
    )

    assessment = date(
        2026,
        8,
        1,
    )

    result = evaluate(
        normalize(
            dob=dob,
            assessment=assessment,
            penta=standard_penta(
                2020
            ),
            dtp=history(
                "dtp",
                [
                    date(
                        2026,
                        8,
                        1,
                    ),
                ],
            ),
        ),
        assessment=assessment,
        dob=dob,
        special="not_screened",
        safety="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "recommended_date"
    ] is None

    assert result[
        "missing_context"
    ] == []


def test_exact7y_closes_ordinary_dtp_without_requesting_context():
    dob = date(
        2020,
        1,
        1,
    )

    assessment = date(
        2027,
        1,
        1,
    )

    normalized = normalize(
        dob=dob,
        assessment=assessment,
        penta=standard_penta(
            2020
        ),
    )

    result = evaluate(
        normalized,
        assessment=assessment,
        dob=dob,
        special="not_screened",
        safety="not_screened",
    )

    assert result[
        "decision"
    ] == "not_applicable"

    assert result[
        "missing_context"
    ] == []


def test_two_valid_DTP_boosters_complete_without_extra_context():
    dob = date(
        2020,
        1,
        1,
    )

    assessment = date(
        2026,
        1,
        1,
    )

    result = evaluate(
        normalize(
            dob=dob,
            assessment=assessment,
            penta=standard_penta(
                2020
            ),
            dtp=history(
                "dtp",
                [
                    date(
                        2021,
                        4,
                        1,
                    ),
                    date(
                        2024,
                        1,
                        1,
                    ),
                ],
            ),
        ),
        assessment=assessment,
        dob=dob,
        special="not_screened",
        safety="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "missing_context"
    ] == []


def test_partial_history_requires_history():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        4,
        1,
    )

    normalized = normalize(
        dob=dob,
        assessment=assessment,
        penta=history(
            "pentavalent",
            state="partial_record",
            undated=1,
        ),
    )

    result = evaluate(
        normalized,
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "history_required"

    assert result[
        "history_required"
    ] is True


def test_invalid_normalized_history_routes_to_review():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        3,
        31,
    )

    normalized = normalize(
        dob=dob,
        assessment=assessment,
        penta=standard_penta(),
        dtp=history(
            "dtp",
            [
                date(
                    2025,
                    3,
                    31,
                ),
            ],
        ),
    )

    result = evaluate(
        normalized,
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "special_pathway_review"


def test_due_path_special_condition_not_screened_requires_context():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        4,
        1,
    )

    result = evaluate(
        normalize(
            dob=dob,
            assessment=assessment,
            penta=standard_penta(),
        ),
        assessment=assessment,
        dob=dob,
        special="not_screened",
        safety="screened_no_concern",
    )

    assert result[
        "decision"
    ] == "context_required"

    assert (
        "dtp_special_condition_screen_state"
        in result[
            "missing_context"
        ]
    )


def test_due_path_special_condition_present_routes_to_review():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        4,
        1,
    )

    result = evaluate(
        normalize(
            dob=dob,
            assessment=assessment,
            penta=standard_penta(),
        ),
        assessment=assessment,
        dob=dob,
        special="screened_special_condition_present",
        safety="screened_no_concern",
    )

    assert result[
        "decision"
    ] == "special_pathway_review"


def test_due_path_safety_not_screened_requires_context():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        4,
        1,
    )

    result = evaluate(
        normalize(
            dob=dob,
            assessment=assessment,
            penta=standard_penta(),
        ),
        assessment=assessment,
        dob=dob,
        special="screened_none",
        safety="not_screened",
    )

    assert result[
        "decision"
    ] == "context_required"

    assert (
        "administration_safety_screen_state"
        in result[
            "missing_context"
        ]
    )


def test_due_path_safety_concern_routes_to_review():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        4,
        1,
    )

    result = evaluate(
        normalize(
            dob=dob,
            assessment=assessment,
            penta=standard_penta(),
        ),
        assessment=assessment,
        dob=dob,
        special="screened_none",
        safety="screened_concern",
    )

    assert result[
        "decision"
    ] == "special_pathway_review"


def test_non_due_path_does_not_request_special_or_safety_context():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        3,
        31,
    )

    result = evaluate(
        normalize(
            dob=dob,
            assessment=assessment,
            penta=standard_penta(),
        ),
        assessment=assessment,
        dob=dob,
        special="not_screened",
        safety="not_screened",
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "missing_context"
    ] == []


def test_calendar_month_rules_are_not_misrepresented_as_fixed_days():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        4,
        1,
    )

    result = evaluate(
        normalize(
            dob=dob,
            assessment=assessment,
            penta=standard_penta(),
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "recommended_interval_days"
    ] is None

    assert result[
        "minimum_interval_days"
    ] is None

    assert result[
        "minimum_interval_applied"
    ] is False


def test_representative_result_is_bilingual_and_language_neutral():
    dob = date(
        2024,
        1,
        1,
    )

    assessment = date(
        2025,
        4,
        1,
    )

    result = evaluate(
        normalize(
            dob=dob,
            assessment=assessment,
            penta=standard_penta(),
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "interpretation_pt"
    ].strip()

    assert result[
        "interpretation_en"
    ].strip()

    assert (
        result[
            "interpretation_pt"
        ]
        != result[
            "interpretation_en"
        ]
    )

    assert result[
        "special_condition_inferred"
    ] is False

    assert result[
        "synthetic_score_applied"
    ] is False
