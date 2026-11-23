
import sqlite3
from pathlib import Path


# Backend root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# SQLite database location
DB_PATH = BASE_DIR / "database" / "vanish.db"


def get_connection():
    """Create and return a SQLite connection."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    """Create evidence table if it does not already exist."""

    with get_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_id TEXT NOT NULL,
                source_directory TEXT NOT NULL,
                file_path TEXT NOT NULL,
                relative_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                extension TEXT,
                file_size INTEGER NOT NULL,
                created_time TEXT,
                modified_time TEXT,
                sha256 TEXT NOT NULL,
                collection_time TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_evidence_audit_id
            ON evidence(audit_id)
        """)

        connection.commit()

def save_evidence(records):
    """Save only new or changed evidence records into SQLite."""

    if not records:
        return 0

    saved_count = 0

    with get_connection() as connection:

        for record in records:

            existing = connection.execute("""
                SELECT id
                FROM evidence
                WHERE file_path = ?
                AND sha256 = ?
            """, (
                record["file_path"],
                record["sha256"],
            )).fetchone()

            # Skip files already collected with the same hash
            if existing:
                continue

            connection.execute("""
                INSERT INTO evidence (
                    audit_id,
                    source_directory,
                    file_path,
                    relative_path,
                    file_name,
                    extension,
                    file_size,
                    created_time,
                    modified_time,
                    sha256,
                    collection_time,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["audit_id"],
                record["source_directory"],
                record["file_path"],
                record["relative_path"],
                record["file_name"],
                record["extension"],
                record["file_size"],
                record["created_time"],
                record["modified_time"],
                record["sha256"],
                record["collection_time"],
                record["status"],
            ))

            saved_count += 1

        connection.commit()

    return saved_count
def get_all_evidence():
    """Retrieve all stored evidence."""

    with get_connection() as connection:

        rows = connection.execute("""
            SELECT *
            FROM evidence
            ORDER BY id DESC
        """).fetchall()

    return [dict(row) for row in rows]


def get_evidence_by_audit(audit_id):
    """Retrieve evidence for a specific audit."""

    with get_connection() as connection:

        rows = connection.execute("""
            SELECT *
            FROM evidence
            WHERE audit_id = ?
            ORDER BY id ASC
        """, (audit_id,)).fetchall()

    return [dict(row) for row in rows]


def get_evidence_count():
    """Return the total number of stored evidence records."""

    with get_connection() as connection:

        result = connection.execute("""
            SELECT COUNT(*) AS total
            FROM evidence
        """).fetchone()

    return result["total"]
