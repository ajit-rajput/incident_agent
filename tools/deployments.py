import json
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "deployments.json"

def check_deployments(service: str) -> dict:
    with open(DATA_FILE) as f:
        data = json.load(f)

    deployment = data.get(service)
    if not deployment:
        return {"ok": False, "error": "No deployment info"}

    return {
        "ok": True,
        "service": service,
        "deployment": deployment
    }