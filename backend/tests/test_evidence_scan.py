import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def scan_environment(monkeypatch):

    # Mock evidence collector
    collected_records = [
        {
            "id": 1,
            "file_name": "evidence1.txt",
            "file_path": "evidence/test_files/evidence1.txt",
            "file_size": 100,
            "sha256": "abc123",
            "status": "COLLECTED",
        },
        {
            "id": 2,
            "file_name": "evidence2.txt",
            "file_path": "evidence/test_files/evidence2.txt",
            "file_size": 200,
            "sha256": "def456",
            "status": "COLLECTED",
        },
    ]

    collector_result = {
        "audit_id": "test-audit-123",
        "files_scanned": 2,
        "records": collected_records,
        "errors": [],
    }

    def fake_collect_evidence(path):
        return collector_result

    # Mock database
    saved_records = []

    def fake_save_evidence(records):
        saved_records.extend(records)
        return len(records)

    # Mock audit logging
    audit_events = []

    def fake_log_event(**kwargs):
        audit_events.append(kwargs)

    # Mock custody recording
    custody_events = []

    def fake_record_custody_event(**kwargs):
        custody_events.append(kwargs)
        return kwargs

    monkeypatch.setattr(
        main,
        "collect_evidence",
        fake_collect_evidence,
    )

    monkeypatch.setattr(
        main,
        "save_evidence",
        fake_save_evidence,
    )

    monkeypatch.setattr(
        main,
        "log_event",
        fake_log_event,
    )

    monkeypatch.setattr(
        main,
        "record_custody_event",
        fake_record_custody_event,
    )

    client = TestClient(main.app)

    return {
        "client": client,
        "collector_result": collector_result,
        "saved_records": saved_records,
        "audit_events": audit_events,
        "custody_events": custody_events,
    }


def test_successful_evidence_scan(scan_environment):

    client = scan_environment["client"]

    response = client.post(
        "/api/v1/evidence/scan"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Evidence scan completed"
    assert data["audit_id"] == "test-audit-123"
    assert data["files_scanned"] == 2
    assert data["records_saved"] == 2
    assert data["errors"] == []

    # Verify records were saved
    assert len(scan_environment["saved_records"]) == 2

    # Verify successful audit logging
    events = scan_environment["audit_events"]

    assert any(
        event["event"] == "EVIDENCE_SCAN_COMPLETED"
        and event["status"] == "SUCCESS"
        for event in events
    )

    # Verify custody events
    custody = scan_environment["custody_events"]

    assert len(custody) == 2

    assert all(
        event["action"] == "EVIDENCE_COLLECTED"
        for event in custody
    )


def test_empty_evidence_scan(scan_environment):

    client = scan_environment["client"]

    scan_environment["collector_result"].update({
        "files_scanned": 0,
        "records": [],
        "errors": [],
    })

    response = client.post(
        "/api/v1/evidence/scan"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["files_scanned"] == 0
    assert data["records_saved"] == 0
    assert data["records"] == []

    assert scan_environment["saved_records"] == []
    assert scan_environment["custody_events"] == []


def test_scan_with_collector_errors(scan_environment):

    client = scan_environment["client"]

    scan_environment["collector_result"]["errors"] = [
        "Permission denied: restricted_file.txt"
    ]

    response = client.post(
        "/api/v1/evidence/scan"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["files_scanned"] == 2

    assert (
        "Permission denied: restricted_file.txt"
        in data["errors"]
    )


def test_scan_database_failure(scan_environment, monkeypatch):

    client = scan_environment["client"]

    def failing_save(records):
        raise RuntimeError("Simulated database failure")

    monkeypatch.setattr(
        main,
        "save_evidence",
        failing_save,
    )

    response = client.post(
        "/api/v1/evidence/scan"
    )

    assert response.status_code == 500

    data = response.json()

    assert "Simulated database failure" in data["detail"]

    # Failure must be logged
    events = scan_environment["audit_events"]

    assert any(
        event["event"] == "EVIDENCE_SCAN_FAILED"
        and event["status"] == "ERROR"
        for event in events
    )