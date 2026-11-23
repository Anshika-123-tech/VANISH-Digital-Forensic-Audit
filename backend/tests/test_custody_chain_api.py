from fastapi.testclient import TestClient

import main


def test_custody_chain_api_verified(monkeypatch):
    mock_result = {
        "status": "CHAIN_VERIFIED",
        "total_events": 5,
        "verified_events": 5,
        "tampered_events": 0,
        "errors": [],
    }

    monkeypatch.setattr(
        main,
        "verify_custody_chain",
        lambda: mock_result,
    )

    client = TestClient(main.app)

    response = client.get(
        "/api/v1/custody/chain/verify"
    )

    assert response.status_code == 200
    assert response.json() == mock_result
    assert response.json()["status"] == "CHAIN_VERIFIED"


def test_custody_chain_api_tampered(monkeypatch):
    mock_result = {
        "status": "CHAIN_INTEGRITY_FAILURE",
        "total_events": 5,
        "verified_events": 3,
        "tampered_events": 2,
        "errors": [
            {"line": 3, "error": "Event hash mismatch"},
            {"line": 4, "error": "Previous hash mismatch"},
        ],
    }

    monkeypatch.setattr(
        main,
        "verify_custody_chain",
        lambda: mock_result,
    )

    client = TestClient(main.app)

    response = client.get(
        "/api/v1/custody/chain/verify"
    )

    assert response.status_code == 200
    assert response.json()["status"] == (
        "CHAIN_INTEGRITY_FAILURE"
    )
    assert response.json()["tampered_events"] == 2
    assert len(response.json()["errors"]) == 2


def test_custody_chain_api_empty(monkeypatch):
    mock_result = {
        "status": "EMPTY",
        "total_events": 0,
        "verified_events": 0,
        "tampered_events": 0,
        "message": "No custody events found.",
    }

    monkeypatch.setattr(
        main,
        "verify_custody_chain",
        lambda: mock_result,
    )

    client = TestClient(main.app)

    response = client.get(
        "/api/v1/custody/chain/verify"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "EMPTY"
    assert response.json()["total_events"] == 0