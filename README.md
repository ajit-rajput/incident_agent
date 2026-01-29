# Incident Response Agent (ReAct Pattern)

A local, tool-driven **Incident Response AI Agent** built to demonstrate the **ReAct (Reason → Act → Observe)** pattern using a free LLM provider (Groq) and deterministic backend tools.

The agent diagnoses service incidents step-by-step, similar to how an SRE would troubleshoot a real production issue.

---

## What this project demonstrates

This project focuses on **agent behavior and autonomous incident diagnosis**.

Key concepts implemented:

- **ReAct agent loop** (Reason → Act → Observe → Repeat)
- **Multi-step reasoning** with LLM-driven decision making
- **Tool selection and orchestration** - the agent chooses which diagnostic tools to use
- **Application-level stopping logic** - the app decides when enough evidence has been collected
- **Deterministic fallback conclusions** - guarantees a conclusion even if max steps reached
- **Live reasoning trace** - displays thoughts, actions, and observations in real-time
- **Provider-agnostic agent design** - easy to swap LLM providers

The LLM proposes actions. The application validates, executes tools, and decides when to stop.

---

## Example use case

**Goal**: Service latency is high for checkout-service

**Agent behavior**
1. Check service metrics → Observe high CPU (92%) and latency (850ms)
2. Check application logs → Observe database timeout errors
3. Check downstream dependencies → Observe payment-gateway is degraded
4. Analyze observations → Conclude likely root cause: payment-gateway degradation

This mirrors real incident response workflows used by SREs.

---

## How it works

### 1. Agent Loop (`agent/react_agent.py`)

The `ReActAgent.run()` method executes the core loop:

```
STEP 1: REASON
  ↓
  Agent calls LLM with:
  - Current goal
  - Service name
  - Previous observations
  
STEP 2: PARSE DECISION
  ↓
  LLM responds with JSON:
  {
    "thought": "...",
    "action": {"tool": "check_metrics", "args": {"service": "..."}},
    "done": false
  }
  
STEP 3: ACT
  ↓
  Agent executes the tool:
  - Tool runs deterministically (reads from JSON files)
  - Returns structured result
  
STEP 4: OBSERVE
  ↓
  Agent stores observation:
  {"step": 1, "thought": "...", "tool": "...", "result": {...}}
  
STEP 5: APPLICATION LOGIC
  ↓
  Agent checks if enough evidence collected:
  - Heuristic: metrics + logs + 1 more tool = stop
  - Prevents over-analysis
  
STEP 6: REPEAT or CONCLUDE
  ↓
  If done → Generate final conclusion
  Else → Loop back to STEP 1 (max 6 steps)
```

### 2. State Management (`agent/state.py`)

`AgentState` tracks:
- `goal`: The incident being investigated (e.g., "Service latency is high")
- `service`: Target service name (e.g., "checkout-service")
- `observations`: List of tool results and reasoning steps
- `steps`: Current step count (prevents infinite loops)
- `done`: Whether investigation is complete
- `conclusion`: Final root cause analysis

### 3. System Prompt (`agent/prompt.py`)

Instructs the LLM to:
- Think step-by-step about what diagnostic tool to use next
- Choose exactly ONE tool per step
- Use previous observations to inform decisions
- Respond in strict JSON format (parsed and validated by the agent)
- Stop when enough evidence is collected

### 4. Diagnostic Tools (`tools/`)

All tools read from static JSON data files (deterministic for testing/demo):

| Tool | Function | Returns |
|------|----------|---------|
| `check_metrics(service)` | Reads `data/metrics.json` | CPU%, latency, throughput |
| `check_logs(service)` | Reads `data/logs.json` | Error count, recent errors |
| `check_deployments(service)` | Reads `data/deployments.json` | Recent deployment info |
| `check_dependencies(service)` | Reads `data/dependencies.json` | Upstream/downstream services, health status |

### 5. Incident Conclusion (`react_agent._summarize()`)

Deterministic rule-based summarizer that:
- Analyzes all collected observations
- Identifies anomalies (high CPU, errors, degraded dependencies)
- Generates human-readable conclusion
- **Guarantees a conclusion** even if max steps reached

---

## Tech stack

