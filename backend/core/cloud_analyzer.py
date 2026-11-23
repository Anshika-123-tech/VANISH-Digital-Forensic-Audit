"""
VANISH Cloud Evidence Analyzer

Analyzes cloud data deletion evidence using deterministic rules.

This module does not directly connect to cloud providers.
It evaluates supplied evidence metadata and identifies
deletion status, residual objects, retained versions,
backups, retention policies, and evidence limitations.
"""


def analyze_cloud_evidence(cloud_evidence):
    """
    Analyze cloud deletion evidence.

    Args:
        cloud_evidence (dict):
            Provider-independent cloud evidence metadata.

    Returns:
        dict:
            Structured cloud forensic analysis.
    """

    if not isinstance(cloud_evidence, dict):
        raise TypeError("cloud_evidence must be a dictionary")

    required_fields = [
        "deletion_confirmed",
        "residual_objects",
        "retained_versions",
        "backup_copies",
        "retention_active",
        "locations_checked",
        "evidence_complete",
    ]

    missing_fields = [
        field for field in required_fields
        if field not in cloud_evidence
    ]

    if missing_fields:
        return {
            "analysis_status": "INCOMPLETE",
            "verification_status": "INCONCLUSIVE",
            "risk_level": "UNKNOWN",
            "findings": [],
            "recommendations": [
                "Collect the missing cloud evidence fields "
                "before performing verification."
            ],
            "missing_fields": missing_fields,
            "summary": (
                "Cloud deletion verification could not be "
                "completed because required evidence is missing."
            ),
        }

    residual_objects = cloud_evidence["residual_objects"]
    retained_versions = cloud_evidence["retained_versions"]
    backup_copies = cloud_evidence["backup_copies"]
    locations_checked = cloud_evidence["locations_checked"]

    if not isinstance(residual_objects, list):
        raise ValueError("residual_objects must be a list")

    if not isinstance(retained_versions, list):
        raise ValueError("retained_versions must be a list")

    if not isinstance(backup_copies, list):
        raise ValueError("backup_copies must be a list")

    if not isinstance(locations_checked, list):
        raise ValueError("locations_checked must be a list")

    findings = []
    recommendations = []

    deletion_confirmed = cloud_evidence["deletion_confirmed"]
    retention_active = cloud_evidence["retention_active"]
    evidence_complete = cloud_evidence["evidence_complete"]

    # Deletion confirmation
    if deletion_confirmed is False:

        findings.append({
            "finding_id": "DELETION_NOT_CONFIRMED",
            "severity": "HIGH",
            "description": (
                "The supplied evidence does not confirm "
                "successful deletion of the target data."
            ),
        })

        recommendations.append(
            "Obtain deletion operation records or provider "
            "confirmation and investigate the deletion status."
        )

    # Residual objects
    if residual_objects:

        findings.append({
            "finding_id": "RESIDUAL_OBJECTS_DETECTED",
            "severity": "HIGH",
            "count": len(residual_objects),
            "description": (
                "Residual objects were identified in the "
                "cloud storage locations examined."
            ),
        })

        recommendations.append(
            "Investigate and verify the disposition of "
            "identified residual objects."
        )

    # Retained versions
    if retained_versions:

        findings.append({
            "finding_id": "RETAINED_VERSIONS_DETECTED",
            "severity": "HIGH",
            "count": len(retained_versions),
            "description": (
                "Previous versions of the target data "
                "were identified in the supplied evidence."
            ),
        })

        recommendations.append(
            "Review retained versions and determine whether "
            "they fall within the requested deletion scope."
        )

    # Backup copies
    if backup_copies:

        findings.append({
            "finding_id": "BACKUP_COPIES_DETECTED",
            "severity": "MEDIUM",
            "count": len(backup_copies),
            "description": (
                "Backup copies were identified or reported "
                "in the supplied cloud evidence."
            ),
        })

        recommendations.append(
            "Review backup retention schedules and determine "
            "whether backup copies are subject to deletion."
        )

    # Retention policy
    if retention_active:

        findings.append({
            "finding_id": "RETENTION_POLICY_ACTIVE",
            "severity": "MEDIUM",
            "description": (
                "A retention policy, legal hold, or similar "
                "preservation mechanism may prevent deletion."
            ),
        })

        recommendations.append(
            "Review applicable retention policies, legal holds, "
            "and storage lifecycle settings."
        )

    # Evidence completeness
    if not evidence_complete:

        findings.append({
            "finding_id": "INCOMPLETE_CLOUD_EVIDENCE",
            "severity": "MEDIUM",
            "description": (
                "The supplied cloud evidence is incomplete "
                "and cannot establish deletion across "
                "all relevant storage locations."
            ),
        })

        recommendations.append(
            "Collect additional provider records and verify "
            "all relevant storage locations."
        )

    # Locations checked
    if not locations_checked:

        findings.append({
            "finding_id": "NO_STORAGE_LOCATIONS_VERIFIED",
            "severity": "MEDIUM",
            "description": (
                "No cloud storage locations were reported "
                "as checked."
            ),
        })

        recommendations.append(
            "Identify and inspect relevant primary, versioned, "
            "replicated, and backup storage locations."
        )

    # Determine verification status
    high_findings = [
        finding for finding in findings
        if finding["severity"] == "HIGH"
    ]

    medium_findings = [
        finding for finding in findings
        if finding["severity"] == "MEDIUM"
    ]

    if high_findings:
        verification_status = "FAILED"
        risk_level = "HIGH"

    elif medium_findings:
        verification_status = "INCONCLUSIVE"
        risk_level = "MEDIUM"

    else:
        verification_status = "VERIFIED"
        risk_level = "LOW"

    # Summary
    if verification_status == "FAILED":

        summary = (
            "Cloud deletion verification failed because "
            "evidence indicates deletion was not confirmed "
            "or residual data was identified."
        )

    elif verification_status == "INCONCLUSIVE":

        summary = (
            "Cloud deletion could not be conclusively "
            "verified because evidence limitations or "
            "retention conditions remain."
        )

    else:

        summary = (
            "The supplied evidence supports deletion within "
            "the examined scope. This does not independently "
            "establish permanent erasure across all cloud "
            "systems or undisclosed copies."
        )

    if not recommendations:

        recommendations.append(
            "Preserve provider deletion records and periodically "
            "verify cloud storage disposition."
        )

    return {
        "analysis_status": "COMPLETED",
        "analysis_type": "RULES_BASED_CLOUD_FORENSIC_ANALYSIS",
        "verification_status": verification_status,
        "risk_level": risk_level,
        "summary": summary,
        "statistics": {
            "residual_objects": len(residual_objects),
            "retained_versions": len(retained_versions),
            "backup_copies": len(backup_copies),
            "locations_checked": len(locations_checked),
            "evidence_complete": evidence_complete,
        },
        "findings": findings,
        "recommendations": recommendations,
    }