from contextlib import asynccontextmanager
import hashlib
import json
import uuid
from uuid import UUID
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from core.audit_logger import log_event, get_audit_logs
from core.evidence_collector import collect_evidence
from core.verification_engine import verify_audit
from core.report_generator import generate_report
from core.ai_analyzer import analyze_evidence
from core.cloud_analyzer import analyze_cloud_evidence
from core.sanitization_verifier import verify_sanitization
from core.sanitization_report_generator import (
    generate_sanitization_report,
)
from core.chain_of_custody import (
    record_custody_event,
    get_custody_events,
    verify_custody_chain,
)

from database.database_manager import (
    initialize_database,
    save_evidence,
    get_all_evidence,
    get_evidence_by_audit,
)


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "evidence" / "uploads"

MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB


# --------------------------------------------------
# APPLICATION LIFECYCLE
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    initialize_database()

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    print("VANISH database initialized.")
    print("VANISH upload directory initialized.")

    yield


app = FastAPI(
    title="VANISH API",
    description="Digital Erasure Forensic Audit Framework",
    version="1.0.0",
    lifespan=lifespan,
)


# --------------------------------------------------
# CORS CONFIGURATION
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# HOME AND HEALTH
# --------------------------------------------------

@app.get("/")
def home():

    return {
        "project": "VANISH",
        "description": "Digital Erasure Forensic Audit Framework",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "database": "connected",
    }


# --------------------------------------------------
# EVIDENCE COLLECTION
# --------------------------------------------------

