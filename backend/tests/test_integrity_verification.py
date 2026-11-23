import hashlib

import pytest

import core.hash_verifier as hash_verifier
import core.verification_engine as verification_engine


@pytest.fixture
def verification_environment(tmp_path, monkeypatch):

    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()

    # Mock evidence database
    records = []

    def fake_get_evidence_by_audit(audit_id):
        return records

    monkeypatch.setattr(
        verification_engine,
        "get_evidence_by_audit",
        fake_get_evidence_by_audit,
    )

    # Mock audit logger
    audit_events = []

    def fake_log_event(**kwargs):
        audit_events.append(kwargs)

    monkeypatch.setattr(
        verification_engine,
        "log_event",
        fake_log_event,
    )

    return {
        "evidence_dir": evidence_dir,
        "records": records,
        "audit_events": audit_events,
    }


def create_record(file_path):

    content_hash = hashlib.sha256(
        file_path.read_bytes()
    ).hexdigest()

    return {
        "file_path": str(file_path),
        "file_name": file_path.name,
        "relative_path": file_path.name,
        "sha256": content_hash,
    }


def test_intact_file_verification(
    verification_environment,
):

    evidence_dir = verification_environment["evidence_dir"]

    file_path = evidence_dir / "intact.txt"
    file_path.write_text("Original evidence", encoding="utf-8")

    verification_environment["records"].append(
        create_record(file_path)
    )

    result = verification_engine.verify_audit("audit-001")

    assert result["overall_status"] == "INTEGRITY_VERIFIED"
    assert result["total_files"] == 1
    assert result["intact"] == 1
    assert result["modified"] == 0
    assert result["missing"] == 0
    assert result["invalid"] == 0

    assert result["results"][0]["status"] == "intact"
    assert result["results"][0]["integrity_verified"] is True


def test_modified_file_detection(
    verification_environment,
):

    evidence_dir = verification_environment["evidence_dir"]

    file_path = evidence_dir / "modified.txt"
    file_path.write_text("Original content", encoding="utf-8")

    record = create_record(file_path)

    # Change the file after recording its hash
    file_path.write_text("Tampered content", encoding="utf-8")

    verification_environment["records"].append(record)

    result = verification_engine.verify_audit("audit-002")

    assert result["overall_status"] == "INTEGRITY_FAILURE"
    assert result["modified"] == 1
    assert result["intact"] == 0

    assert result["results"][0]["status"] == "modified"
    assert result["results"][0]["integrity_verified"] is False


def test_missing_file_detection(
    verification_environment,
):

    evidence_dir = verification_environment["evidence_dir"]

    file_path = evidence_dir / "missing.txt"
    file_path.write_text("Evidence content", encoding="utf-8")

    record = create_record(file_path)

    # Delete the file
    file_path.unlink()

    verification_environment["records"].append(record)

    result = verification_engine.verify_audit("audit-003")

    assert result["overall_status"] == "INTEGRITY_FAILURE"
    assert result["missing"] == 1

    assert result["results"][0]["status"] == "missing"
    assert result["results"][0]["actual_hash"] is None


def test_invalid_file_detection(
    verification_environment,
):

    evidence_dir = verification_environment["evidence_dir"]

    directory_path = evidence_dir / "directory_evidence"
    directory_path.mkdir()

    verification_environment["records"].append({
        "file_path": str(directory_path),
        "file_name": "directory_evidence",
        "relative_path": "directory_evidence",
        "sha256": "fake_hash",
    })

    result = verification_engine.verify_audit("audit-004")

    assert result["overall_status"] == "INTEGRITY_FAILURE"
    assert result["invalid"] == 1

    assert result["results"][0]["status"] == "invalid_file"


def test_no_evidence_records(
    verification_environment,
):

    result = verification_engine.verify_audit("audit-005")

    assert result["status"] == "not_found"

    assert (
        result["message"]
        == "No evidence records found for this audit."
    )

    events = verification_environment["audit_events"]

    assert any(
        event["event"] == "INTEGRITY_VERIFICATION_FAILED"
        for event in events
    )


def test_multiple_files_mixed_integrity(
    verification_environment,
):

    evidence_dir = verification_environment["evidence_dir"]

    intact_file = evidence_dir / "intact.txt"
    modified_file = evidence_dir / "modified.txt"
    missing_file = evidence_dir / "missing.txt"

    intact_file.write_text("Intact", encoding="utf-8")
    modified_file.write_text("Original", encoding="utf-8")
    missing_file.write_text("Will be deleted", encoding="utf-8")

    intact_record = create_record(intact_file)
    modified_record = create_record(modified_file)
    missing_record = create_record(missing_file)

    modified_file.write_text("Changed", encoding="utf-8")
    missing_file.unlink()

    verification_environment["records"].extend([
        intact_record,
        modified_record,
        missing_record,
    ])

    result = verification_engine.verify_audit("audit-006")

    assert result["total_files"] == 3
    assert result["intact"] == 1
    assert result["modified"] == 1
    assert result["missing"] == 1
    assert result["invalid"] == 0

    assert result["overall_status"] == "INTEGRITY_FAILURE"


def test_verification_completion_is_logged(
    verification_environment,
):

    evidence_dir = verification_environment["evidence_dir"]

    file_path = evidence_dir / "logged.txt"
    file_path.write_text("Audit logging test", encoding="utf-8")

    verification_environment["records"].append(
        create_record(file_path)
    )

    verification_engine.verify_audit("audit-007")

    events = verification_environment["audit_events"]

    assert any(
        event["event"] == "INTEGRITY_VERIFICATION_STARTED"
        for event in events
    )

    assert any(
        event["event"] == "INTEGRITY_VERIFICATION_COMPLETED"
        and event["status"] == "INTEGRITY_VERIFIED"
        for event in events
    )