import json
import hashlib
import uuid

from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "audit_logs"
CUSTODY_FILE = LOG_DIR / "custody_chain.jsonl"

GENESIS_HASH = "0" * 64


def calculate_event_hash(event):
    """
    Calculate SHA-256 hash of a custody event.
    """

    event_data = json.dumps(
        event,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        event_data.encode("utf-8")
    ).hexdigest()


def record_custody_event(
    audit_id,
    action,
    actor="SYSTEM",
    evidence_id=None,
    details=None,
):
    """
    Record an evidence custody event using a hash chain.
    """

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    previous_hash = GENESIS_HASH

    if CUSTODY_FILE.exists() and CUSTODY_FILE.stat().st_size > 0:

        with open(CUSTODY_FILE, "r", encoding="utf-8") as file:
            lines = file.readlines()

        if lines:
            last_event = json.loads(lines[-1])
            previous_hash = last_event["event_hash"]

    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "audit_id": audit_id,
        "evidence_id": evidence_id,
        "action": action,
        "actor": actor,
        "details": details or {},
        "previous_hash": previous_hash,
    }

    event["event_hash"] = calculate_event_hash(event)

    with open(CUSTODY_FILE, "a", encoding="utf-8") as file:
        file.write(json.dumps(event) + "\n")

    return event


def get_custody_events(audit_id=None):
    """
    Retrieve custody events.
    Optionally filter by audit ID.
    """

    if not CUSTODY_FILE.exists():
        return []

    events = []

    with open(CUSTODY_FILE, "r", encoding="utf-8") as file:

        for line in file:

            try:
                event = json.loads(line)

                if audit_id is None or event["audit_id"] == audit_id:
                    events.append(event)

            except json.JSONDecodeError:
                continue

    return events


def verify_custody_chain():
    """
    Verify the integrity and sequence of the custody hash chain.
    """

    if not CUSTODY_FILE.exists():
        return {
            "status": "EMPTY",
            "total_events": 0,
            "verified_events": 0,
            "tampered_events": 0,
            "message": "No custody events found.",
        }

    previous_hash = GENESIS_HASH
    total_events = 0
    verified_events = 0
    tampered_events = 0
    errors = []

    with open(CUSTODY_FILE, "r", encoding="utf-8") as file:

        for line_number, line in enumerate(file, start=1):

            total_events += 1

            try:
                event = json.loads(line)

            except json.JSONDecodeError:
                tampered_events += 1
                errors.append({
                    "line": line_number,
                    "error": "Invalid JSON record",
                })
                continue

            stored_hash = event.get("event_hash")

            event_without_hash = {
                key: value
                for key, value in event.items()
                if key != "event_hash"
            }

            calculated_hash = calculate_event_hash(
                event_without_hash
            )

            if event.get("previous_hash") != previous_hash:
                errors.append({
                    "line": line_number,
                    "error": "Previous hash mismatch",
                })

            if stored_hash != calculated_hash:
                errors.append({
                    "line": line_number,
                    "error": "Event hash mismatch",
                })

            if (
                event.get("previous_hash") == previous_hash
                and stored_hash == calculated_hash
            ):
                verified_events += 1

            else:
                tampered_events += 1

            # Continue using the stored hash to verify
            # the chain's subsequent links.
            previous_hash = stored_hash

    if tampered_events == 0 and total_events > 0:
        status = "CHAIN_VERIFIED"

    else:
        status = "CHAIN_INTEGRITY_FAILURE"

    return {
        "status": status,
        "total_events": total_events,
        "verified_events": verified_events,
        "tampered_events": tampered_events,
        "errors": errors,
    }