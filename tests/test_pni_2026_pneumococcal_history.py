from datetime import date

import pytest

import schemas

from clinical_tools.pni_history import (
    normalize_pneumococcal_history,
)


ASSESSMENT = date(
    2026,
    9,
    11,
)


def history(
    key,
    state,
    *,
    dates=None,
    reported_prior=0,
):
    return schemas.PniVaccineHistory(
        vaccine_key=key,
        history_state=state,
        doses=[
            schemas.PniDoseRecord(
                administration_date=value,
                product_key=key,
                documentation_source="official_registry",
            )
            for value in (
                dates
                or []
            )
        ],
        reported_prior_doses_without_exact_dates=reported_prior,
    )


def normalize(
    histories,
    *,
    scope="complete",
):
    return normalize_pneumococcal_history(
        assessment_date=ASSESSMENT,
        histories=histories,
        history_scope=scope,
    )


def test_documented_zero_both_products_is_safe_zero():
    result = normalize(
        [
            history(
                "pneumococcal_10",
                "documented_zero_dose",
            ),
            history(
                "pneumococcal_20",
                "documented_zero_dose",
            ),
        ]
    )

    assert (
        result["history_state"]
        == "documented_zero_exposure"
    )

    assert result["exposure_event_count"] == 0
    assert result["safe_for_role_assignment"] is True

    assert result["vpc10_history_supplied"] is True
    assert result["vpc20_history_supplied"] is True


def test_vpc10_identity_preserved():
    result = normalize(
        [
            history(
                "pneumococcal_10",
                "documented_doses",
                dates=[
                    date(2026, 4, 1),
                ],
            ),
        ]
    )

    assert result["vpc10_exposure_count"] == 1
    assert result["vpc20_exposure_count"] == 0

    exposure = result["exposures"][0]

    assert (
        exposure["source_vaccine_key"]
        == "pneumococcal_10"
    )

    assert exposure["official_acronym"] == "VPC10"
    assert exposure["valency"] == 10


def test_vpc20_identity_preserved():
    result = normalize(
        [
            history(
                "pneumococcal_20",
                "documented_doses",
                dates=[
                    date(2026, 2, 1),
                ],
            ),
        ]
    )

    assert result["vpc10_exposure_count"] == 0
    assert result["vpc20_exposure_count"] == 1

    exposure = result["exposures"][0]

    assert (
        exposure["source_vaccine_key"]
        == "pneumococcal_20"
    )

    assert exposure["official_acronym"] == "VPC20"
    assert exposure["valency"] == 20


def test_mixed_product_chronology_is_expected_and_preserved():
    result = normalize(
        [
            history(
                "pneumococcal_20",
                "documented_doses",
                dates=[
                    date(2026, 2, 1),
                ],
            ),
            history(
                "pneumococcal_10",
                "documented_doses",
                dates=[
                    date(2026, 4, 1),
                ],
            ),
        ]
    )

    assert result["exposure_event_count"] == 2
    assert result["vpc10_exposure_count"] == 1
    assert result["vpc20_exposure_count"] == 1

    assert (
        result["mixed_vpc10_vpc20_history"]
        is True
    )

    assert [
        item["administration_date"]
        for item in result["exposures"]
    ] == [
        date(2026, 2, 1),
        date(2026, 4, 1),
    ]

    assert [
        item["source_vaccine_key"]
        for item in result["exposures"]
    ] == [
        "pneumococcal_20",
        "pneumococcal_10",
    ]


def test_absent_vpc10_is_distinct_from_documented_zero():
    absent = normalize(
        [
            history(
                "pneumococcal_20",
                "documented_zero_dose",
            ),
        ]
    )

    zero = normalize(
        [
            history(
                "pneumococcal_20",
                "documented_zero_dose",
            ),
            history(
                "pneumococcal_10",
                "documented_zero_dose",
            ),
        ]
    )

    assert absent["vpc10_history_supplied"] is False
    assert zero["vpc10_history_supplied"] is True


def test_absent_vpc20_is_distinct_from_documented_zero():
    absent = normalize(
        [
            history(
                "pneumococcal_10",
                "documented_zero_dose",
            ),
        ]
    )

    zero = normalize(
        [
            history(
                "pneumococcal_10",
                "documented_zero_dose",
            ),
            history(
                "pneumococcal_20",
                "documented_zero_dose",
            ),
        ]
    )

    assert absent["vpc20_history_supplied"] is False
    assert zero["vpc20_history_supplied"] is True


