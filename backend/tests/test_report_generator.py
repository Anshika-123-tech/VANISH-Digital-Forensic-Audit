import json

import core.report_generator as report_generator


def make_verification_result(
    intact=0,
    modified=0,
    missing=0,
    invalid=0,
):
    results = []

    for i in range(intact):
        results.append({
            "file_name": f"intact_{i}.txt",
            "relative_path": f"files/intact_{i}.txt",
            "file_path": f"files/intact_{i}.txt",
            "status": "intact",
            "expected_hash": "abc",
            "actual_hash": "abc",
            "integrity_verified": True,
        })

    for i in range(modified):
        results.append({
            "file_name": f"modified_{i}.txt",
            "relative_path": f"files/modified_{i}.txt",
            "file_path": f"files/modified_{i}.txt",
            "status": "modified",
            "expected_hash": "abc",
            "actual_hash": "xyz",
            "integrity_verified": False,
        })

    for i in range(missing):
        results.append({
            "file_name": f"missing_{i}.txt",
            "relative_path": f"files/missing_{i}.txt",
            "file_path": f"files/missing_{i}.txt",
            "status": "missing",
            "expected_hash": "abc",
            "actual_hash": None,
            "integrity_verified": False,
        })

    for i in range(invalid):
        results.append({
            "file_name": f"invalid_{i}.txt",
            "relative_path": f"files/invalid_{i}.txt",
            "file_path": f"files/invalid_{i}.txt",
            "status": "invalid_file",
            "expected_hash": "abc",
            "actual_hash": None,
            "integrity_verified": False,
        })

    total = len(results)

    return {
        "audit_id": "test-audit-123",
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


def test_report_includes_forensic_analysis(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        report_generator,
        "REPORT_DIR",
        tmp_path,
    )

    verification = make_verification_result(
        intact=2
    )

    result = report_generator.generate_report(
        verification
    )

    report = result["report"]

    assert result["status"] == "generated"
    assert report["audit_id"] == "test-audit-123"

    assert "forensic_analysis" in report

    analysis = report["forensic_analysis"]

    assert analysis["analysis_status"] == "COMPLETED"
    assert analysis["risk_level"] == "LOW"
    assert analysis["statistics"]["intact"] == 2


def test_report_analysis_detects_modified_evidence(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        report_generator,
        "REPORT_DIR",
        tmp_path,
    )

    verification = make_verification_result(
        intact=1,
        modified=1,
    )

    result = report_generator.generate_report(
        verification
    )

    analysis = result["report"]["forensic_analysis"]

    assert analysis["risk_level"] == "HIGH"

    assert any(
        finding["finding_id"] == "MODIFIED_EVIDENCE"
        for finding in analysis["findings"]
    )


def test_saved_json_contains_forensic_analysis(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        report_generator,
        "REPORT_DIR",
        tmp_path,
    )

    verification = make_verification_result(
        intact=1,
        missing=1,
    )

    result = report_generator.generate_report(
        verification
    )

    report_path = result["report_path"]

    with open(
        report_path,
        "r",
        encoding="utf-8",
    ) as file:
        saved_report = json.load(file)

    assert saved_report == result["report"]

    assert (
        saved_report["forensic_analysis"]["risk_level"]
        == "HIGH"
    )

    assert (
        saved_report["forensic_analysis"]["statistics"]["missing"]
        == 1
    )


def test_report_preserves_original_summary(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        report_generator,
        "REPORT_DIR",
        tmp_path,
    )

    verification = make_verification_result(
        intact=2,
        modified=1,
    )

    result = report_generator.generate_report(
        verification
    )

    summary = result["report"]["summary"]

    assert summary["total_files"] == 3
    assert summary["intact"] == 2
    assert summary["modified"] == 1
    assert summary["missing"] == 0
    assert summary["invalid"] == 0
    assert summary["overall_status"] == "INTEGRITY_FAILURE"