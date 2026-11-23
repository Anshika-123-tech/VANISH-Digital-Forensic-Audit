import json
import hashlib 
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

REPORT_DIR = BASE_DIR / "reports" / "sanitization"


def generate_sanitization_report(verification_result):

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    verification_id = verification_result["verification_id"]

    report = {
        "report_type": "SANITIZATION_VERIFICATION_REPORT",
        "report_id": verification_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),

        "verification": {
            "verification_id": verification_id,
            "target_path": verification_result["target_path"],
            "sanitization_method": verification_result[
                "sanitization_method"
            ],
            "storage_type": verification_result["storage_type"],
            "verification_time": verification_result[
                "verification_time"
            ],
            "status": verification_result["status"],
        },

        "checks": verification_result["checks"],

        "findings": verification_result["findings"],

        "limitations": verification_result["limitations"],

        "conclusion": (
            "Sanitization verification completed. "
            "Review the checks, findings, and limitations "
            "before drawing forensic conclusions."
        ),
    }

    report_path = REPORT_DIR / f"{verification_id}.json"

    with open(report_path, "w", encoding="utf-8") as report_file:

        json.dump(
            report,
            report_file,
            indent=4,
            ensure_ascii=False,
        )
            # Calculate SHA-256 hash of the generated report
    sha256_hash = hashlib.sha256()

    with open(report_path, "rb") as report_file:

        for chunk in iter(
            lambda: report_file.read(4096),
            b"",
        ):

            sha256_hash.update(chunk)

    report_hash = sha256_hash.hexdigest()

    return {
        "report_id": verification_id,
        "report_status": "GENERATED",
        "report_path": str(report_path),
        "hash_algorithm": "SHA-256",
        "report_hash": report_hash,
        "report": report,
    }