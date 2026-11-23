"""
VANISH Forensic Analysis Engine

Provides rules-based analysis of digital evidence integrity
verification results.

This module does not replace cryptographic verification.
It interprets verification results and generates risk
assessments, findings, and recommendations.
"""


def analyze_evidence(verification_result):
    """
    Analyze an integrity verification result.

    Args:
        verification_result (dict):
            Output produced by verify_audit().

    Returns:
        dict:
            Structured forensic analysis.
    """

    if not isinstance(verification_result, dict):
        raise TypeError("verification_result must be a dictionary")

    if verification_result.get("status") == "not_found":
        return {
            "analysis_status": "NOT_ANALYZED",
            "risk_level": "UNKNOWN",
            "risk_score": 0,
            "findings": [],
            "recommendations": [
                "Verify the audit ID and ensure evidence records exist."
            ],
            "summary": "No evidence records were available for analysis.",
        }

    results = verification_result.get("results", [])

    if not isinstance(results, list):
        raise ValueError("Verification results must be a list")

    total_files = verification_result.get(
        "total_files", len(results)
    )

    modified = verification_result.get("modified", 0)
    missing = verification_result.get("missing", 0)
    invalid = verification_result.get("invalid", 0)
    intact = verification_result.get("intact", 0)

    findings = []
    recommendations = []

    # Modified evidence
    if modified > 0:
        findings.append({
            "finding_id": "MODIFIED_EVIDENCE",
            "severity": "HIGH",
            "count": modified,
            "description": (
                "One or more evidence files have hashes "
                "that differ from their originally recorded "
                "SHA-256 hashes."
            ),
        })

        recommendations.append(
            "Investigate modified files and compare their "
            "recorded and current SHA-256 hashes."
        )

    # Missing evidence
    if missing > 0:
        findings.append({
            "finding_id": "MISSING_EVIDENCE",
            "severity": "HIGH",
            "count": missing,
            "description": (
                "One or more previously recorded evidence "
                "files could not be located."
            ),
        })

        recommendations.append(
            "Investigate missing files, storage locations, "
            "and evidence handling records."
        )

    # Invalid evidence
    if invalid > 0:
        findings.append({
            "finding_id": "INVALID_EVIDENCE",
            "severity": "HIGH",
            "count": invalid,
            "description": (
                "One or more evidence paths do not point "
                "to valid regular files."
            ),
        })

        recommendations.append(
            "Review invalid evidence paths and verify "
            "the corresponding evidence records."
        )

    # Individual file analysis
    file_findings = []

    for result in results:

        if not isinstance(result, dict):
            continue

        file_status = result.get("status")

        if file_status in ("modified", "missing", "invalid_file"):

            file_findings.append({
                "file_name": result.get(
                    "file_name", "Unknown"
                ),
                "relative_path": result.get(
                    "relative_path", "Unknown"
                ),
                "status": file_status,
                "expected_hash": result.get(
                    "expected_hash"
                ),
                "actual_hash": result.get(
                    "actual_hash"
                ),
            })

    # Calculate risk score
    if modified > 0 or missing > 0 or invalid > 0:
        risk_score = 100
        risk_level = "HIGH"

    elif total_files == 0:
        risk_score = 0
        risk_level = "UNKNOWN"

    else:
        risk_score = 0
        risk_level = "LOW"

    # Summary
    if risk_level == "HIGH":
        summary = (
            "Integrity anomalies were detected. "
            "Further forensic investigation is recommended."
        )

    elif risk_level == "LOW":
        summary = (
            "All recorded evidence files passed "
            "the integrity verification."
        )

    else:
        summary = (
            "Integrity risk could not be determined "
            "from the available evidence."
        )

    # General recommendation
    if not recommendations:
        recommendations.append(
            "Maintain secure evidence storage and "
            "periodically perform integrity verification."
        )

    return {
        "analysis_status": "COMPLETED",
        "analysis_type": "RULES_BASED_FORENSIC_ANALYSIS",
        "risk_level": risk_level,
        "risk_score": risk_score,
        "summary": summary,
        "statistics": {
            "total_files": total_files,
            "intact": intact,
            "modified": modified,
            "missing": missing,
            "invalid": invalid,
        },
        "findings": findings,
        "file_findings": file_findings,
        "recommendations": recommendations,
    }