@app.post("/api/v1/evidence/scan")
def scan_evidence():

    try:

        result = collect_evidence("evidence/test_files")

        saved_count = save_evidence(result["records"])

        log_event(
            event="EVIDENCE_SCAN_COMPLETED",
            audit_id=result["audit_id"],
            status="SUCCESS",
            details={
                "files_scanned": result["files_scanned"],
                "records_saved": saved_count,
                "errors": result["errors"],
            },
        )

        for record in result["records"]:

            record_custody_event(
                audit_id=result["audit_id"],
                action="EVIDENCE_COLLECTED",
                actor="VANISH_SYSTEM",
                evidence_id=record.get("id"),
                details={
                    "file_name": record.get(
                        "file_name",
                        record.get("filename", "unknown"),
                    ),
                    "file_hash": record.get(
                        "sha256",
                        record.get(
                            "file_hash",
                            record.get("hash"),
                        ),
                    ),
                    "description": "Evidence collected by VANISH",
                },
            )

        return {
            "message": "Evidence scan completed",
            "audit_id": result["audit_id"],
            "files_scanned": result["files_scanned"],
            "records_saved": saved_count,
            "errors": result["errors"],
            "records": result["records"],
        }

    except Exception as error:

        log_event(
            event="EVIDENCE_SCAN_FAILED",
            status="ERROR",
            details={
                "error": str(error),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# --------------------------------------------------
# DIRECT FILE UPLOAD
# --------------------------------------------------

@app.post("/api/v1/evidence/upload")
async def upload_evidence(file: UploadFile = File(...)):

    audit_id = str(uuid.uuid4())

    original_filename = file.filename or "uploaded_file"

    # Prevent directory traversal through filenames
    original_filename = (
        original_filename.replace("\\", "/").split("/")[-1]
    )

    if not original_filename:
        original_filename = "uploaded_file"

    file_extension = Path(original_filename).suffix.lower()

    # Generate unique stored filename
    stored_filename = (
        f"{uuid.uuid4().hex}_{original_filename}"
    )

    saved_path = UPLOAD_DIR / stored_filename

    sha256_hash = hashlib.sha256()

    file_size = 0

    database_saved = False

    try:

        # Save uploaded file and calculate SHA-256
        with open(saved_path, "wb") as output_file:

            while True:

                chunk = await file.read(1024 * 1024)

                if not chunk:
                    break

                file_size += len(chunk)

                # Maximum upload size: 100 MB
                if file_size > MAX_UPLOAD_SIZE:

                    output_file.close()

                    saved_path.unlink(missing_ok=True)

                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "File exceeds the maximum "
                            "upload size of 100 MB"
                        ),
                    )

                sha256_hash.update(chunk)

                output_file.write(chunk)

        await file.close()

        file_hash = sha256_hash.hexdigest()

        collection_time = datetime.now(
            timezone.utc
        ).isoformat()

        # Create evidence database record
        record = {
            "audit_id": audit_id,
            "source_directory": "direct_upload",
            "file_path": str(saved_path.resolve()),
            "relative_path": str(
                saved_path.relative_to(BASE_DIR)
            ),
            "file_name": original_filename,
            "extension": file_extension,
            "file_size": file_size,
            "created_time": collection_time,
            "modified_time": collection_time,
            "sha256": file_hash,
            "collection_time": collection_time,
            "status": "COLLECTED",
        }

        # Save evidence into database
        saved_count = save_evidence([record])

        database_saved = saved_count > 0

        # Retrieve saved evidence ID
        saved_records = get_evidence_by_audit(audit_id)

        evidence_id = (
            saved_records[0]["id"]
            if saved_records
            else None
        )

        # Record audit log
        log_event(
            event="EVIDENCE_UPLOAD_COMPLETED",
            audit_id=audit_id,
            status="SUCCESS",
            details={
                "file_name": original_filename,
                "file_size": file_size,
                "sha256": file_hash,
            },
        )

        # Record custody event
        custody_status = "RECORDED"

        try:

            record_custody_event(
                audit_id=audit_id,
                action="EVIDENCE_COLLECTED",
                actor="VANISH_SYSTEM",
                evidence_id=evidence_id,
                details={
                    "file_name": original_filename,
                    "file_size": file_size,
                    "sha256": file_hash,
                    "source": "DIRECT_UPLOAD",
                },
            )

        except Exception as custody_error:

            custody_status = "FAILED"

            log_event(
                event="CUSTODY_RECORDING_FAILED",
                audit_id=audit_id,
                status="ERROR",
                details={
                    "error": str(custody_error),
                },
            )

        return {
            "message": (
                "File uploaded and evidence collected successfully"
            ),
            "audit_id": audit_id,
            "evidence_id": evidence_id,
            "file_name": original_filename,
            "file_size": file_size,
            "sha256": file_hash,
            "status": "COLLECTED",
            "database_records_saved": saved_count,
            "custody_status": custody_status,
            "storage_path": str(saved_path),
        }

    except HTTPException:
        raise

    except Exception as error:

        # Remove uploaded file if database save failed
        if saved_path.exists() and not database_saved:

            saved_path.unlink(missing_ok=True)

        log_event(
            event="EVIDENCE_UPLOAD_FAILED",
            audit_id=audit_id,
            status="ERROR",
            details={
                "file_name": original_filename,
                "error": str(error),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    finally:

        await file.close()


# --------------------------------------------------
# EVIDENCE MANAGEMENT
# --------------------------------------------------

@app.get("/api/v1/evidence")
def list_evidence():

    return get_all_evidence()


@app.get("/api/v1/evidence/audit/{audit_id}")
def get_audit_records(audit_id: str):

    records = get_evidence_by_audit(audit_id)

    if not records:

        raise HTTPException(
            status_code=404,
            detail="Audit ID not found",
        )

    return {
        "audit_id": audit_id,
        "total_records": len(records),
        "records": records,
    }


# --------------------------------------------------
# INTEGRITY VERIFICATION
# --------------------------------------------------

@app.get("/api/v1/evidence/verify/{audit_id}")
def verify_audit_integrity(audit_id: str):

    result = verify_audit(audit_id)

    if result.get("status") == "not_found":

        raise HTTPException(
            status_code=404,
            detail=result["message"],
        )

    result["forensic_analysis"] = analyze_evidence(result)

    verification_status = result.get("overall_status")

    custody_action = (
        "INTEGRITY_VERIFIED"
        if verification_status == "INTEGRITY_VERIFIED"
        else "INTEGRITY_FAILURE"
    )

    record_custody_event(
        audit_id=audit_id,
        action=custody_action,
        actor="VANISH_SYSTEM",
        details={
            "verification_status": verification_status,
            "verification_result": result,
        },
    )

    return result


# --------------------------------------------------
# EVIDENCE REPORT GENERATION
# --------------------------------------------------

@app.get("/api/v1/evidence/report/{audit_id}")
def generate_audit_report(audit_id: str):

    verification = verify_audit(audit_id)

    if verification.get("status") == "not_found":

        raise HTTPException(
            status_code=404,
            detail=verification["message"],
        )

    result = generate_report(verification)

    record_custody_event(
        audit_id=audit_id,
        action="REPORT_GENERATED",
        actor="VANISH_SYSTEM",
        details={
            "report_status": result["status"],
            "report_path": result["report_path"],
        },
    )

    return {
        "message": "Forensic report generated successfully",
        "audit_id": audit_id,
        "report_status": result["status"],
        "report_path": result["report_path"],
        "report": result["report"],
    }


# --------------------------------------------------
# AUDIT LOGS
# --------------------------------------------------

@app.get("/api/v1/audit/logs")
def retrieve_audit_logs():

    logs = get_audit_logs()

    return {
        "total_logs": len(logs),
        "logs": logs,
    }


# --------------------------------------------------
# CHAIN OF CUSTODY
# --------------------------------------------------

@app.get("/api/v1/custody/events")
def retrieve_all_custody_events():

    events = get_custody_events()

    return {
        "total_events": len(events),
        "events": events,
    }


@app.get("/api/v1/custody/events/{audit_id}")
def retrieve_custody_events_by_audit(audit_id: str):

    events = get_custody_events(audit_id)

    return {
        "audit_id": audit_id,
        "total_events": len(events),
        "events": events,
    }


# --------------------------------------------------
# CHAIN INTEGRITY VERIFICATION
# --------------------------------------------------

@app.get("/api/v1/custody/chain/verify")
def verify_custody_integrity():

    return verify_custody_chain()


# --------------------------------------------------
# SANITIZATION VERIFICATION
# --------------------------------------------------

@app.post("/api/v1/sanitization/verify")
def sanitization_verification(
    target_path: str,
    sanitization_method: str = "unknown",
    storage_type: str = "filesystem",
    residual_marker: str = None,
):

    # Restrict verification to test evidence directory
    allowed_directory = (
        BASE_DIR / "evidence" / "test_files"
    ).resolve()

    target = Path(target_path).resolve()

    # Prevent access outside the test directory
    if not target.is_relative_to(allowed_directory):
        raise HTTPException(
            status_code=403,
            detail="Access restricted to the test evidence directory",
        )

    # Perform sanitization verification
    result = verify_sanitization(
        target_path=str(target),
        sanitization_method=sanitization_method,
        storage_type=storage_type,
        residual_marker=residual_marker,
    )

    verification_id = result["verification_id"]

    # Record verification audit log
    log_event(
        event="SANITIZATION_VERIFICATION_COMPLETED",
        status=result["status"],
        details=result,
    )

    # Record verification custody event
    record_custody_event(
        audit_id=verification_id,
        action="SANITIZATION_VERIFICATION_COMPLETED",
        actor="VANISH_SYSTEM",
        details={
            "target_path": result["target_path"],
            "sanitization_method": result["sanitization_method"],
            "storage_type": result["storage_type"],
            "verification_status": result["status"],
            "checks": result["checks"],
            "findings": result["findings"],
        },
    )

    # Generate sanitization verification report
    try:

        report_result = generate_sanitization_report(result)

        result["report_generation"] = {
            "report_status": report_result["report_status"],
            "report_path": report_result["report_path"],
            "report_hash": report_result["report_hash"],
            "hash_algorithm": report_result["hash_algorithm"],
            "custody_status": "PENDING",
        }

        # Log report generation
        log_event(
            event="SANITIZATION_REPORT_GENERATED",
            status="SUCCESS",
            details={
                "verification_id": verification_id,
                "report_path": report_result["report_path"],
                "report_hash": report_result["report_hash"],
                "hash_algorithm": report_result["hash_algorithm"],
            },
        )

        # Record trusted report hash in custody chain
        try:

            record_custody_event(
                audit_id=verification_id,
                action="SANITIZATION_REPORT_GENERATED",
                actor="VANISH_SYSTEM",
                details={
                    "verification_id": verification_id,
                    "report_path": report_result["report_path"],
                    "report_hash": report_result["report_hash"],
                    "hash_algorithm": report_result["hash_algorithm"],
                    "report_status": report_result["report_status"],
                },
            )

            result["report_generation"]["custody_status"] = "RECORDED"

        except Exception as custody_error:

            result["report_generation"]["custody_status"] = "FAILED"

            log_event(
                event="SANITIZATION_REPORT_CUSTODY_FAILED",
                status="ERROR",
                details={
                    "verification_id": verification_id,
                    "error": str(custody_error),
                },
            )

    except Exception as error:

        result["report_generation"] = {
            "report_status": "FAILED",
            "error": str(error),
        }

        log_event(
            event="SANITIZATION_REPORT_GENERATION_FAILED",
            status="FAILED",
            details={
                "verification_id": verification_id,
                "error": str(error),
            },
        )

    return result


# --------------------------------------------------
# SANITIZATION REPORT RETRIEVAL AND INTEGRITY VERIFICATION
# --------------------------------------------------

@app.get("/api/v1/sanitization/report/{verification_id}")
def retrieve_sanitization_report(verification_id: str):

    # Validate verification ID
    try:

        valid_id = str(UUID(verification_id))

    except ValueError:

        raise HTTPException(
            status_code=400,
            detail="Invalid verification ID format",
        )

    # Locate report directory
    report_directory = (
        BASE_DIR / "reports" / "sanitization"
    ).resolve()

    report_path = (
        report_directory / f"{valid_id}.json"
    ).resolve()

    # Security check
    if not report_path.is_relative_to(report_directory):

        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    # Check report existence
    if not report_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Sanitization report not found",
        )

    # Read raw report bytes and calculate hash FIRST
    try:

        with open(report_path, "rb") as report_file:
            report_bytes = report_file.read()

        actual_hash = hashlib.sha256(
            report_bytes
        ).hexdigest()

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to read report: {str(error)}",
        )

    # Retrieve custody events
    custody_events = get_custody_events(valid_id)

    if isinstance(custody_events, dict):
        custody_events = custody_events.get("events", [])

    # Find trusted report hash
    expected_hash = None

    for event in custody_events:

        if event.get("action") == "SANITIZATION_REPORT_GENERATED":

            event_details = event.get("details", {})

            if isinstance(event_details, str):

                try:
                    event_details = json.loads(event_details)

                except json.JSONDecodeError:
                    continue

            if isinstance(event_details, dict):

                stored_hash = event_details.get(
                    "report_hash"
                )

                if stored_hash:
                    expected_hash = stored_hash

    # Determine integrity status
    if expected_hash is None:

        integrity_status = "UNVERIFIED"

    elif actual_hash == expected_hash:

        integrity_status = "VERIFIED"

    else:

        integrity_status = "TAMPERED"

        # Record integrity failure in audit log
        log_event(
            event="SANITIZATION_REPORT_INTEGRITY_FAILURE",
            status="FAILED",
            details={
                "verification_id": valid_id,
                "report_path": str(report_path),
                "expected_hash": expected_hash,
                "actual_hash": actual_hash,
                "hash_algorithm": "SHA-256",
                "integrity_status": integrity_status,
            },
        )

        # Record integrity failure in custody chain
        try:

            record_custody_event(
                audit_id=valid_id,
                action="SANITIZATION_REPORT_INTEGRITY_FAILURE",
                actor="VANISH_SYSTEM",
                details={
                    "verification_id": valid_id,
                    "report_path": str(report_path),
                    "expected_hash": expected_hash,
                    "actual_hash": actual_hash,
                    "hash_algorithm": "SHA-256",
                    "integrity_status": integrity_status,
                },
            )

        except Exception as custody_error:

            log_event(
                event="INTEGRITY_FAILURE_CUSTODY_RECORD_FAILED",
                status="ERROR",
                details={
                    "verification_id": valid_id,
                    "error": str(custody_error),
                },
            )

        # Reject tampered report
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Report integrity verification failed",
                "verification_id": valid_id,
                "integrity_status": integrity_status,
                "expected_hash": expected_hash,
                "actual_hash": actual_hash,
                "hash_algorithm": "SHA-256",
            },
        )

    # Parse JSON only AFTER integrity verification
    try:

        report = json.loads(
            report_bytes.decode("utf-8")
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Report JSON parsing failed: {str(error)}",
        )

    # Record successful report access
    access_time = datetime.now(
        timezone.utc
    ).isoformat()

    log_event(
        event="SANITIZATION_REPORT_ACCESSED",
        status="SUCCESS",
        details={
            "verification_id": valid_id,
            "report_path": str(report_path),
            "access_time": access_time,
            "report_hash": actual_hash,
            "integrity_status": integrity_status,
        },
    )

    # Record successful access in custody chain
    record_custody_event(
        audit_id=valid_id,
        action="SANITIZATION_REPORT_ACCESSED",
        actor="VANISH_SYSTEM",
        details={
            "verification_id": valid_id,
            "report_path": str(report_path),
            "access_time": access_time,
            "report_hash": actual_hash,
            "integrity_status": integrity_status,
        },
    )

    # Return verified report
    return {
        "message": "Sanitization report retrieved successfully",
        "verification_id": valid_id,
        "integrity_status": integrity_status,
        "report_hash": actual_hash,
        "expected_hash": expected_hash,
        "hash_algorithm": "SHA-256",
        "report": report,
    }


# --------------------------------------------------
# CLOUD DELETION VERIFICATION
# --------------------------------------------------

@app.post("/api/v1/cloud/verify")
def cloud_deletion_verification(cloud_evidence: dict):

    verification_id = str(uuid.uuid4())

    # Analyze supplied cloud evidence
    try:

        result = analyze_cloud_evidence(cloud_evidence)

    except (TypeError, ValueError) as error:

        raise HTTPException(
            status_code=422,
            detail=str(error),
        )

    # Add verification ID
    result["verification_id"] = verification_id

    # Record audit log
    log_event(
        event="CLOUD_DELETION_VERIFICATION_COMPLETED",
        audit_id=verification_id,
        status=result["verification_status"],
        details=result,
    )

    # Record chain of custody event
    record_custody_event(
        audit_id=verification_id,
        action="CLOUD_DELETION_VERIFICATION_COMPLETED",
        actor="VANISH_SYSTEM",
        details={
            "verification_status": result["verification_status"],
            "risk_level": result["risk_level"],
            "cloud_analysis": result,
        },
    )

    return result