- **Python 3.10+** - Language
- **Groq API** (free tier) - LLM provider
- **LLaMA 3.3 (70B)** - Base model
- **Pure Python** - No agent frameworks (all logic explicit)
- **JSON** - Data format and LLM I/O
- **CLI** - For transparency and debugging

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Groq API key (get free at [console.groq.com](https://console.groq.com))

### Steps

1. **Clone and navigate to project**
   ```bash
   cd incident_agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**
   Create a `.env` file in the project root:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

---

## Usage

### Run the agent

```bash
python main.py
```

**Expected output:**
```
Step 1: check_metrics
{'ok': True, 'service': 'checkout-service', 'metrics': {...}}

Step 2: check_logs
{'ok': True, 'service': 'checkout-service', 'error_count': 5, ...}

Step 3: check_dependencies
{'ok': True, 'service': 'checkout-service', 'degraded_dependencies': ['payment-gateway']}

[STOP] Enough evidence collected by application logic.

--- INCIDENT SUMMARY ---
Conclusion:
High service latency observed. Payment gateway is degraded. High CPU usage detected. Application errors found in logs.
```

### Customize the incident

Edit `main.py`:

```python
state = AgentState(
    goal="Service latency is high",      # Change the incident
    service="checkout-service"            # Change the service
)
```

---

## Configuration

### Max steps limit

Edit `agent/react_agent.py`:

```python
def run(self, state: AgentState, max_steps: int = 6) -> AgentState:
```

Change `max_steps=6` to adjust how many reasoning steps before forced conclusion.

### LLM model

Edit `agent/react_agent.py`:

```python
def __init__(self, model="llama-3.3-70b-versatile"):
```

Swap with other Groq models: `mixtral-8x7b-32768`, `gemma2-9b-it`, etc.

### Application stopping heuristic

Edit `agent/react_agent._enough_evidence()`:

```python
def _enough_evidence(self, observations):
    # Customize when to stop based on tools used
    tools_used = {obs["tool"] for obs in observations}
    return (
        "check_metrics" in tools_used and
        "check_logs" in tools_used and
        len(tools_used) >= 3
    )
```

---

## Key design decisions

1. **Deterministic tools** - All tools read from static JSON (no real APIs). Makes testing predictable and reproducible.

2. **Application-level stopping** - The agent doesn't decide when to stop; the application does. Prevents unnecessary LLM calls and ensures the agent always terminates.

3. **Guaranteed conclusion** - Even if max steps reached, a conclusion is always generated from observations.

4. **Explicit logic** - No magic framework. All agent behavior is visible in pure Python code.

5. **JSON I/O** - Strict structured format between agent and LLM prevents parsing ambiguity.

---

## Extending the agent

### Add a new diagnostic tool

1. Create a tool function in `tools/your_tool.py`:
   ```python
   def check_performance(service: str) -> dict:
       # Your logic here
       return {"ok": True, "data": {...}}
   ```

2. Add to tools registry in `agent/react_agent.py`:
   ```python
   from tools.your_tool import check_performance
   
   TOOLS = {
       ...
       "check_performance": check_performance,
   }
   ```

3. Update the system prompt in `agent/prompt.py`:
   ```python
   Available tools:
   - check_metrics(service)
   - check_logs(service)
   - check_deployments(service)
   - check_dependencies(service)
   - check_performance(service)
   ```

### Add a new incident scenario

Edit `data/` JSON files to model your incident:

- `metrics.json` - Add service with CPU/latency anomalies
- `logs.json` - Add error logs
- `deployments.json` - Add recent deployment info
- `dependencies.json` - Add dependency health status

Then run:
```bash
python main.py
```

---

## Dependencies

See `requirements.txt`:
- **groq** (>=0.9.0) - LLM API client
- **python-dotenv** (>=1.0.0) - Environment variable management

---

## Limitations & Future work

**Current limitations:**
- Tools read from static JSON (not real-time data)

**Future enhancements:**
- Connect to real metrics APIs (Prometheus, Datadog)
- Web UI for incident submission and result viewing
- Multi-agent coordination for complex incidents
- Incident post-mortems and learning loops
- Slack/PagerDuty integration

