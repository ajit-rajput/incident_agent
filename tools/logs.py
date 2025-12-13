import json
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "logs.json"

def check_logs(service: str) -> dict:
    with open(DATA_FILE) as f:
        data = json.load(f)

    logs = data.get(service, [])
    error_logs = [l for l in logs if l["level"] == "ERROR"]

    return {
        "ok": True,
        "service": service,
        "error_count": len(error_logs),
        "recent_errors": error_logs[:3]
    }