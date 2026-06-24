# Lab 20: Multi-Agent Research System

This repo implements a multi-agent research assistant with **Supervisor + Researcher + Analyst + Writer** and a single-agent Gemini baseline for comparison.

## Learning Outcomes

After the lab, the project demonstrates:

1. Clear roles for multiple agents.
2. Shared state for handoff and debugging.
3. Guardrails: max iterations, timeout, fallback, and validation.
4. Traceable workflow execution.
5. Benchmark comparison between single-agent and multi-agent runs.

## Architecture

```text
User Query
   |
   v
Supervisor / Router
   |------> Researcher Agent  -> research_notes
   |------> Analyst Agent     -> analysis_notes
   |------> Writer Agent      -> final_answer
   |
   v
Trace + Benchmark Report
```

## Repository Structure

```text
.
├── src/multi_agent_research_lab/
│   ├── agents/              # Supervisor, Researcher, Analyst, Writer, Critic
│   ├── core/                # Config, state, schemas, errors
│   ├── graph/               # Lightweight workflow runner
│   ├── services/            # Gemini LLM, Tavily search, artifact storage
│   ├── evaluation/          # Benchmark and markdown report rendering
│   ├── observability/       # Logging and local tracing hooks
│   └── cli.py               # CLI entrypoint
├── configs/
├── docs/
├── reports/                 # Benchmark report and trace exports
├── tests/
├── .env.example
├── pyproject.toml
└── Makefile
```

## Quickstart

### 1. Create Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[llm,dev]"
cp .env.example .env
```

### 2. Configure API Keys

Open `.env` and fill in your keys.

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.1-flash-lite

# Optional tracing/search providers
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=multi-agent-research-lab
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
LANGFUSE_HOST=https://cloud.langfuse.com
TAVILY_API_KEY=...
```

No API key is hard-coded in source files.

### 3. Run Smoke Tests

```bash
python -m pytest
python -m multi_agent_research_lab.cli --help
```

### 4. Run Single-Agent Baseline

```bash
python -m multi_agent_research_lab.cli baseline \
  --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

### 5. Run Multi-Agent Workflow

```bash
python -m multi_agent_research_lab.cli multi-agent \
  --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

The expected route is:

```text
researcher -> analyst -> writer -> done
```

### 6. Generate Benchmark Deliverables

```bash
python -m multi_agent_research_lab.cli benchmark \
  --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

Generated artifacts:

- `reports/benchmark_report.md`
- `reports/traces/baseline.json`
- `reports/traces/multi_agent.json`

### 7. Benchmark All Prompts In `Question.md`

```bash
python -m multi_agent_research_lab.cli benchmark-questions --file Question.md
```

Generated artifacts:

- `reports/question_benchmark_report.md`
- `reports/traces/questions/*_baseline.json`
- `reports/traces/questions/*_multi_agent.json`

## Implementation Summary

| Requirement | Status |
|---|---|
| Implement LLM client | Done: Gemini via `google-genai` |
| Implement search client | Done: Tavily with local fallback |
| Implement Supervisor routing | Done |
| Implement Researcher, Analyst, Writer | Done |
| Build workflow | Done: lightweight deterministic runner |
| Add tracing | Done: local state trace and JSON export |
| Write benchmark report | Done via `benchmark` CLI |
| Evaluate `Question.md` prompts | Done via `benchmark-questions` CLI |

## Production Conventions

- `agents`, `services`, `core`, `graph`, `evaluation`, and `observability` are separated.
- Input/output data uses Pydantic schemas.
- API keys are read from `.env`.
- Workflow is guarded by `MAX_ITERATIONS` and provider timeouts.
- Search and LLM failures have fallbacks so the workflow can finish and record the issue.
- Benchmark artifacts are written under `reports/`.

## Deliverables

Submit:

1. Personal GitHub repo.
2. Screenshot of CLI trace output or the exported JSON trace files.
3. `reports/benchmark_report.md`.
4. Failure mode explanation from `reports/benchmark_report.md` or `docs/design_template.md`.

## Failure Mode

During live testing, Gemini occasionally disconnected before sending a response. The fix wraps SDK/network exceptions in the LLM client and lets agents fall back to the best available intermediate state. Tavily search also has a local fallback so the workflow remains demonstrable when search is unavailable.

## References

- Anthropic: Building effective agents — https://www.anthropic.com/engineering/building-effective-agents
- LangGraph concepts — https://langchain-ai.github.io/langgraph/concepts/
- LangSmith tracing — https://docs.smith.langchain.com/
- Langfuse tracing — https://langfuse.com/docs
