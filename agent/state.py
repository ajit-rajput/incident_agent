from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class AgentState:
    goal: str
    service: str
    observations: List[Dict[str, Any]] = field(default_factory=list)
    steps: int = 0
    done: bool = False
    conclusion: str | None = None