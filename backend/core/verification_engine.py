from database.database_manager import get_evidence_by_audit
from core.hash_verifier import verify_file_hash
from core.audit_logger import log_event


def verify_audit(audit_id):
    """
    Perform integrity verification for all files
    belonging to a specific audit.
    """

    records = get_evidence_by_audit(audit_id)

    # Log verification start
    log_event(
        event="INTEGRITY_VERIFICATION_STARTED",
        audit_id=audit_id,
        status="STARTED",
        details={
            "records_found": len(records)
        },
    )

    if not records:
        log_event(
            event="INTEGRITY_VERIFICATION_FAILED",
            audit_id=audit_id,
            status="NOT_FOUND",
            details={
                "message": "No evidence records found for this audit."
            },
        )

        return {
            "audit_id": audit_id,
            "status": "not_found",
            "message": "No evidence records found for this audit.",
        }

    results = []

    # Verify each file
    for record in records:

        result = verify_file_hash(
            record["file_path"],
            record["sha256"],
        )

        result["file_name"] = record["file_name"]
        result["relative_path"] = record["relative_path"]

        results.append(result)

    # Count verification results
    intact = sum(
        1 for result in results
        if result["status"] == "intact"
    )

    modified = sum(
        1 for result in results
        if result["status"] == "modified"
    )

    missing = sum(
        1 for result in results
        if result["status"] == "missing"
    )

    invalid = sum(
        1 for result in results
        if result["status"] == "invalid_file"
    )

    # Determine overall integrity status
    if modified > 0 or missing > 0 or invalid > 0:
        overall_status = "INTEGRITY_FAILURE"
    else:
        overall_status = "INTEGRITY_VERIFIED"

    # Log verification completion
    log_event(
        event="INTEGRITY_VERIFICATION_COMPLETED",
        audit_id=audit_id,
        status=overall_status,
        details={
            "total_files": len(results),
            "intact": intact,
            "modified": modified,
            "missing": missing,
            "invalid": invalid,
        },
    )

    return {
        "audit_id": audit_id,
        "total_files": len(results),
        "intact": intact,
        "modified": modified,
        "missing": missing,
        "invalid": invalid,
        "overall_status": overall_status,
        "results": results,
    }