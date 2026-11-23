
import hashlib
import os
import uuid

from datetime import datetime, timezone
from pathlib import Path


def get_timestamp():
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def calculate_sha256(file_path):
    """Calculate SHA-256 hash using memory-efficient chunks."""
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while True:
            chunk = file.read(1024 * 1024)  # 1 MB chunks

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def collect_evidence(directory):
    """
    Recursively collect file metadata and SHA-256 hashes.

    This collector does not intentionally modify or delete target files.
    It skips symbolic links and records collection errors.
    """

    root = Path(directory).expanduser().resolve()

    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")

    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    audit_id = str(uuid.uuid4())
    collection_time = get_timestamp()

    records = []
    errors = []

    for current_dir, subdirectories, filenames in os.walk(
        root,
        followlinks=False
    ):

        # Skip symbolic-link directories
        subdirectories[:] = [
            name for name in subdirectories
            if not (Path(current_dir) / name).is_symlink()
        ]

        for filename in filenames:
            file_path = Path(current_dir) / filename

            try:
                # Skip symbolic links
                if file_path.is_symlink():
                    continue

                if not file_path.is_file():
                    continue

                # Capture metadata before hashing
                before = file_path.stat()

                file_hash = calculate_sha256(file_path)

                # Capture metadata after hashing
                after = file_path.stat()

                # Check whether the file changed during collection
                stable = (
                    before.st_size == after.st_size
                    and before.st_mtime_ns == after.st_mtime_ns
                )

                record = {
                    "audit_id": audit_id,
                    "source_directory": str(root),
                    "file_path": str(file_path),
                    "relative_path": str(file_path.relative_to(root)),
                    "file_name": file_path.name,
                    "extension": file_path.suffix.lower(),
                    "file_size": after.st_size,
                    "created_time": datetime.fromtimestamp(
                        after.st_ctime,
                        timezone.utc
                    ).isoformat(),
                    "modified_time": datetime.fromtimestamp(
                        after.st_mtime,
                        timezone.utc
                    ).isoformat(),
                    "sha256": file_hash,
                    "collection_time": get_timestamp(),
                    "status": "collected" if stable else "unstable",
                }

                records.append(record)

                if not stable:
                    errors.append(
                        f"File changed during collection: {file_path}"
                    )

            except OSError as error:
                errors.append(
                    f"Unable to collect {file_path}: {error}"
                )

    return {
        "audit_id": audit_id,
        "source_directory": str(root),
        "collection_time": collection_time,
        "files_scanned": len(records),
        "records": records,
        "errors": errors,
    }
