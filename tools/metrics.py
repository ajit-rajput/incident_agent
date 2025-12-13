import json
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "metrics.json"

def check_metrics(service: str) -> dict:
    with open(DATA_FILE) as f:
        data = json.load(f)

    metrics = data.get(service)
    if not metrics:
        return {"ok": False, "error": "Service not found"}

    return {
        "ok": True,
        "service": service,
        "metrics": metrics
    }