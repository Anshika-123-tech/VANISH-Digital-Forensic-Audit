import hashlib
import uuid

import pytest
from fastapi.testclient import TestClient

import main
import core.sanitization_report_generator as report_generator

@pytest.fixture
def test_environment(tmp_path, monkeypatch):
    """
    Creates an isolated VANISH test environment.
    """

    # Temporary project directory
    monkeypatch.setattr(main, "BASE_DIR", tmp_path)
    monkeypatch.setattr(report_generator, "BASE_DIR", tmp_path)

    # Temporary report directory
    report_dir = tmp_path / "reports" / "sanitization"

    monkeypatch.setattr(
        report_generator,
        "REPORT_DIR",
        report_dir,
    )

    # Temporary evidence directory
    evidence_dir = tmp_path / "evidence" / "test_files"
    evidence_dir.mkdir(parents=True)

    report_dir.mkdir(parents=True)

    # Create synthetic test evidence
    test_file = evidence_dir / "test_probe.txt"
    marker = "VANISH_AUTOMATED_TEST_MARKER"
    test_file.write_text(marker, encoding="utf-8")

    # Store mocked audit events
    audit_events = []

    # Store mocked custody events
    custody_events = []

    def fake_log_event(event, status, details):
        audit_events.append({
            "event": event,
            "status": status,
            "details": details,
        })

    def fake_record_custody_event(
        audit_id,
        action,
        actor,
        details,
    ):
        event = {
            "audit_id": audit_id,
            "action": action,
            "actor": actor,
            "details": details,
        }

        custody_events.append(event)
        return event

    def fake_get_custody_events(audit_id):
        return [
            event
            for event in custody_events
            if event["audit_id"] == audit_id
        ]

    # Replace logging and custody functions
    monkeypatch.setattr(main, "log_event", fake_log_event)

    monkeypatch.setattr(
        main,
        "record_custody_event",
        fake_record_custody_event,
    )

    monkeypatch.setattr(
        main,
        "get_custody_events",
        fake_get_custody_events,
    )

    # FastAPI test client
    client = TestClient(main.app)

    return {
        "client": client,
        "test_file": test_file,
        "report_dir": report_dir,
        "marker": marker,
        "audit_events": audit_events,
        "custody_events": custody_events,
    }


def generate_report(environment):
    """
    Generates a sanitization report through the API.
    """

    client = environment["client"]
    test_file = environment["test_file"]
    marker = environment["marker"]

    response = client.post(
        "/api/v1/sanitization/verify",
        params={
            "target_path": str(test_file),
            "sanitization_method": "file_deletion",
            "storage_type": "filesystem",
            "residual_marker": marker,
        },
    )

    assert response.status_code == 200

    result = response.json()

    verification_id = result["verification_id"]

    report_path = (
        environment["report_dir"]
        / f"{verification_id}.json"
    )

    return result, verification_id, report_path


def test_report_generation_and_hash_recording(
    test_environment,
):
    """
    Report should be generated and its SHA-256 hash
    should be recorded in custody.
    """

    result, verification_id, report_path = (
        generate_report(test_environment)
    )

    assert result["report_generation"]["report_status"] == "GENERATED"

    assert (
        result["report_generation"]["custody_status"]
        == "RECORDED"
    )

    assert report_path.exists()

    # Calculate hash independently
    actual_hash = hashlib.sha256(
        report_path.read_bytes()
    ).hexdigest()

    assert (
        result["report_generation"]["report_hash"]
        == actual_hash
    )

    # Confirm trusted hash exists in custody
    events = test_environment["custody_events"]

    report_event = next(
        event
        for event in events
        if event["action"]
        == "SANITIZATION_REPORT_GENERATED"
    )

    assert (
        report_event["details"]["report_hash"]
        == actual_hash
    )

    assert (
        report_event["audit_id"]
        == verification_id
    )


def test_valid_report_retrieval_is_verified(
    test_environment,
):
    """
    Untampered report should return HTTP 200
    and VERIFIED status.
    """

    _, verification_id, _ = generate_report(
        test_environment
    )

    response = test_environment["client"].get(
        f"/api/v1/sanitization/report/{verification_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["integrity_status"] == "VERIFIED"

    assert (
        data["report_hash"]
        == data["expected_hash"]
    )

    assert data["hash_algorithm"] == "SHA-256"


def test_tampered_report_is_rejected(
    test_environment,
):
    """
    Modified report should return HTTP 409
    and TAMPERED status.
    """

    _, verification_id, report_path = (
        generate_report(test_environment)
    )

    # Modify report bytes
    with open(report_path, "ab") as report_file:
        report_file.write(b"\nTAMPERING_TEST")

    response = test_environment["client"].get(
        f"/api/v1/sanitization/report/{verification_id}"
    )

    assert response.status_code == 409

    data = response.json()["detail"]

    assert data["integrity_status"] == "TAMPERED"

    assert (
        data["expected_hash"]
        != data["actual_hash"]
    )

    # Confirm tampering audit event was recorded
    audit_events = test_environment["audit_events"]

    assert any(
        event["event"]
        == "SANITIZATION_REPORT_INTEGRITY_FAILURE"
        for event in audit_events
    )

    # Confirm tampering custody event was recorded
    custody_events = test_environment["custody_events"]

    assert any(
        event["action"]
        == "SANITIZATION_REPORT_INTEGRITY_FAILURE"
        for event in custody_events
    )


def test_restored_report_is_verified(
    test_environment,
):
    """
    Restoring the original report bytes should
    restore VERIFIED status.
    """

    _, verification_id, report_path = (
        generate_report(test_environment)
    )

    # Save original report
    original_bytes = report_path.read_bytes()

    # Simulate tampering
    report_path.write_bytes(
        original_bytes + b"\nTAMPERING_TEST"
    )

    tampered_response = (
        test_environment["client"].get(
            f"/api/v1/sanitization/report/{verification_id}"
        )
    )

    assert tampered_response.status_code == 409

    # Restore original bytes
    report_path.write_bytes(original_bytes)

    restored_response = (
        test_environment["client"].get(
            f"/api/v1/sanitization/report/{verification_id}"
        )
    )

    assert restored_response.status_code == 200

    assert (
        restored_response.json()["integrity_status"]
        == "VERIFIED"
    )


def test_missing_report_returns_404(
    test_environment,
):
    """
    A valid UUID with no report should return 404.
    """

    missing_id = str(uuid.uuid4())

    response = test_environment["client"].get(
        f"/api/v1/sanitization/report/{missing_id}"
    )

    assert response.status_code == 404


def test_invalid_verification_id_returns_400(
    test_environment,
):
    """
    Invalid verification ID should return HTTP 400.
    """

    response = test_environment["client"].get(
        "/api/v1/sanitization/report/not-a-valid-uuid"
    )

    assert response.status_code == 400
def test_report_without_trusted_hash_is_unverified(
    test_environment,
):
    """
    A report without a trusted custody hash must not
    be incorrectly marked VERIFIED.
    """

    verification_id = str(uuid.uuid4())

    report_path = (
        test_environment["report_dir"]
        / f"{verification_id}.json"
    )

    # Create a valid report without a trusted hash
    report_path.write_text(
        '{"test": "report"}',
        encoding="utf-8",
    )

    response = test_environment["client"].get(
        f"/api/v1/sanitization/report/{verification_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["integrity_status"] == "UNVERIFIED"
    assert data["report_hash"] is not None
    assert data["expected_hash"] is None