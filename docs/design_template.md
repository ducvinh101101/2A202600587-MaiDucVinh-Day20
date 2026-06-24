# Design Notes

## Problem

Build a research assistant that receives a user query, searches for relevant sources, extracts research notes, analyzes evidence, and writes a final Vietnamese answer with citations.

## Why multi-agent?

A single-agent baseline can answer quickly, but it mixes search, analysis, and writing in one prompt. The multi-agent design separates responsibilities so each step is easier to trace, debug, and evaluate. This is useful when the answer needs source grounding, explicit analysis, and a final synthesis.

## Agent Roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Route the workflow and stop safely | Shared `ResearchState` | Next route in `route_history` | Stops at `MAX_ITERATIONS` if state does not converge |
| Researcher | Search sources and create concise notes | Query, `max_sources` | `sources`, `research_notes` | Falls back to local source notes if search or LLM fails |
| Analyst | Extract findings, trade-offs, and evidence gaps | `research_notes` | `analysis_notes` | Falls back to simple structured notes |
| Writer | Produce final Vietnamese answer with citations | Query, notes, sources | `final_answer` | Falls back to available notes and source list |
| Critic | Optional lightweight quality check | Final state | Critic `AgentResult` | Reports missing answer, citation gaps, or workflow errors |

## Shared State

- `request`: original query, audience, and source limit.
- `iteration`: guardrail counter for workflow loops.
- `route_history`: explains which agent ran and in what order.
- `sources`: source documents from Tavily or local fallback.
- `research_notes`: evidence summary from the researcher.
- `analysis_notes`: structured reasoning from the analyst.
- `final_answer`: final response from the writer.
- `agent_results`: per-agent output plus token metadata.
- `trace`: local trace events for routing, token usage, and status.
- `errors`: non-fatal or fatal workflow issues.

## Routing Policy

```text
start
  -> supervisor
  -> researcher if research_notes is missing
  -> analyst if analysis_notes is missing
  -> writer if final_answer is missing
  -> done
```

The workflow stops immediately when all required fields exist or when `MAX_ITERATIONS` is reached.

## Guardrails

- Max iterations: configured by `MAX_ITERATIONS`, default `6`.
- Timeout: Tavily uses `TIMEOUT_SECONDS`; Gemini SDK has provider-level retry behavior.
- Retry: Gemini SDK retries transient requests; workflow can be rerun from CLI.
- Fallback: search falls back to local notes; agents fall back to intermediate state if Gemini fails.
- Validation: Pydantic schemas validate query length, source count, state fields, and metric ranges.

## Benchmark Plan

| Query | Metrics | Expected outcome |
|---|---|---|
| `Research GraphRAG state-of-the-art and write a 500-word summary` | latency, estimated cost, quality, citation coverage, failure count | Multi-agent should have better grounding and traceability, while baseline should be faster |
| `Giai thich ngan gon multi-agent system la gi` | latency, estimated cost, quality, citation coverage, failure count | Multi-agent should include sources and explicit analysis; baseline should answer directly |

## Failure Mode

Live Gemini requests can occasionally disconnect before sending a response. The LLM client wraps provider/network exceptions as `ConfigurationError`, and each agent catches `LabError` to write a fallback output. This keeps the workflow usable and makes the failure visible in `state.errors` and trace artifacts.
