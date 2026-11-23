from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


def test_sanitization_rejects_path_outside_allowed_directory(
    tmp_path,
):
    """
    The API must reject targets outside the permitted
    evidence directory.
    """

    outside_file = tmp_path / "outside.txt"
    outside_file.write_text(
        "Sensitive test data",
        encoding="utf-8",
    )

    response = client.post(
        "/api/v1/sanitization/verify",
        params={
            "target_path": str(outside_file),
            "sanitization_method": "file_deletion",
            "storage_type": "filesystem",
        },
    )

    assert response.status_code == 403

    assert (
        response.json()["detail"]
        == "Access restricted to the test evidence directory"
    )


def test_sanitization_rejects_path_traversal():
    """
    The API must reject path traversal attempts
    that resolve outside the permitted directory.
    """

    traversal_path = (
        main.BASE_DIR
        / "evidence"
        / "test_files"
        / ".."
        / ".."
        / ".."
        / "outside.txt"
    )

    response = client.post(
        "/api/v1/sanitization/verify",
        params={
            "target_path": str(traversal_path),
            "sanitization_method": "file_deletion",
            "storage_type": "filesystem",
        },
    )

    assert response.status_code == 403

    assert (
        response.json()["detail"]
        == "Access restricted to the test evidence directory"
    )