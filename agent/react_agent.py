import json
from groq import Groq
from agent.prompt import SYSTEM_PROMPT
from agent.state import AgentState

from tools.metrics import check_metrics
from tools.logs import check_logs
from tools.deployments import check_deployments
from tools.dependencies import check_dependencies

TOOLS = {
    "check_metrics": check_metrics,
    "check_logs": check_logs,
    "check_deployments": check_deployments,
    "check_dependencies": check_dependencies,
}

class ReActAgent:
    def __init__(self, model="llama-3.3-70b-versatile"):
        self.client = Groq()
        self.model = model

    def run(self, state: AgentState, max_steps: int = 6) -> AgentState:
        """
        Execute the ReAct loop:
        Reason -> Act -> Observe -> Repeat
        with application-level stopping and deterministic fallback conclusion.
        """

        while not state.done and state.steps < max_steps:
            # 1. Ask the LLM what to do next
            response = self._reason(state)
            decision = self._parse_response(response)

            # 2. Model-driven stop (if the LLM explicitly finishes)
            if decision.get("done"):
                state.done = True
                state.conclusion = decision.get(
                    "conclusion",
                    "Incident analysis completed by agent."
                )
                break

            # 3. Extract tool call
            action = decision.get("action")
            if not action:
                # Defensive guardrail
                break

            tool_name = action.get("tool")
            args = action.get("args", {})

            tool_fn = TOOLS.get(tool_name)
            if not tool_fn:
                raise ValueError(f"Unknown tool requested by agent: {tool_name}")

            # 4. Execute tool deterministically
            result = tool_fn(**args)

            # 5. Store observation
            state.observations.append({
                "step": state.steps + 1,
                "thought": decision.get("thought"),
                "tool": tool_name,
                "args": args,
                "result": result
            })

            state.steps += 1
            
            # Live reasoning trace
            self._print_trace(state.observations[-1])   
            
            # 6. Application-level stopping (critical)
            if self._enough_evidence(state.observations):
                state.done = True
                print("\n[STOP] Enough evidence collected by application logic.")
                state.conclusion = self._summarize(state)
                break

        # 7. Final fallback (guarantees a conclusion)
        if not state.conclusion:
            state.conclusion = self._summarize(state)

        print("\nConclusion:")
        print(state.conclusion)
        return state

    def _reason(self, state: AgentState) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps({
                    "goal": state.goal,
                    "service": state.service,
                    "observations": state.observations
                })
            }
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0
        )

        return response.choices[0].message.content

    def _parse_response(self, response: str) -> dict:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from model:\n{response}")
    
    def _enough_evidence(self, observations):
        tools_used = {obs["tool"] for obs in observations}

        # Simple heuristic: if we checked metrics + logs + one more signal
        return (
            "check_metrics" in tools_used and
            "check_logs" in tools_used and
            len(tools_used) >= 3
        )
    
    def _summarize(self, state: AgentState) -> str:
        summary = []

        for obs in state.observations:
            tool = obs["tool"]
            result = obs["result"]

            if tool == "check_metrics":
                metrics = result["metrics"]
                if metrics["cpu_percent"] > 80:
                    summary.append("High CPU usage detected.")
                if metrics["latency_ms"] > 500:
                    summary.append("High service latency observed.")

            elif tool == "check_logs":
                if result["error_count"] > 0:
                    summary.append("Application errors found in logs.")

            elif tool == "check_deployments":
                summary.append("Recent deployment detected.")

            elif tool == "check_dependencies":
                if result["degraded_dependencies"]:
                    summary.append(
                        f"Degraded dependency: {', '.join(result['degraded_dependencies'])}"
                    )

        return "Likely root cause: " + " ".join(summary)
    
    def _print_trace(self, step_data: dict):
        print(f"\n[Step {step_data['step']}]")
        if step_data.get("thought"):
            print(f"Thought: {step_data['thought']}")

        print(
            f"Action: {step_data['tool']}"
            f"(service={step_data['args'].get('service')})"
        )

        result = step_data["result"]
        if "metrics" in result:
            m = result["metrics"]
            print(
                f"Observation: CPU={m['cpu_percent']}%, "
                f"Latency={m['latency_ms']}ms"
            )
        elif "error_count" in result:
            print(f"Observation: {result['error_count']} error logs found")
        elif "degraded_dependencies" in result:
            if result["degraded_dependencies"]:
                print(
                    "Observation: Degraded dependency -> "
                    + ", ".join(result["degraded_dependencies"])
                )
            else:
                print("Observation: All dependencies healthy")
        elif "deployment" in result:
            print(
                "Observation: Recent deployment "
                f"{result['deployment']['version']}"
            )