# Lab Guide: Multi-Agent Research System

## Scenario

This project builds a research assistant that can receive a query, collect sources, analyze the evidence, and write a final answer. The lab compares two approaches:

1. **Single-agent baseline**: one Gemini call answers the full query directly.
2. **Multi-agent workflow**: Supervisor routes Researcher, Analyst, and Writer through shared state.

## Important Rules

- Keep each agent role clear and narrow.
- Store handoff data in `ResearchState` so the run is debuggable.
- Trace every routing and worker step.
- Benchmark the result instead of judging only by a nice-looking answer.
- Keep API keys in `.env`; never hard-code them in source files.

## Milestone 1: Baseline

Implemented in:

- `src/multi_agent_research_lab/cli.py`
- `src/multi_agent_research_lab/services/llm_client.py`

The baseline command calls Gemini directly and records token metadata in `agent_results`.

```bash
python -m multi_agent_research_lab.cli baseline --query "Giai thich ngan gon multi-agent system la gi"
```

## Milestone 2: Supervisor

Implemented in:

- `src/multi_agent_research_lab/agents/supervisor.py`
- `src/multi_agent_research_lab/graph/workflow.py`

Routing policy:

```text
researcher -> analyst -> writer -> done
```

The supervisor checks missing state fields and records every route in `route_history`.

## Milestone 3: Worker Agents

Implemented in:

- `src/multi_agent_research_lab/agents/researcher.py`
- `src/multi_agent_research_lab/agents/analyst.py`
- `src/multi_agent_research_lab/agents/writer.py`

Researcher uses Tavily sources when available, Analyst structures reasoning, and Writer creates the final Vietnamese answer with citations.

## Milestone 4: Trace And Benchmark

Implemented in:

- `src/multi_agent_research_lab/evaluation/benchmark.py`
- `src/multi_agent_research_lab/evaluation/report.py`
- `src/multi_agent_research_lab/services/storage.py`

Run:

```bash
python -m multi_agent_research_lab.cli benchmark --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

Outputs:

- `reports/benchmark_report.md`
- `reports/traces/baseline.json`
- `reports/traces/multi_agent.json`

Metrics:

| Metric | How it is measured |
|---|---|
| Latency | Wall-clock time |
| Cost | Estimated from input/output token metadata |
| Quality | Deterministic 0-10 heuristic for lab comparison |
| Citation coverage | Cited source markers divided by source count |
| Failure rate | Errors recorded in state |

## Exit Ticket

1. Use multi-agent when the task needs source collection, explicit reasoning, handoff traceability, and a final answer with citations.
2. Avoid multi-agent for very short, low-risk tasks where orchestration overhead is larger than the benefit.
