from __future__ import annotations

from pathlib import Path
import sys

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )


import main  # noqa: E402


client = TestClient(main.app)


def test_growth_api_official_under5_vector():
    response = client.post(
        "/api/v1/tools/who-growth",
        json={
            "sex": "male",
            "age_value": 1001,
            "age_unit": "days",
            "weight_kg": 18,
            "length_height_cm": 120,
            "measurement_position": "height",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    indicators = payload[
        "indicators"
    ]

    assert (
        indicators[
            "length_height_for_age"
        ][
            "z_score"
        ]
        == 7.31
    )

    assert (
        indicators[
            "weight_for_age"
        ][
            "z_score"
        ]
        == 2.2
    )

    assert (
        indicators[
            "weight_for_length_height"
        ][
            "z_score"
        ]
        == -2.39
    )

    assert (
        indicators[
            "bmi_for_age"
        ][
            "z_score"
        ]
        == -3.01
    )


def test_growth_api_separates_who_and_sisvan():
    response = client.post(
        "/api/v1/tools/who-growth",
        json={
            "sex": "male",
            "age_value": 1001,
            "age_unit": "days",
            "weight_kg": 18,
            "length_height_cm": 120,
            "measurement_position": "height",
        },
    )

    assert response.status_code == 200

    result = response.json()[
        "indicators"
    ][
        "weight_for_length_height"
    ]

    assert (
        result[
            "classification_who"
        ][
            "code"
        ]
        == "wasted"
    )

    assert (
        result[
            "classification_br"
        ][
            "code"
        ]
        == "thinness"
    )


def test_growth_api_official_anthroplus_vector():
    response = client.post(
        "/api/v1/tools/who-growth",
        json={
            "sex": "male",
            "age_value": 100,
            "age_unit": "months",
            "weight_kg": 30,
            "length_height_cm": 100,
            "measurement_position": "height",
        },
    )

    assert response.status_code == 200

    indicators = response.json()[
        "indicators"
    ]

    assert (
        indicators[
            "length_height_for_age"
        ][
            "z_score"
        ]
        == -5.04
    )

    assert (
        indicators[
            "weight_for_age"
        ][
            "z_score"
        ]
        == 0.87
    )

    assert (
        indicators[
            "bmi_for_age"
        ][
            "z_score"
        ]
        == 5.03
    )

    assert (
        indicators[
            "bmi_for_age"
        ][
            "classification_who"
        ][
            "code"
        ]
        == "obesity"
    )

    assert (
        indicators[
            "bmi_for_age"
        ][
            "classification_br"
        ][
            "code"
        ]
        == "severe_obesity"
    )


def test_growth_api_requires_measurement():
    response = client.post(
        "/api/v1/tools/who-growth",
        json={
            "sex": "female",
            "age_value": 12,
            "age_unit": "months",
        },
    )

    assert response.status_code == 422

    assert (
        "At least one anthropometric"
        in response.json()["detail"]
    )


def test_growth_api_rejects_2007_recumbent_length():
    response = client.post(
        "/api/v1/tools/who-growth",
        json={
            "sex": "female",
            "age_value": 100,
            "age_unit": "months",
            "length_height_cm": 140,
            "measurement_position": "length",
        },
    )

    assert response.status_code == 422


def test_growth_api_metadata_contract():
    response = client.get(
        "/api/v1/tools/who-growth/meta"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["id"]
        == "who-pediatric-growth"
    )

    assert (
        payload["offline_capable"]
        is True
    )

    assert payload["name_pt"]
    assert payload["name_en"]
    assert payload["limitations_pt"]
    assert payload["limitations_en"]

    assert (
        "WHO Child Growth Standards 2006"
        in payload["source_title"]
    )
