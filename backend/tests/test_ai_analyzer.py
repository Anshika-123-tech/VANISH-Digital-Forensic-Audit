import pytest

from core.ai_analyzer import analyze_evidence


def make_result(
    intact=0,
    modified=0,
    missing=0,
    invalid=0,
):
    total = intact + modified + missing + invalid

    results = []

    for i in range(intact):
        results.append({
            "file_name": f"intact_{i}.txt",
            "relative_path": f"files/intact_{i}.txt",
            "status": "intact",
            "expected_hash": "abc",
            "actual_hash": "abc",
        })

    for i in range(modified):
        results.append({
            "file_name": f"modified_{i}.txt",
            "relative_path": f"files/modified_{i}.txt",
            "status": "modified",
            "expected_hash": "abc",
            "actual_hash": "xyz",
        })

    for i in range(missing):
        results.append({
            "file_name": f"missing_{i}.txt",
            "relative_path": f"files/missing_{i}.txt",
            "status": "missing",
            "expected_hash": "abc",
            "actual_hash": None,
        })

    for i in range(invalid):
        results.append({
            "file_name": f"invalid_{i}.txt",
            "relative_path": f"files/invalid_{i}.txt",
            "status": "invalid_file",
            "expected_hash": "abc",
            "actual_hash": None,
        })

    return {
        "audit_id": "test-audit",
        "total_files": total,
        "intact": intact,
        "modified": modified,
        "missing": missing,
        "invalid": invalid,
        "overall_status": (
            "INTEGRITY_FAILURE"
            if modified or missing or invalid
            else "INTEGRITY_VERIFIED"
        ),
        "results": results,
    }


def test_all_files_intact():
    result = make_result(intact=3)

    analysis = analyze_evidence(result)

    assert analysis["analysis_status"] == "COMPLETED"
    assert analysis["risk_level"] == "LOW"
    assert analysis["risk_score"] == 0
    assert analysis["findings"] == []
    assert analysis["statistics"]["intact"] == 3


def test_modified_file_detected():
    result = make_result(intact=2, modified=1)

    analysis = analyze_evidence(result)

    assert analysis["risk_level"] == "HIGH"
    assert analysis["risk_score"] == 100

    assert any(
        finding["finding_id"] == "MODIFIED_EVIDENCE"
        for finding in analysis["findings"]
    )


def test_missing_file_detected():
    result = make_result(intact=1, missing=1)

    analysis = analyze_evidence(result)

    assert analysis["risk_level"] == "HIGH"

    assert any(
        finding["finding_id"] == "MISSING_EVIDENCE"
        for finding in analysis["findings"]
    )


def test_invalid_file_detected():
    result = make_result(invalid=1)

    analysis = analyze_evidence(result)

    assert analysis["risk_level"] == "HIGH"

    assert any(
        finding["finding_id"] == "INVALID_EVIDENCE"
        for finding in analysis["findings"]
    )


def test_multiple_anomalies_detected():
    result = make_result(
        intact=1,
        modified=1,
        missing=1,
        invalid=1,
    )

    analysis = analyze_evidence(result)

    assert analysis["risk_level"] == "HIGH"
    assert len(analysis["findings"]) == 3
    assert len(analysis["file_findings"]) == 3
    assert len(analysis["recommendations"]) >= 3


def test_file_findings_contain_file_information():
    result = make_result(modified=1)

    analysis = analyze_evidence(result)

    file_finding = analysis["file_findings"][0]

    assert file_finding["file_name"] == "modified_0.txt"
    assert file_finding["status"] == "modified"
    assert file_finding["expected_hash"] == "abc"
    assert file_finding["actual_hash"] == "xyz"


def test_empty_audit_returns_unknown_risk():
    result = make_result()

    analysis = analyze_evidence(result)

    assert analysis["risk_level"] == "UNKNOWN"
    assert analysis["risk_score"] == 0


def test_not_found_result():
    result = {
        "audit_id": "missing-audit",
        "status": "not_found",
        "message": "No evidence records found.",
    }

    analysis = analyze_evidence(result)

    assert analysis["analysis_status"] == "NOT_ANALYZED"
    assert analysis["risk_level"] == "UNKNOWN"
    assert analysis["findings"] == []


def test_non_dictionary_input_raises_error():
    with pytest.raises(TypeError):
        analyze_evidence("invalid")


def test_results_not_list_raises_error():
    result = make_result(intact=1)
    result["results"] = "invalid"

    with pytest.raises(ValueError):
        analyze_evidence(result)