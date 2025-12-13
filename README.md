# Incident Response Agent (ReAct Pattern)

A local, tool-driven **Incident Response AI Agent** built to demonstrate the **ReAct (Reason → Act → Observe)** pattern using a free LLM provider (Groq) and deterministic backend tools.

The agent diagnoses service incidents step-by-step, similar to how an SRE would troubleshoot a real production issue.

---

## What this project demonstrates

This project focuses on **agent behavior**, not chatbots.

Key concepts implemented:

- ReAct agent loop (Reason → Act → Observe → Repeat)
- Multi-step reasoning
- Tool selection and orchestration
- Application-level stopping logic
- Deterministic fallback conclusions
- Live reasoning trace (thoughts, actions, observations)
- Provider-agnostic agent design

The LLM proposes actions.  
The application validates, executes tools, and decides when to stop.

---

## Example use case

**Input**
**Agent behavior**
1. Check service metrics  
2. Observe high CPU and latency  
3. Check application logs  
4. Observe error patterns  
5. Check downstream dependencies  
6. Conclude likely root cause  

This mirrors real incident response workflows.

---

## Architecture overview

User Goal --> ReAct Agent Loop --> Reason (LLM) --> Action (Tool selection) --> Observation (Deterministic data) --> Repeat until sufficient evidence --> Final conclusion (always guaranteed)

## Tech stack

- Python 3.10+
- Groq API (free tier)
- LLaMA 3.3 (70B) model
- No agent frameworks (pure Python)
- CLI-based execution for transparency

## Run
python main.py