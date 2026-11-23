import hashlib
from pathlib import Path

import pytest

import core.evidence_collector as collector


def test_recursive_collection(tmp_path):

    root = tmp_path / "evidence"
    subfolder = root / "nested"

    subfolder.mkdir(parents=True)

    file1 = root / "first.txt"
    file2 = subfolder / "second.txt"

    file1.write_text("First evidence", encoding="utf-8")
    file2.write_text("Second evidence", encoding="utf-8")

    result = collector.collect_evidence(str(root))

    assert result["files_scanned"] == 2
    assert len(result["records"]) == 2
    assert result["errors"] == []

    paths = {
        record["relative_path"]
        for record in result["records"]
    }

    assert "first.txt" in paths
    assert str(Path("nested") / "second.txt") in paths


def test_sha256_is_correct(tmp_path):

    root = tmp_path / "evidence"
    root.mkdir()

    content = b"VANISH forensic hash test"

    file_path = root / "hash_test.txt"
    file_path.write_bytes(content)

    result = collector.collect_evidence(str(root))

    record = result["records"][0]

    expected_hash = hashlib.sha256(content).hexdigest()

    assert record["sha256"] == expected_hash


def test_file_metadata_is_collected(tmp_path):

    root = tmp_path / "evidence"
    root.mkdir()

    file_path = root / "metadata.pdf"
    content = b"Test PDF evidence"
    file_path.write_bytes(content)

    result = collector.collect_evidence(str(root))

    record = result["records"][0]

    assert record["file_name"] == "metadata.pdf"
    assert record["extension"] == ".pdf"
    assert record["file_size"] == len(content)
    assert record["status"] == "collected"

    assert record["created_time"]
    assert record["modified_time"]
    assert record["collection_time"]

    assert record["audit_id"] == result["audit_id"]


def test_empty_directory(tmp_path):

    root = tmp_path / "empty_evidence"
    root.mkdir()

    result = collector.collect_evidence(str(root))

    assert result["files_scanned"] == 0
    assert result["records"] == []
    assert result["errors"] == []


def test_missing_directory_raises_error(tmp_path):

    missing = tmp_path / "does_not_exist"

    with pytest.raises(FileNotFoundError):
        collector.collect_evidence(str(missing))


def test_file_instead_of_directory_raises_error(tmp_path):

    file_path = tmp_path / "not_a_directory.txt"
    file_path.write_text("test", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        collector.collect_evidence(str(file_path))


def test_symbolic_link_file_is_skipped(tmp_path):

    root = tmp_path / "evidence"
    root.mkdir()

    original = root / "original.txt"
    original.write_text("Original file", encoding="utf-8")

    link = root / "linked.txt"

    try:
        link.symlink_to(original)

    except (OSError, NotImplementedError):
        pytest.skip("Symbolic links unavailable on this system")

    result = collector.collect_evidence(str(root))

    assert result["files_scanned"] == 1

    filenames = [
        record["file_name"]
        for record in result["records"]
    ]

    assert "original.txt" in filenames
    assert "linked.txt" not in filenames


def test_symbolic_link_directory_is_skipped(tmp_path):

    root = tmp_path / "evidence"
    root.mkdir()

    real_directory = root / "real"
    real_directory.mkdir()

    real_file = real_directory / "inside.txt"
    real_file.write_text("Evidence", encoding="utf-8")

    linked_directory = root / "linked_directory"

    try:
        linked_directory.symlink_to(
            real_directory,
            target_is_directory=True,
        )

    except (OSError, NotImplementedError):
        pytest.skip("Directory symbolic links unavailable")

    result = collector.collect_evidence(str(root))

    # File should only be collected once, from the real directory
    assert result["files_scanned"] == 1


def test_file_changed_during_collection_is_marked_unstable(
    tmp_path,
    monkeypatch,
):

    root = tmp_path / "evidence"
    root.mkdir()

    file_path = root / "changing.txt"
    file_path.write_text("Original content", encoding="utf-8")

    original_hash_function = collector.calculate_sha256

    def changing_hash_function(path):

        calculated_hash = original_hash_function(path)

        # Modify the file after its initial hash calculation
        Path(path).write_text(
            "Modified content with a different size",
            encoding="utf-8",
        )

        return calculated_hash

    monkeypatch.setattr(
        collector,
        "calculate_sha256",
        changing_hash_function,
    )

    result = collector.collect_evidence(str(root))

    assert result["files_scanned"] == 1

    record = result["records"][0]

    assert record["status"] == "unstable"

    assert any(
        "File changed during collection"
        in error
        for error in result["errors"]
    )