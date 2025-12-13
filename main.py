from agent.react_agent import ReActAgent
from agent.state import AgentState

if __name__ == "__main__":

    from dotenv import load_dotenv
    load_dotenv()

    state = AgentState(
        goal="Service latency is high",
        service="checkout-service"
    )

    agent = ReActAgent()
    final_state = agent.run(state)

    print("\n--- INCIDENT SUMMARY ---")
    for step, obs in enumerate(final_state.observations, 1):
        print(f"\nStep {step}: {obs['tool']}")
        print(obs["result"])

    print("\nConclusion:")
    print(final_state.conclusion)