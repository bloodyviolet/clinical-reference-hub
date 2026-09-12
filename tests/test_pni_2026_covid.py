from datetime import date, timedelta

import pytest

import schemas

from clinical_tools.pni_2026 import (
    COVID_CHILD_RULE_ID,
    evaluate_pni_covid_child_routine,
)

from clinical_tools.pni_history import (
    COVID_CHILD_PRODUCT_CORONAVAC,
    COVID_CHILD_PRODUCT_MODERNA,
    COVID_CHILD_PRODUCT_PFIZER,
    normalize_covid_child_history,
)


P = COVID_CHILD_PRODUCT_PFIZER
M = COVID_CHILD_PRODUCT_MODERNA
C = COVID_CHILD_PRODUCT_CORONAVAC


DOB = date(
    2022,
    1,
    1,
)

ASSESSMENT = date(
    2026,
    6,
    1,
)


def normalized(
    events=None,
    *,
    assessment=ASSESSMENT,
    dob=DOB,
    state=None,
    scope="complete",
    undated=0,
):
    events = list(
        events
        or []
    )

    if state is None:
        state = (
            "documented_doses"
            if events
            else "documented_zero_dose"
        )

    history = schemas.PniVaccineHistory(
        vaccine_key="covid_19",
        history_state=state,
        doses=[
            schemas.PniDoseRecord(
                administration_date=event_date,
                product_key=product,
                documentation_source="official_registry",
            )
            for event_date, product
            in events
        ],
        reported_prior_doses_without_exact_dates=undated,
    )

    return normalize_covid_child_history(
        assessment_date=assessment,
        date_of_birth=dob,
        history=history,
        history_scope=scope,
    )


def evaluate(
    history,
    *,
    assessment=ASSESSMENT,
    dob=DOB,
    context="screened_none",
    safety="screened_no_concern",
):
    result = evaluate_pni_covid_child_routine(
        assessment_date=assessment,
        date_of_birth=dob,
        covid_history=history,
        healthy_child_context_state=context,
        administration_safety_screen_state=safety,
    )

    schemas.PniCovidChildRuleResult.model_validate(
        result
    )

    return result


def test_specialized_result_extends_base_without_changing_base_contract():
    assert issubclass(
        schemas.PniCovidChildRuleResult,
        schemas.PniRuleResult,
    )

    assert (
        "allowed_next_product_keys"
        not in schemas.PniRuleResult.model_fields
    )

    assert (
        "allowed_next_product_keys"
        in schemas.PniCovidChildRuleResult.model_fields
    )

    assert (
        "next_product_options"
        in schemas.PniCovidChildRuleResult.model_fields
    )


def test_rule_id_constant():
    assert (
        COVID_CHILD_RULE_ID
        == "PNI26-COVID-CHILD-ROUTINE-001"
    )


def test_before_exact_6_months_not_due():
    dob = date(
        2026,
        1,
        1,
    )

    assessment = date(
        2026,
        6,
        30,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
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
        7,
        1,
    )

    assert result[
        "allowed_next_product_keys"
    ] == []


