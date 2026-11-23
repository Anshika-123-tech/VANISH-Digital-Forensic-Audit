import json

import core.chain_of_custody as custody


def setup_custody_file(tmp_path, monkeypatch):
    log_dir = tmp_path / "audit_logs"
    custody_file = log_dir / "custody_chain.jsonl"

    monkeypatch.setattr(custody, "LOG_DIR", log_dir)
    monkeypatch.setattr(custody, "CUSTODY_FILE", custody_file)

    return custody_file


def test_empty_chain( tmp_path, monkeypatch):
    setup_custody_file(tmp_path, monkeypatch)

    result = custody.verify_custody_chain()

    assert result["status"] == "EMPTY"
    assert result["total_events"] == 0
    assert result["verified_events"] == 0
    assert result["tampered_events"] == 0


def test_valid_chain_verification(tmp_path, monkeypatch):
    setup_custody_file(tmp_path, monkeypatch)

    custody.record_custody_event(
        audit_id="audit-001",
        action="EVIDENCE_COLLECTED",
    )

    custody.record_custody_event(
        audit_id="audit-001",
        action="EVIDENCE_VERIFIED",
    )

    result = custody.verify_custody_chain()

    assert result["status"] == "CHAIN_VERIFIED"
    assert result["total_events"] == 2
    assert result["verified_events"] == 2
    assert result["tampered_events"] == 0
    assert result["errors"] == []


def test_event_tampering_detected(tmp_path, monkeypatch):
    custody_file = setup_custody_file(tmp_path, monkeypatch)

    custody.record_custody_event(
        audit_id="audit-002",
        action="EVIDENCE_COLLECTED",
    )

    events = [
        json.loads(line)
        for line in custody_file.read_text(
            encoding="utf-8"
        ).splitlines()
    ]

    # Modify the event without recalculating its hash.
    events[0]["action"] = "TAMPERED_ACTION"

    custody_file.write_text(
        json.dumps(events[0]) + "\n",
        encoding="utf-8",
    )

    result = custody.verify_custody_chain()

    assert result["status"] == "CHAIN_INTEGRITY_FAILURE"
    assert result["tampered_events"] == 1
    assert any(
        error["error"] == "Event hash mismatch"
        for error in result["errors"]
    )


def test_previous_hash_mismatch_detected(tmp_path, monkeypatch):
    custody_file = setup_custody_file(tmp_path, monkeypatch)

    custody.record_custody_event(
        audit_id="audit-003",
        action="FIRST_EVENT",
    )

    custody.record_custody_event(
        audit_id="audit-003",
        action="SECOND_EVENT",
    )

    events = [
        json.loads(line)
        for line in custody_file.read_text(
            encoding="utf-8"
        ).splitlines()
    ]

    # Change the second event's previous hash.
    events[1]["previous_hash"] = "f" * 64

    # Recalculate its event hash so we isolate
    # the previous-hash linkage check.
    events[1]["event_hash"] = custody.calculate_event_hash(
        {
            key: value
            for key, value in events[1].items()
            if key != "event_hash"
        }
    )

    custody_file.write_text(
        "".join(json.dumps(event) + "\n" for event in events),
        encoding="utf-8",
    )

    result = custody.verify_custody_chain()

    assert result["status"] == "CHAIN_INTEGRITY_FAILURE"
    assert result["tampered_events"] == 1
    assert any(
        error["error"] == "Previous hash mismatch"
        for error in result["errors"]
    )


def test_invalid_json_record_detected(tmp_path, monkeypatch):
    custody_file = setup_custody_file(tmp_path, monkeypatch)

    custody.record_custody_event(
        audit_id="audit-004",
        action="VALID_EVENT",
    )

    with open(custody_file, "a", encoding="utf-8") as file:
        file.write("{invalid json record}\n")

    result = custody.verify_custody_chain()

    assert result["status"] == "CHAIN_INTEGRITY_FAILURE"
    assert result["total_events"] == 2
    assert result["tampered_events"] == 1
    assert any(
        error["error"] == "Invalid JSON record"
        for error in result["errors"]
    )