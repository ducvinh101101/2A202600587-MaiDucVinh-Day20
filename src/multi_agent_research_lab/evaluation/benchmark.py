"""Benchmark skeleton for single-agent vs multi-agent."""

from time import perf_counter
from typing import Callable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState


Runner = Callable[[str], ResearchState]


def run_benchmark(run_name: str, query: str, runner: Runner) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency, cost, quality heuristic, citation coverage, and errors."""

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started
    input_tokens, output_tokens = _token_usage(state)
    citation_coverage = _citation_coverage(state)
    error_rate = 1.0 if state.errors else 0.0
    quality, quality_breakdown = _quality_score(state, citation_coverage, error_rate)
    estimated_cost = _estimate_gemini_flash_cost(input_tokens, output_tokens)
    notes = (
        f"tokens in/out={input_tokens}/{output_tokens}; "
        f"citation_coverage={citation_coverage:.2f}; errors={len(state.errors)}; "
        f"rubric={quality_breakdown}"
    )
    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=estimated_cost,
        quality_score=quality,
        notes=notes,
    )
    return state, metrics


def _token_usage(state: ResearchState) -> tuple[int, int]:
    input_tokens = 0
    output_tokens = 0
    for result in state.agent_results:
        input_tokens += int(result.metadata.get("input_tokens") or 0)
        output_tokens += int(result.metadata.get("output_tokens") or 0)
    return input_tokens, output_tokens


def _estimate_gemini_flash_cost(input_tokens: int, output_tokens: int) -> float:
    """Rough estimate for inexpensive Gemini Flash-family models.

    The exact rate depends on model/date/account. This keeps benchmark comparisons
    reproducible by using a documented assumption in the generated report.
    """

    input_rate_per_million = 0.10
    output_rate_per_million = 0.40
    return (input_tokens / 1_000_000 * input_rate_per_million) + (
        output_tokens / 1_000_000 * output_rate_per_million
    )


def _citation_coverage(state: ResearchState) -> float:
    if not state.final_answer:
        return 0.0
    if not state.sources:
        return 0.0
    cited = sum(1 for index in range(1, len(state.sources) + 1) if f"[{index}]" in state.final_answer)
    return cited / len(state.sources)


def _quality_score(
    state: ResearchState, citation_coverage: float, error_rate: float
) -> tuple[float, str]:
    """Weighted research-quality proxy.

    This mirrors a practical human/LLM-judge rubric while staying deterministic
    for local lab runs. For formal evaluation, replace each component with a
    human or LLM judge score using the same weights.
    """

    components = {
        "correctness": _correctness_proxy(state, error_rate),
        "source_grounding": min(citation_coverage * 10.0, 10.0),
        "completeness": _completeness_proxy(state),
        "research_judgment": _research_judgment_proxy(state),
        "clarity": _clarity_proxy(state),
        "constraint_following": _constraint_following_proxy(state),
    }
    weights = {
        "correctness": 0.25,
        "source_grounding": 0.20,
        "completeness": 0.20,
        "research_judgment": 0.15,
        "clarity": 0.10,
        "constraint_following": 0.10,
    }
    score = sum(components[name] * weights[name] for name in components)
    breakdown = ",".join(f"{name}:{components[name]:.1f}" for name in components)
    return max(0.0, min(10.0, score)), breakdown


def _correctness_proxy(state: ResearchState, error_rate: float) -> float:
    if not state.final_answer:
        return 0.0
    score = 7.0
    if state.sources:
        score += 1.0
    if state.research_notes and state.analysis_notes:
        score += 1.0
    score -= error_rate * 4.0
    return max(0.0, min(10.0, score))


def _completeness_proxy(state: ResearchState) -> float:
    if not state.final_answer:
        return 0.0
    answer = state.final_answer
    score = 4.0
    if len(answer) >= 600:
        score += 2.0
    if len(answer) >= 1200:
        score += 1.0
    if state.research_notes:
        score += 1.0
    if state.analysis_notes:
        score += 1.0
    if state.sources:
        score += 1.0
    return min(10.0, score)


def _research_judgment_proxy(state: ResearchState) -> float:
    text = " ".join(
        part or "" for part in [state.research_notes, state.analysis_notes, state.final_answer]
    ).lower()
    signals = [
        "trade-off",
        "tradeoff",
        "uncertain",
        "uncertainty",
        "limitation",
        "evidence gap",
        "failure",
        "risk",
        "benchmark",
        "caveat",
        "hạn chế",
        "rủi ro",
    ]
    score = 4.0 + min(6, sum(1 for signal in signals if signal in text))
    return min(10.0, score)


def _clarity_proxy(state: ResearchState) -> float:
    if not state.final_answer:
        return 0.0
    answer = state.final_answer
    score = 5.0
    if "\n" in answer:
        score += 1.0
    if any(marker in answer for marker in ["#", "-", "*", "1."]):
        score += 2.0
    if 500 <= len(answer) <= 6000:
        score += 2.0
    return min(10.0, score)


def _constraint_following_proxy(state: ResearchState) -> float:
    if not state.final_answer:
        return 0.0
    query = state.request.query.lower()
    answer = state.final_answer.lower()
    score = 7.0
    if "output format" in query and any(marker in answer for marker in ["core question", "main positions", "section", "rubric"]):
        score += 1.0
    if "must include" in query and len(answer) >= 1000:
        score += 1.0
    if state.errors:
        score -= 2.0
    return max(0.0, min(10.0, score))