def test_exact_6_months_zero_history_recommend_now():
    dob = date(
        2026,
        1,
        1,
    )

    assessment = date(
        2026,
        7,
        1,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "recommend_now"

    assert result[
        "allowed_next_product_keys"
    ] == [
        P,
        M,
    ]

    assert result[
        "preferred_next_product_key"
    ] == P

    assert (
        result[
            "preferred_product_basis"
        ]
        == "current_2026_first_option"
    )

    assert (
        result[
            "product_choice_condition"
        ]
        == "pfizer_unavailable"
    )

    assert result[
        "next_product_options"
    ][
        0
    ][
        "resulting_product_sequence"
    ] == [
        P,
    ]

    assert result[
        "next_product_options"
    ][
        0
    ][
        "next_minimum_interval_days"
    ] == 28

    assert result[
        "next_product_options"
    ][
        1
    ][
        "condition"
    ] == "pfizer_unavailable"


def test_zero_history_never_offers_coronavac():
    result = evaluate(
        normalized()
    )

    assert C not in result[
        "allowed_next_product_keys"
    ]

    assert all(
        option[
            "product_key"
        ]
        != C
        for option
        in result[
            "next_product_options"
        ]
    )


def test_healthy_context_not_screened_fails_closed():
    result = evaluate(
        normalized(),
        context="not_screened",
    )

    assert result[
        "decision"
    ] == "context_required"

    assert (
        "healthy_child_context_state"
        in result[
            "missing_context"
        ]
    )

    assert result[
        "allowed_next_product_keys"
    ] == []


def test_special_condition_routes_out():
    result = evaluate(
        normalized(),
        context="screened_special_condition_present",
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )

    assert result[
        "allowed_next_product_keys"
    ] == []


def test_due_but_safety_not_screened_requires_context():
    result = evaluate(
        normalized(),
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

    assert result[
        "allowed_next_product_keys"
    ] == []


def test_due_with_safety_concern_routes_to_review():
    result = evaluate(
        normalized(),
        safety="screened_concern",
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )

    assert result[
        "allowed_next_product_keys"
    ] == []


def test_pfizer_day27_not_due_day28_due():
    d1 = date(
        2026,
        4,
        1,
    )

    day27 = (
        d1
        + timedelta(
            days=27,
        )
    )

    day28 = (
        d1
        + timedelta(
            days=28,
        )
    )

    result27 = evaluate(
        normalized(
            [
                (
                    d1,
                    P,
                ),
            ],
            assessment=day27,
        ),
        assessment=day27,
    )

    result28 = evaluate(
        normalized(
            [
                (
                    d1,
                    P,
                ),
            ],
            assessment=day28,
        ),
        assessment=day28,
    )

    assert result27[
        "decision"
    ] == "not_due_now"

    assert result27[
        "recommended_date"
    ] == day28

    assert result27[
        "recommended_interval_days"
    ] == 28

    assert result27[
        "allowed_next_product_keys"
    ] == [
        P,
        M,
    ]

    assert result28[
        "decision"
    ] == "recommend_now"

    assert result28[
        "preferred_next_product_key"
    ] == P


def test_one_moderna_product_consequence_is_preserved():
    d1 = date(
        2026,
        4,
        1,
    )

    assessment = (
        d1
        + timedelta(
            days=28,
        )
    )

    result = evaluate(
        normalized(
            [
                (
                    d1,
                    M,
                ),
            ],
            assessment=assessment,
        ),
        assessment=assessment,
    )

    assert result[
        "decision"
    ] == "recommend_now"

    assert result[
        "allowed_next_product_keys"
    ] == [
        M,
        P,
    ]

    assert result[
        "preferred_next_product_key"
    ] == M

    by_product = {
        option[
            "product_key"
        ]:
            option
        for option
        in result[
            "next_product_options"
        ]
    }

    assert (
        by_product[
            M
        ][
            "resulting_sequence_state"
        ]
        == "source_authorized_complete"
    )

    assert (
        by_product[
            M
        ][
            "next_minimum_interval_days"
        ]
        is None
    )

    assert (
        by_product[
            P
        ][
            "resulting_product_sequence"
        ]
        == [
            M,
            P,
        ]
    )

    assert (
        by_product[
            P
        ][
            "resulting_sequence_state"
        ]
        == "source_authorized_incomplete_prefix"
    )

    assert (
        by_product[
            P
        ][
            "next_minimum_interval_days"
        ]
        == 56
    )


def test_moderna_moderna_complete_at_two_exposures():
    d1 = date(
        2026,
        2,
        1,
    )

    d2 = (
        d1
        + timedelta(
            days=28,
        )
    )

    result = evaluate(
        normalized(
            [
                (
                    d1,
                    M,
                ),
                (
                    d2,
                    M,
                ),
            ]
        )
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "allowed_next_product_keys"
    ] == []

    assert result[
        "next_product_options"
    ] == []


@pytest.mark.parametrize(
    "prefix",
    [
        (
            P,
            P,
        ),
        (
            P,
            M,
        ),
        (
            M,
            P,
        ),
        (
            C,
            P,
        ),
        (
            C,
            M,
        ),
        (
            C,
            C,
        ),
    ],
)
def test_two_exposure_prefix_day55_not_due_day56_due(
    prefix,
):
    d1 = date(
        2026,
        1,
        1,
    )

    d2 = (
        d1
        + timedelta(
            days=28,
        )
    )

    day55 = (
        d2
        + timedelta(
            days=55,
        )
    )

    day56 = (
        d2
        + timedelta(
            days=56,
        )
    )

    result55 = evaluate(
        normalized(
            [
                (
                    d1,
                    prefix[
                        0
                    ],
                ),
                (
                    d2,
                    prefix[
                        1
                    ],
                ),
            ],
            assessment=day55,
        ),
        assessment=day55,
    )

    result56 = evaluate(
        normalized(
            [
                (
                    d1,
                    prefix[
                        0
                    ],
                ),
                (
                    d2,
                    prefix[
                        1
                    ],
                ),
            ],
            assessment=day56,
        ),
        assessment=day56,
    )

    assert result55[
        "decision"
    ] == "not_due_now"

    assert result55[
        "recommended_date"
    ] == day56

    assert result56[
        "decision"
    ] == "recommend_now"

    assert C not in result56[
        "allowed_next_product_keys"
    ]


def test_pure_pfizer_two_dose_prefix_prefers_pfizer():
    d1 = date(
        2026,
        1,
        1,
    )

    d2 = (
        d1
        + timedelta(
            days=28,
        )
    )

    assessment = (
        d2
        + timedelta(
            days=56,
        )
    )

    result = evaluate(
        normalized(
            [
                (
                    d1,
                    P,
                ),
                (
                    d2,
                    P,
                ),
            ],
            assessment=assessment,
        ),
        assessment=assessment,
    )

    assert result[
        "preferred_next_product_key"
    ] == P

    assert (
        result[
            "preferred_product_basis"
        ]
        == "homologous_priority"
    )


def test_mixed_pfizer_moderna_has_no_invented_preference():
    d1 = date(
        2026,
        1,
        1,
    )

    d2 = (
        d1
        + timedelta(
            days=28,
        )
    )

    assessment = (
        d2
        + timedelta(
            days=56,
        )
    )

    result = evaluate(
        normalized(
            [
                (
                    d1,
                    P,
                ),
                (
                    d2,
                    M,
                ),
            ],
            assessment=assessment,
        ),
        assessment=assessment,
    )

    assert result[
        "preferred_next_product_key"
    ] is None

    assert (
        result[
            "preferred_product_basis"
        ]
        == "mixed_history_no_new_preference_inferred"
    )

    assert {
        option[
            "option_role"
        ]
        for option
        in result[
            "next_product_options"
        ]
    } == {
        "source_allowed_no_preference",
    }


def test_single_legacy_coronavac_allows_mrna_only():
    d1 = date(
        2026,
        3,
        1,
    )

    assessment = (
        d1
        + timedelta(
            days=28,
        )
    )

    result = evaluate(
        normalized(
            [
                (
                    d1,
                    C,
                ),
            ],
            assessment=assessment,
        ),
        assessment=assessment,
    )

    assert result[
        "decision"
    ] == "recommend_now"

    assert set(
        result[
            "allowed_next_product_keys"
        ]
    ) == {
        P,
        M,
    }

    assert C not in result[
        "allowed_next_product_keys"
    ]

    assert result[
        "preferred_next_product_key"
    ] is None


def test_complete_three_exposure_mixed_sequence_no_periodic_dose():
    d1 = date(
        2025,
        12,
        1,
    )

    d2 = (
        d1
        + timedelta(
            days=28,
        )
    )

    d3 = (
        d2
        + timedelta(
            days=56,
        )
    )

    result = evaluate(
        normalized(
            [
                (
                    d1,
                    P,
                ),
                (
                    d2,
                    M,
                ),
                (
                    d3,
                    P,
                ),
            ]
        )
    )

    assert result[
        "decision"
    ] == "not_due_now"

    assert result[
        "allowed_next_product_keys"
    ] == []

    assert result[
        "preferred_next_product_key"
    ] is None


def test_exact_age5_with_prior_supported_exposure_applies_closure():
    dob = date(
        2021,
        9,
        11,
    )

    d1 = date(
        2026,
        8,
        1,
    )

    assessment = date(
        2026,
        9,
        11,
    )

    result = evaluate(
        normalized(
            [
                (
                    d1,
                    P,
                ),
            ],
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "not_applicable"

    assert result[
        "age_out_closure_applied"
    ] is True

    assert result[
        "allowed_next_product_keys"
    ] == []


def test_exact_age5_zero_history_is_outside_under5_core():
    dob = date(
        2021,
        9,
        11,
    )

    assessment = date(
        2026,
        9,
        11,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "not_applicable"

    assert result[
        "age_out_closure_applied"
    ] is False


def test_age5_unknown_history_requires_history():
    dob = date(
        2021,
        9,
        11,
    )

    assessment = date(
        2026,
        9,
        11,
    )

    result = evaluate(
        normalized(
            assessment=assessment,
            dob=dob,
            state="unknown",
        ),
        assessment=assessment,
        dob=dob,
    )

    assert result[
        "decision"
    ] == "history_required"

    assert result[
        "history_required"
    ] is True


def test_age_out_beats_future_28_day_threshold():
    dob = date(
        2021,
        9,
        11,
    )

    d1 = date(
        2026,
        8,
        25,
    )

    assessment = date(
        2026,
        9,
        10,
    )

    result = evaluate(
        normalized(
            [
                (
                    d1,
                    P,
                ),
            ],
            assessment=assessment,
            dob=dob,
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
        9,
        11,
    )

    assert result[
        "allowed_next_product_keys"
    ] == []

    assert result[
        "next_product_options"
    ] == []


def test_partial_history_requires_history():
    history = schemas.PniVaccineHistory(
        vaccine_key="covid_19",
        history_state="partial_record",
        reported_prior_doses_without_exact_dates=1,
    )

    normalized_history = normalize_covid_child_history(
        assessment_date=ASSESSMENT,
        date_of_birth=DOB,
        history=history,
        history_scope="complete",
    )

    result = evaluate(
        normalized_history
    )

    assert result[
        "decision"
    ] == "history_required"


def test_pre6m_history_routes_to_review():
    dob = date(
        2022,
        1,
        1,
    )

    early = date(
        2022,
        6,
        30,
    )

    assessment = date(
        2026,
        6,
        1,
    )

    result = evaluate(
        normalized(
            [
                (
                    early,
                    P,
                ),
            ],
            assessment=assessment,
            dob=dob,
        ),
        assessment=assessment,
        dob=dob,
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_unsupported_product_history_routes_to_review():
    history = schemas.PniVaccineHistory(
        vaccine_key="covid_19",
        history_state="documented_doses",
        doses=[
            schemas.PniDoseRecord(
                administration_date=date(
                    2026,
                    3,
                    1,
                ),
                product_key="covid_19",
                documentation_source="official_registry",
            ),
        ],
    )

    normalized_history = normalize_covid_child_history(
        assessment_date=ASSESSMENT,
        date_of_birth=DOB,
        history=history,
        history_scope="complete",
    )

    result = evaluate(
        normalized_history
    )

    assert (
        result[
            "decision"
        ]
        == "special_pathway_review"
    )


def test_tampered_registration_ordinal_invariant_rejected():
    history = normalized()

    tampered = dict(
        history
    )

    tampered[
        "registration_role_defines_clinical_ordinal"
    ] = True

    with pytest.raises(
        ValueError,
        match="registration role",
    ):
        evaluate_pni_covid_child_routine(
            assessment_date=ASSESSMENT,
            date_of_birth=DOB,
            covid_history=tampered,
            healthy_child_context_state="screened_none",
            administration_safety_screen_state="screened_no_concern",
        )


def test_tampered_date_of_birth_boundary_rejected():
    history = normalized()

    with pytest.raises(
        ValueError,
        match="6-month boundary",
    ):
        evaluate_pni_covid_child_routine(
            assessment_date=ASSESSMENT,
            date_of_birth=date(
                2022,
                1,
                2,
            ),
            covid_history=history,
            healthy_child_context_state="screened_none",
            administration_safety_screen_state="screened_no_concern",
        )


def test_coronavac_rejected_as_current_typed_option():
    with pytest.raises(
        Exception
    ):
        schemas.PniCovidNextProductOption(
            product_key=C,
            option_role="allowed_alternative",
            condition=None,
            resulting_product_sequence=[
                C,
                C,
            ],
            resulting_sequence_state=(
                "source_authorized_complete"
            ),
            next_minimum_interval_days=None,
        )


def test_result_model_rejects_preferred_key_not_in_allowed_set():
    baseline = evaluate(
        normalized()
    )

    baseline[
        "preferred_next_product_key"
    ] = M

    with pytest.raises(
        Exception
    ):
        schemas.PniCovidChildRuleResult.model_validate(
            baseline
        )


def test_bilingual_and_language_neutral_decision():
    result = evaluate(
        normalized()
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
        "decision"
    ] == "recommend_now"


def test_no_special_condition_or_synthetic_score_inference():
    result = evaluate(
        normalized()
    )

    assert result[
        "special_condition_inferred"
    ] is False

    assert result[
        "synthetic_score_applied"
    ] is False
