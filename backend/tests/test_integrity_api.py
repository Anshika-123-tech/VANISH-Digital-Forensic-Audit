from fastapi.testclient import TestClient

import main


def test_integrity_api_success(monkeypatch):
    mock_result = {
        "audit_id": "audit-api-001",
        "total_files": 1,
        "intact": 1,
        "modified": 0,
        "missing": 0,
        "invalid": 0,
        "overall_status": "INTEGRITY_VERIFIED",
        "results": [],
    }

    custody_events = []

    monkeypatch.setattr(
        main,
        "verify_audit",
        lambda audit_id: mock_result,
    )

    monkeypatch.setattr(
        main,
        "record_custody_event",
        lambda **kwargs: custody_events.append(kwargs),
    )

    client = TestClient(main.app)

    response = client.get(
        "/api/v1/evidence/verify/audit-api-001"
    )

    assert response.status_code == 200
    assert response.json()["overall_status"] == "INTEGRITY_VERIFIED"

    assert len(custody_events) == 1
    assert custody_events[0]["action"] == "INTEGRITY_VERIFIED"
    assert custody_events[0]["actor"] == "VANISH_SYSTEM"


def test_integrity_api_detects_failure(monkeypatch):
    mock_result = {
        "audit_id": "audit-api-002",
        "total_files": 1,
        "intact": 0,
        "modified": 1,
        "missing": 0,
        "invalid": 0,
        "overall_status": "INTEGRITY_FAILURE",
        "results": [],
    }

    custody_events = []

    monkeypatch.setattr(
        main,
        "verify_audit",
        lambda audit_id: mock_result,
    )

    monkeypatch.setattr(
        main,
        "record_custody_event",
        lambda **kwargs: custody_events.append(kwargs),
    )

    client = TestClient(main.app)

    response = client.get(
        "/api/v1/evidence/verify/audit-api-002"
    )

    assert response.status_code == 200
    assert response.json()["overall_status"] == "INTEGRITY_FAILURE"

    assert len(custody_events) == 1
    assert custody_events[0]["action"] == "INTEGRITY_FAILURE"


def test_integrity_api_returns_404_for_missing_audit(monkeypatch):
    mock_result = {
        "audit_id": "audit-api-003",
        "status": "not_found",
        "message": "No evidence records found for this audit.",
    }

    custody_events = []

    monkeypatch.setattr(
        main,
        "verify_audit",
        lambda audit_id: mock_result,
    )

    monkeypatch.setattr(
        main,
        "record_custody_event",
        lambda **kwargs: custody_events.append(kwargs),
    )

    client = TestClient(main.app)

    response = client.get(
        "/api/v1/evidence/verify/audit-api-003"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "No evidence records found for this audit."
    )

    # No custody event should be recorded for a missing audit.
    assert len(custody_events) == 0


def test_integrity_api_custody_contains_verification_result(
    monkeypatch,
):
    mock_result = {
        "audit_id": "audit-api-004",
        "total_files": 2,
        "intact": 1,
        "modified": 1,
        "missing": 0,
        "invalid": 0,
        "overall_status": "INTEGRITY_FAILURE",
        "results": [
            {"file_name": "file1.txt", "status": "intact"},
            {"file_name": "file2.txt", "status": "modified"},
        ],
    }

    custody_events = []

    monkeypatch.setattr(
        main,
        "verify_audit",
        lambda audit_id: mock_result,
    )

    monkeypatch.setattr(
        main,
        "record_custody_event",
        lambda **kwargs: custody_events.append(kwargs),
    )

    client = TestClient(main.app)

    response = client.get(
        "/api/v1/evidence/verify/audit-api-004"
    )

    assert response.status_code == 200

    custody_details = custody_events[0]["details"]

    assert custody_details["verification_status"] == (
        "INTEGRITY_FAILURE"
    )

    assert custody_details["verification_result"] == mock_result
def test_integrity_api_includes_forensic_analysis(monkeypatch):
    mock_result = {
        "audit_id": "audit-ai-api-001",
        "total_files": 2,
        "intact": 2,
        "modified": 0,
        "missing": 0,
        "invalid": 0,
        "overall_status": "INTEGRITY_VERIFIED",
        "results": [
            {"file_name": "file1.txt", "status": "intact"},
            {"file_name": "file2.txt", "status": "intact"},
        ],
    }

    monkeypatch.setattr(
        main,
        "verify_audit",
        lambda audit_id: mock_result.copy(),
    )

    monkeypatch.setattr(
        main,
        "record_custody_event",
        lambda **kwargs: None,
    )

    client = TestClient(main.app)

    response = client.get(
        "/api/v1/evidence/verify/audit-ai-api-001"
    )

    assert response.status_code == 200

    data = response.json()

    assert "forensic_analysis" in data
    assert data["forensic_analysis"]["analysis_status"] == "COMPLETED"
    assert data["forensic_analysis"]["risk_level"] == "LOW"
    assert data["forensic_analysis"]["risk_score"] == 0
    assert data["forensic_analysis"]["findings"] == []