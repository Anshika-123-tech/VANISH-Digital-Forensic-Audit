import json
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "audit_logs"
LOG_FILE = LOG_DIR / "vanish_audit.log"


def log_event(
    event,
    audit_id=None,
    status="INFO",
    details=None,
):
    """
    Record a VANISH audit event in JSON Lines format.
    """

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "audit_id": audit_id,
        "status": status,
        "details": details or {},
    }

    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(json.dumps(entry) + "\n")

    return entry
def get_audit_logs():
    if not LOG_FILE.exists():
        return []

    logs = []

    with open(LOG_FILE, "r", encoding="utf-8") as file:
        for line in file:
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return logs