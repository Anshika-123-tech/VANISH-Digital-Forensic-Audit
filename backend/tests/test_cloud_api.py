from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


def mock_audit_and_custody(monkeypatch):
    monkeypatch.setattr(main, "log_event", lambda **kwargs: None)
    monkeypatch.setattr(main, "record_custody_event", lambda **kwargs: None)


def test_cloud_verification_success(monkeypatch):
    mock_audit_and_custody(monkeypatch)

    monkeypatch.setattr(
        main,
        "analyze_cloud_evidence",
        lambda evidence: {
            "verification_status": "VERIFIED",
            "risk_level": "LOW",
            "findings": [],
            "recommendations": [],
            "summary": "Cloud deletion evidence verified.",
        },
    )

    response = client.post(
        "/api/v1/cloud/verify",
        json={"deletion_confirmed": True},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["verification_status"] == "VERIFIED"
    assert data["risk_level"] == "LOW"
    assert "verification_id" in data


def test_cloud_verification_failed(monkeypatch):
    mock_audit_and_custody(monkeypatch)

    monkeypatch.setattr(
        main,
        "analyze_cloud_evidence",
        lambda evidence: {
            "verification_status": "FAILED",
            "risk_level": "HIGH",
            "findings": ["Residual objects detected"],
            "recommendations": ["Investigate residual objects"],
            "summary": "Deletion verification failed.",
        },
    )

    response = client.post(
        "/api/v1/cloud/verify",
        json={"deletion_confirmed": False},
    )

    assert response.status_code == 200
    assert response.json()["verification_status"] == "FAILED"
    assert response.json()["risk_level"] == "HIGH"


def test_cloud_verification_inconclusive(monkeypatch):
    mock_audit_and_custody(monkeypatch)

    monkeypatch.setattr(
        main,
        "analyze_cloud_evidence",
        lambda evidence: {
            "verification_status": "INCONCLUSIVE",
            "risk_level": "MEDIUM",
            "findings": ["Evidence incomplete"],
            "recommendations": ["Collect additional evidence"],
            "summary": "Verification is inconclusive.",
        },
    )

    response = client.post(
        "/api/v1/cloud/verify",
        json={},
    )

    assert response.status_code == 200
    assert response.json()["verification_status"] == "INCONCLUSIVE"


def test_cloud_verification_invalid_input(monkeypatch):
    mock_audit_and_custody(monkeypatch)

    monkeypatch.setattr(
        main,
        "analyze_cloud_evidence",
        lambda evidence: (_ for _ in ()).throw(
            ValueError("Invalid cloud evidence")
        ),
    )

    response = client.post(
        "/api/v1/cloud/verify",
        json={"residual_objects": "invalid"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid cloud evidence"