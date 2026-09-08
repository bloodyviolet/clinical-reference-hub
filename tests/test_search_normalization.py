from fastapi.testclient import TestClient

import main


client = TestClient(main.app)

EXPECTED_NUTRITION_CODES = [
    "00269",
    "00270",
    "00343",
    "00359",
    "00360",
    "00409",
    "00419",
]


def _codes(query: str) -> list[str]:
    response = client.get(
        "/api/v1/sae/search",
        params={
            "q": query,
            "limit": 50,
        },
    )

    assert response.status_code == 200

    return [
        item["code"]
        for item in response.json()["items"]
    ]


def test_sae_search_is_accent_and_case_insensitive():
    for query in (
        "nutrição",
        "nutricao",
        "NUTRIÇÃO",
    ):
        assert _codes(query) == (
            EXPECTED_NUTRITION_CODES
        )


def test_normalise_search_matches_offline_contract():
    assert (
        main._normalise_search("NUTRIÇÃO")
        == main._normalise_search("nutricao")
        == "nutricao"
    )
