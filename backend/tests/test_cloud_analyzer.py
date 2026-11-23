import pytest

from core.cloud_analyzer import analyze_cloud_evidence


def valid_cloud_evidence():
    return {
        "deletion_confirmed": True,
        "residual_objects": [],
        "retained_versions": [],
        "backup_copies": [],
        "retention_active": False,
        "locations_checked": ["primary_storage"],
        "evidence_complete": True,
    }


def test_cloud_deletion_verified():
    result = analyze_cloud_evidence(valid_cloud_evidence())

    assert result["analysis_status"] == "COMPLETED"
    assert result["verification_status"] == "VERIFIED"
    assert result["risk_level"] == "LOW"
    assert result["findings"] == []


def test_deletion_not_confirmed():
    evidence = valid_cloud_evidence()
    evidence["deletion_confirmed"] = False

    result = analyze_cloud_evidence(evidence)

    assert result["verification_status"] == "FAILED"
    assert result["risk_level"] == "HIGH"
    assert "DELETION_NOT_CONFIRMED" in [
        finding["finding_id"]
        for finding in result["findings"]
    ]


def test_residual_objects_detected():
    evidence = valid_cloud_evidence()
    evidence["residual_objects"] = ["object_001", "object_002"]

    result = analyze_cloud_evidence(evidence)

    assert result["verification_status"] == "FAILED"
    assert "RESIDUAL_OBJECTS_DETECTED" in [
        finding["finding_id"]
        for finding in result["findings"]
    ]


def test_retained_versions_detected():
    evidence = valid_cloud_evidence()
    evidence["retained_versions"] = ["version_001"]

    result = analyze_cloud_evidence(evidence)

    assert result["verification_status"] == "FAILED"
    assert "RETAINED_VERSIONS_DETECTED" in [
        finding["finding_id"]
        for finding in result["findings"]
    ]


def test_backup_copies_detected():
    evidence = valid_cloud_evidence()
    evidence["backup_copies"] = ["backup_001"]

    result = analyze_cloud_evidence(evidence)

    assert result["verification_status"] == "INCONCLUSIVE"
    assert result["risk_level"] == "MEDIUM"
    assert "BACKUP_COPIES_DETECTED" in [
        finding["finding_id"]
        for finding in result["findings"]
    ]


def test_retention_policy_active():
    evidence = valid_cloud_evidence()
    evidence["retention_active"] = True

    result = analyze_cloud_evidence(evidence)

    assert result["verification_status"] == "INCONCLUSIVE"
    assert "RETENTION_POLICY_ACTIVE" in [
        finding["finding_id"]
        for finding in result["findings"]
    ]


def test_incomplete_evidence():
    evidence = valid_cloud_evidence()
    evidence["evidence_complete"] = False

    result = analyze_cloud_evidence(evidence)

    assert result["verification_status"] == "INCONCLUSIVE"
    assert "INCOMPLETE_CLOUD_EVIDENCE" in [
        finding["finding_id"]
        for finding in result["findings"]
    ]


def test_no_locations_checked():
    evidence = valid_cloud_evidence()
    evidence["locations_checked"] = []

    result = analyze_cloud_evidence(evidence)

    assert result["verification_status"] == "INCONCLUSIVE"
    assert "NO_STORAGE_LOCATIONS_VERIFIED" in [
        finding["finding_id"]
        for finding in result["findings"]
    ]


def test_missing_required_fields():
    evidence = valid_cloud_evidence()
    del evidence["deletion_confirmed"]

    result = analyze_cloud_evidence(evidence)

    assert result["analysis_status"] == "INCOMPLETE"
    assert result["verification_status"] == "INCONCLUSIVE"
    assert "deletion_confirmed" in result["missing_fields"]


def test_invalid_input_type():
    with pytest.raises(TypeError):
        analyze_cloud_evidence("invalid input")


def test_invalid_residual_objects_type():
    evidence = valid_cloud_evidence()
    evidence["residual_objects"] = "not a list"

    with pytest.raises(ValueError):
        analyze_cloud_evidence(evidence)