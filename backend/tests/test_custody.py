from core.chain_of_custody import (
    record_custody_event,
    get_custody_events,
    verify_custody_chain,
)


TEST_AUDIT_ID = "VANISH-CUSTODY-TEST-001"


# 1. Record evidence collection
event1 = record_custody_event(
    audit_id=TEST_AUDIT_ID,
    action="EVIDENCE_COLLECTED",
    actor="VANISH_SYSTEM",
    details={
        "file_name": "tampered_document.txt",
        "description": "Synthetic test evidence collected",
    },
)


# 2. Record evidence verification
event2 = record_custody_event(
    audit_id=TEST_AUDIT_ID,
    action="INTEGRITY_VERIFIED",
    actor="VANISH_SYSTEM",
    details={
        "method": "SHA-256",
    },
)


# 3. Record report generation
event3 = record_custody_event(
    audit_id=TEST_AUDIT_ID,
    action="REPORT_GENERATED",
    actor="VANISH_SYSTEM",
    details={
        "report_type": "JSON",
    },
)


# 4. Retrieve events
events = get_custody_events(TEST_AUDIT_ID)

print("\n--- CUSTODY EVENTS ---")

for event in events:
    print(
        event["action"],
        "|",
        event["event_hash"],
    )


# 5. Verify chain integrity
verification = verify_custody_chain()

print("\n--- CHAIN VERIFICATION ---")
print(verification)