@pytest.mark.parametrize(
    "key",
    [
        "pneumococcal_10",
        "pneumococcal_20",
    ],
)
def test_unknown_relevant_history_fails_closed(
    key,
):
    result = normalize(
        [
            history(
                key,
                "unknown",
            ),
        ]
    )

    assert result["source_history_incomplete"] is True
    assert result["safe_for_role_assignment"] is False

    assert (
        result["history_state"]
        == "partial_or_uncertain"
    )


@pytest.mark.parametrize(
    "key",
    [
        "pneumococcal_10",
        "pneumococcal_20",
    ],
)
def test_partial_undated_history_fails_closed(
    key,
):
    result = normalize(
        [
            history(
                key,
                "partial_record",
                reported_prior=1,
            ),
        ]
    )

    assert result["source_history_incomplete"] is True
    assert result["safe_for_role_assignment"] is False


def test_partial_global_scope_fails_closed():
    result = normalize(
        [
            history(
                "pneumococcal_20",
                "documented_zero_dose",
            ),
        ],
        scope="partial",
    )

    assert result["safe_for_role_assignment"] is False


def test_unknown_global_scope_is_unknown():
    result = normalize(
        [],
        scope="unknown",
    )

    assert result["history_state"] == "unknown"
    assert result["safe_for_role_assignment"] is False


def test_same_day_cross_product_possible_duplicate_fails_closed():
    same_day = date(
        2026,
        6,
        1,
    )

    result = normalize(
        [
            history(
                "pneumococcal_10",
                "documented_doses",
                dates=[
                    same_day,
                ],
            ),
            history(
                "pneumococcal_20",
                "documented_doses",
                dates=[
                    same_day,
                ],
            ),
        ]
    )

    assert (
        result["ambiguous_same_day_exposure_dates"]
        == [
            same_day,
        ]
    )

    assert result["safe_for_role_assignment"] is False


def test_cross_labeled_product_key_rejected():
    bad = schemas.PniVaccineHistory(
        vaccine_key="pneumococcal_10",
        history_state="documented_doses",
        doses=[
            schemas.PniDoseRecord(
                administration_date=date(
                    2026,
                    4,
                    1,
                ),
                product_key="pneumococcal_20",
                documentation_source="official_registry",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match="incompatible product_key",
    ):
        normalize(
            [
                bad,
            ]
        )


def test_future_pneumococcal_dose_rejected():
    with pytest.raises(
        ValueError,
        match="cannot follow assessment_date",
    ):
        normalize(
            [
                history(
                    "pneumococcal_20",
                    "documented_doses",
                    dates=[
                        date(
                            2026,
                            9,
                            12,
                        ),
                    ],
                ),
            ]
        )


def test_duplicate_history_key_rejected():
    with pytest.raises(
        ValueError,
        match="duplicate vaccine history entries",
    ):
        normalize_pneumococcal_history(
            assessment_date=ASSESSMENT,
            histories=[
                history(
                    "pneumococcal_20",
                    "documented_zero_dose",
                ),
                history(
                    "pneumococcal_20",
                    "documented_zero_dose",
                ),
            ],
            history_scope="complete",
        )


@pytest.mark.parametrize(
    "key",
    [
        "ipv",
        "pentavalent",
        "hepatitis_a",
        "meningococcal_c",
        "penta_acellular_ipv",
    ],
)
def test_known_unrelated_histories_are_ignored(
    key,
):
    result = normalize(
        [
            history(
                key,
                "documented_zero_dose",
            ),
            history(
                "pneumococcal_20",
                "documented_zero_dose",
            ),
        ]
    )

    assert result["unmapped_vaccine_keys"] == []
    assert result["safe_for_role_assignment"] is True


def test_unknown_extra_product_fails_closed():
    result = normalize(
        [
            history(
                "pneumococcal_20",
                "documented_zero_dose",
            ),
            history(
                "mystery_pneumococcal_product",
                "documented_zero_dose",
            ),
        ]
    )

    assert result["unmapped_vaccine_keys"] == [
        "mystery_pneumococcal_product",
    ]

    assert result["safe_for_role_assignment"] is False


def test_normalizer_does_not_assign_dose_roles():
    result = normalize(
        [
            history(
                "pneumococcal_20",
                "documented_doses",
                dates=[
                    date(2026, 2, 1),
                    date(2026, 8, 1),
                ],
            ),
        ]
    )

    for exposure in result["exposures"]:
        assert "normalized_role" not in exposure
        assert "is_booster" not in exposure

    assert result["source_hold_11m_no_history"] is True


def test_normalizer_has_no_rie_inference_output():
    result = normalize(
        [
            history(
                "pneumococcal_20",
                "documented_zero_dose",
            ),
        ]
    )

    assert "special_condition_inferred" not in result
    assert "rie_indicated" not in result
