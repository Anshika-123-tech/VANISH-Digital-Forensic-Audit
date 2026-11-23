from pathlib import Path

from core.evidence_collector import calculate_sha256


def verify_file_hash(file_path, expected_hash):
    """
    Verify a file against its previously recorded SHA-256 hash.
    """

    path = Path(file_path)

    # Check whether the file exists
    if not path.exists():
        return {
            "file_path": str(path),
            "status": "missing",
            "expected_hash": expected_hash,
            "actual_hash": None,
            "integrity_verified": False,
        }

    # Ensure it is a regular file
    if not path.is_file():
        return {
            "file_path": str(path),
            "status": "invalid_file",
            "expected_hash": expected_hash,
            "actual_hash": None,
            "integrity_verified": False,
        }

    # Calculate current SHA-256 hash
    actual_hash = calculate_sha256(path)

    # Compare original and current hashes
    if actual_hash == expected_hash:
        status = "intact"
        verified = True
    else:
        status = "modified"
        verified = False

    return {
        "file_path": str(path),
        "status": status,
        "expected_hash": expected_hash,
        "actual_hash": actual_hash,
        "integrity_verified": verified,
    }