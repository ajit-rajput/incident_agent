import json
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "dependencies.json"

def check_dependencies(service: str) -> dict:
    with open(DATA_FILE) as f:
        data = json.load(f)

    deps = data.get(service)
    if not deps:
        return {"ok": False, "error": "No dependency data"}

    degraded = [
        name for name, status in deps["dependency_health"].items()
        if status != "healthy"
    ]

    return {
        "ok": True,
        "service": service,
        "dependencies": deps["depends_on"],
        "degraded_dependencies": degraded
    }