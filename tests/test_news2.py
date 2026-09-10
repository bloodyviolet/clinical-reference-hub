from pathlib import Path
import json
import sys

import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


import main  # noqa: E402

from clinical_tools.news2 import (  # noqa: E402
    NEWS2_METADATA,
    calculate_news2,
)


client = TestClient(main.app)


VECTORS = json.loads(
    (
        PROJECT_ROOT
        / "tests"
        / "fixtures"
        / "news2_vectors.json"
    ).read_text(
        encoding="utf-8"
    )
)


def baseline():
    return dict(
        VECTORS[0]["input"]
    )


def test_shared_news2_vectors():
    for vector in VECTORS:
        result = calculate_news2(
            **vector["input"]
        )

        assert (
            result["total"]
            == vector["total"]
        )

        assert (
            result["trigger_code"]
            == vector["trigger"]
        )

        assert result["aggregate_label_pt"]
        assert result["aggregate_label_en"]

        assert result["monitoring_pt"]
        assert result["monitoring_en"]

        assert result["response_pt"]
        assert result["response_en"]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (8, 3),
        (9, 1),
        (11, 1),
        (12, 0),
        (20, 0),
        (21, 2),
        (24, 2),
        (25, 3),
    ],
)
def test_respiration_boundaries(
    value,
    expected,
):
    payload = baseline()

    payload[
        "respiration_rate"
    ] = value

    result = calculate_news2(
        **payload
    )

    assert (
        result["components"]
        ["respiration_rate"]
        == expected
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (91, 3),
        (92, 2),
        (93, 2),
        (94, 1),
        (95, 1),
        (96, 0),
        (100, 0),
    ],
)
def test_spo2_scale1_boundaries(
    value,
    expected,
):
    payload = baseline()
    payload["spo2"] = value

    result = calculate_news2(
        **payload
    )

    assert (
        result["components"]["spo2"]
        == expected
    )


@pytest.mark.parametrize(
    (
        "value",
        "oxygen",
        "expected",
    ),
    [
        (83, False, 3),
        (84, False, 2),
        (85, False, 2),
        (86, False, 1),
        (87, False, 1),
        (88, False, 0),
        (92, False, 0),
        (93, False, 0),
        (100, False, 0),

        (88, True, 0),
        (92, True, 0),
        (93, True, 1),
        (94, True, 1),
        (95, True, 2),
        (96, True, 2),
        (97, True, 3),
        (100, True, 3),
    ],
)
def test_spo2_scale2_boundaries(
    value,
    oxygen,
    expected,
):
    payload = baseline()

    payload.update({
        "spo2": value,
        "spo2_scale": 2,
        "scale2_prescribed": True,
        "supplemental_oxygen":
            oxygen,
    })

    result = calculate_news2(
        **payload
    )

    assert (
        result["components"]["spo2"]
        == expected
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (90, 3),
        (91, 2),
        (100, 2),
        (101, 1),
        (110, 1),
        (111, 0),
        (219, 0),
        (220, 3),
    ],
)
def test_systolic_boundaries(
    value,
    expected,
):
    payload = baseline()
    payload["systolic_bp"] = value

    result = calculate_news2(
        **payload
    )

    assert (
        result["components"]
        ["systolic_bp"]
        == expected
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (40, 3),
        (41, 1),
        (50, 1),
        (51, 0),
        (90, 0),
        (91, 1),
        (110, 1),
        (111, 2),
        (130, 2),
        (131, 3),
    ],
)
def test_pulse_boundaries(
    value,
    expected,
):
    payload = baseline()
    payload["pulse"] = value

    result = calculate_news2(
        **payload
    )

    assert (
        result["components"]["pulse"]
        == expected
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (35.0, 3),
        (35.1, 1),
        (36.0, 1),
        (36.1, 0),
        (38.0, 0),
        (38.1, 1),
        (39.0, 1),
        (39.1, 2),
    ],
)
def test_temperature_boundaries(
    value,
    expected,
):
    payload = baseline()

    payload[
        "temperature"
    ] = value

    result = calculate_news2(
        **payload
    )

    assert (
        result["components"]
        ["temperature"]
        == expected
    )


