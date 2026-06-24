"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown."""

    lines = [
        "# Benchmark Report",
        "",
        "This report compares a single-agent Gemini baseline with the multi-agent workflow.",
        "Cost is estimated from token usage with a fixed local assumption: $0.10/M input tokens and $0.40/M output tokens.",
        "Quality uses a weighted research rubric: 25% correctness, 20% source grounding, 20% completeness, 15% research judgment, 10% clarity, and 10% constraint following.",
        "The current implementation uses deterministic proxy scores for each rubric component. For a formal study, replace those proxies with human or LLM-judge scores using the same weights.",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality | Notes |",
        "|---|---:|---:|---:|---|",
    ]
    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"{item.estimated_cost_usd:.6f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}"
        lines.append(f"| {item.run_name} | {item.latency_seconds:.2f} | {cost} | {quality} | {item.notes} |")
    lines.extend(
        [
            "",
            "## Trace Artifacts",
            "",
            "- Single-agent trace/output: `reports/traces/baseline.json`",
            "- Multi-agent trace/output: `reports/traces/multi_agent.json`",
            "",
            "## Failure Mode and Fix",
            "",
            "During live testing, Gemini occasionally disconnected before sending a response. "
            "The fix wraps provider/network exceptions inside the LLM client and lets each agent "
            "fall back to the best available intermediate notes instead of crashing the workflow.",
            "",
            "Tavily search can also fail because of network or quota issues. The search client falls "
            "back to deterministic local source notes so the lab can still demonstrate routing, "
            "state handoff, tracing, and final synthesis.",
        ]
    )
    return "\n".join(lines) + "\n"
