import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def upload_environment(tmp_path, monkeypatch):
    """Create an isolated environment for upload tests."""

    # Temporary upload storage
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True)

    monkeypatch.setattr(main, "UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(main, "BASE_DIR", tmp_path)

    # Mock database functions
    saved_records = []

    def fake_save_evidence(records):
        saved_records.extend(records)
        return len(records)

    def fake_get_evidence_by_audit(audit_id):
        return [
            {"id": index + 1}
            for index, record in enumerate(saved_records)
            if record["audit_id"] == audit_id
        ]

    # Mock audit logging
    audit_events = []

    def fake_log_event(event, audit_id, status, details):
        audit_events.append({
            "event": event,
            "audit_id": audit_id,
            "status": status,
            "details": details,
        })

    # Mock chain of custody
    custody_events = []

    def fake_record_custody_event(
        audit_id,
        action,
        actor,
        evidence_id,
        details,
    ):
        event = {
            "audit_id": audit_id,
            "action": action,
            "actor": actor,
            "evidence_id": evidence_id,
            "details": details,
        }

        custody_events.append(event)
        return event

    monkeypatch.setattr(
        main,
        "save_evidence",
        fake_save_evidence,
    )

    monkeypatch.setattr(
        main,
        "get_evidence_by_audit",
        fake_get_evidence_by_audit,
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
        "upload_dir": upload_dir,
        "saved_records": saved_records,
        "audit_events": audit_events,
        "custody_events": custody_events,
    }


def test_successful_upload(upload_environment):

    client = upload_environment["client"]

    content = b"VANISH evidence upload test"

    response = client.post(
        "/api/v1/evidence/upload",
        files={
            "file": (
                "evidence.txt",
                content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    # Verify response
    assert data["status"] == "COLLECTED"
    assert data["file_name"] == "evidence.txt"
    assert data["file_size"] == len(content)
    assert data["database_records_saved"] == 1
    assert data["custody_status"] == "RECORDED"

    # Verify SHA-256
    expected_hash = hashlib.sha256(content).hexdigest()

    assert data["sha256"] == expected_hash

    # Verify actual file exists
    uploaded_file = Path(data["storage_path"])

    assert uploaded_file.exists()
    assert uploaded_file.read_bytes() == content

    # Verify database record
    records = upload_environment["saved_records"]

    assert len(records) == 1
    assert records[0]["sha256"] == expected_hash
    assert records[0]["file_size"] == len(content)
    assert records[0]["status"] == "COLLECTED"

    # Verify audit logging
    events = upload_environment["audit_events"]

    assert any(
        event["event"] == "EVIDENCE_UPLOAD_COMPLETED"
        for event in events
    )

    # Verify chain of custody
    custody = upload_environment["custody_events"]

    assert any(
        event["action"] == "EVIDENCE_COLLECTED"
        for event in custody
    )


def test_duplicate_filename_creates_unique_files(
    upload_environment,
):

    client = upload_environment["client"]

    content1 = b"First evidence file"
    content2 = b"Second evidence file"

    response1 = client.post(
        "/api/v1/evidence/upload",
        files={
            "file": (
                "same.txt",
                content1,
                "text/plain",
            )
        },
    )

    response2 = client.post(
        "/api/v1/evidence/upload",
        files={
            "file": (
                "same.txt",
                content2,
                "text/plain",
            )
        },
    )

    assert response1.status_code == 200
    assert response2.status_code == 200

    data1 = response1.json()
    data2 = response2.json()

    # Stored filenames must be different
    assert data1["storage_path"] != data2["storage_path"]

    # Both files must exist
    assert Path(data1["storage_path"]).exists()
    assert Path(data2["storage_path"]).exists()

    # Contents must remain correct
    assert Path(data1["storage_path"]).read_bytes() == content1
    assert Path(data2["storage_path"]).read_bytes() == content2


def test_filename_path_traversal_is_sanitized(
    upload_environment,
):

    client = upload_environment["client"]

    response = client.post(
        "/api/v1/evidence/upload",
        files={
            "file": (
                "..\\..\\sensitive.txt",
                b"Safe test content",
                "text/plain",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    # Original filename should be sanitized
    assert data["file_name"] == "sensitive.txt"

    # Stored file must remain inside upload directory
    saved_path = Path(data["storage_path"]).resolve()
    upload_dir = upload_environment["upload_dir"].resolve()

    assert saved_path.is_relative_to(upload_dir)

    assert saved_path.exists()


def test_oversized_upload_is_rejected(
    upload_environment,
    monkeypatch,
):

    client = upload_environment["client"]

    # Lower the limit for a fast test
    monkeypatch.setattr(main, "MAX_UPLOAD_SIZE", 10)

    content = b"A" * 11

    response = client.post(
        "/api/v1/evidence/upload",
        files={
            "file": (
                "large.txt",
                content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 413

    # No oversized file should remain
    upload_dir = upload_environment["upload_dir"]

    assert list(upload_dir.iterdir()) == []
def test_database_failure_removes_uploaded_file(
    upload_environment,
    monkeypatch,
):

    client = upload_environment["client"]

    def failing_save(records):
        raise RuntimeError("Simulated database failure")

    monkeypatch.setattr(
        main,
        "save_evidence",
        failing_save,
    )

    response = client.post(
        "/api/v1/evidence/upload",
        files={
            "file": (
                "failure_test.txt",
                b"Test content",
                "text/plain",
            )
        },
    )

    assert response.status_code == 500

    # Uploaded file must be cleaned up
    upload_dir = upload_environment["upload_dir"]

    assert list(upload_dir.iterdir()) == []

    # Failure must be logged
    events = upload_environment["audit_events"]

    assert any(
        event["event"] == "EVIDENCE_UPLOAD_FAILED"
        for event in events
    )


def test_custody_failure_is_reported(
    upload_environment,
    monkeypatch,
):

    client = upload_environment["client"]

    def failing_custody(
        audit_id,
        action,
        actor,
        evidence_id,
        details,
    ):
        raise RuntimeError("Simulated custody failure")

    monkeypatch.setattr(
        main,
        "record_custody_event",
        failing_custody,
    )

    response = client.post(
        "/api/v1/evidence/upload",
        files={
            "file": (
                "custody_test.txt",
                b"Test content",
                "text/plain",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    # Upload succeeds, but custody failure is reported
    assert data["status"] == "COLLECTED"
    assert data["custody_status"] == "FAILED"

    # Evidence file should still exist
    assert Path(data["storage_path"]).exists()

    # Failure should be logged
    events = upload_environment["audit_events"]

    assert any(
        event["event"] == "CUSTODY_RECORDING_FAILED"
        for event in events
    )