@pytest.mark.parametrize(
    "state",
    [
        "new_confusion",
        "voice",
        "pain",
        "unresponsive",
    ],
)
def test_non_alert_consciousness_scores_three(
    state,
):
    payload = baseline()

    payload[
        "consciousness"
    ] = state

    result = calculate_news2(
        **payload
    )

    assert (
        result["components"]
        ["consciousness"]
        == 3
    )

    assert (
        result[
            "single_parameter_red_score"
        ]
        is True
    )


def test_scale2_requires_explicit_prescription():
    payload = baseline()

    payload.update({
        "spo2_scale": 2,
        "scale2_prescribed": False,
    })

    with pytest.raises(
        ValueError,
        match="88-92%",
    ):
        calculate_news2(
            **payload
        )


def test_supplemental_oxygen_adds_two():
    payload = baseline()

    payload[
        "supplemental_oxygen"
    ] = True

    result = calculate_news2(
        **payload
    )

    assert (
        result["components"]
        ["supplemental_oxygen"]
        == 2
    )

    assert result["total"] == 2


def test_single_red_is_not_medium_band():
    payload = baseline()

    payload[
        "respiration_rate"
    ] = 8

    result = calculate_news2(
        **payload
    )

    assert result["total"] == 3

    assert (
        result["aggregate_band"]
        == "low"
    )

    assert (
        result["trigger_code"]
        == "single_red"
    )

    assert (
        result["monitoring_code"]
        == "minimum_hourly"
    )


def test_api_endpoint_serializes_bilingual_result():
    response = client.post(
        "/api/v1/tools/news2",
        json=baseline(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["tool"] == "news2"
    assert payload["total"] == 0

    assert payload[
        "aggregate_label_pt"
    ]

    assert payload[
        "aggregate_label_en"
    ]

    assert payload[
        "response_pt"
    ]

    assert payload[
        "response_en"
    ]


def test_api_rejects_unprescribed_scale2():
    payload = baseline()

    payload.update({
        "spo2_scale": 2,
        "scale2_prescribed": False,
    })

    response = client.post(
        "/api/v1/tools/news2",
        json=payload,
    )

    assert response.status_code == 422

    assert (
        "88-92%"
        in response.json()["detail"]
    )


def test_metadata_contract_is_bilingual():
    response = client.get(
        "/api/v1/tools/news2/meta"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == "news2"

    assert payload[
        "publisher"
    ] == (
        "Royal College of Physicians"
    )

    assert payload[
        "source_language"
    ] == "en-GB"

    assert payload[
        "canonical_language"
    ] == "en-GB"

    assert payload[
        "translation_status_en"
    ] == "official_original"

    assert payload[
        "translation_status_pt"
    ] == (
        "local_translation_"
        "with_disclaimer_required"
    )

    assert payload[
        "translation_disclaimer_required"
    ] is True

    assert payload["aliases_pt"]
    assert payload["aliases_en"]

    assert payload["limitations_pt"]
    assert payload["limitations_en"]

    assert (
        "20 semanas"
        in " ".join(
            payload[
                "limitations_pt"
            ]
        )
    )

    assert (
        "20 weeks"
        in " ".join(
            payload[
                "limitations_en"
            ]
        )
    )


def test_metadata_provenance_does_not_claim_2022_revision():
    assert (
        "revision 2022"
        not in NEWS2_METADATA[
            "source_version"
        ]
    )

    assert (
        "2017"
        in NEWS2_METADATA[
            "source_version"
        ]
    )

    assert (
        "2021"
        in NEWS2_METADATA[
            "source_version"
        ]
    )
