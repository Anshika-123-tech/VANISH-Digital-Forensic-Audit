import json
from datetime import datetime, timezone
from pathlib import Path

from core.ai_analyzer import analyze_evidence


BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "reports"


def generate_report(verification_result):
    """
    Generate and save a forensic verification report
    containing integrity verification and forensic analysis.
    """

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Perform rules-based forensic analysis
    forensic_analysis = analyze_evidence(
        verification_result
    )

    report = {
        "report_id": (
            f"VANISH-{verification_result['audit_id']}"
        ),
        "project": "VANISH",
        "report_type": "Digital Integrity Verification Report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "audit_id": verification_result["audit_id"],

        "summary": {
            "total_files": verification_result["total_files"],
            "intact": verification_result["intact"],
            "modified": verification_result["modified"],
            "missing": verification_result["missing"],
            "invalid": verification_result["invalid"],
            "overall_status": verification_result["overall_status"],
        },

        "file_results": verification_result["results"],

        # New forensic analysis section
        "forensic_analysis": forensic_analysis,
    }

    report_path = (
        REPORT_DIR
        / f"{verification_result['audit_id']}_report.json"
    )

    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    return {
        "report": report,
        "report_path": str(report_path),
        "status": "generated",
    }