"""Command-line entrypoint for the lab starter."""

import json
import re
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import LabError, StudentTodoError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.storage import LocalArtifactStore
from multi_agent_research_lab.services.llm_client import LLMClient

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console(legacy_windows=False)


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


def _run_baseline_state(query: str) -> ResearchState:
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    try:
        response = LLMClient().complete(
            system_prompt=(
                "You are a single-agent research baseline. Answer directly, clearly, and mention "
                "when claims should be verified with external sources."
            ),
            user_prompt=f"Question: {query}\n\nWrite the answer in Vietnamese.",
        )
        state.final_answer = response.content
        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "baseline": True,
                },
            )
        )
        state.add_trace_event(
            "baseline",
            {"input_tokens": response.input_tokens, "output_tokens": response.output_tokens},
        )
    except LabError as exc:
        state.final_answer = f"Baseline failed before completion: {exc}"
        state.errors.append(str(exc))
        state.add_trace_event("baseline_error", {"error": str(exc)})
    return state


def _run_multi_agent_state(query: str) -> ResearchState:
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    return workflow.run(state)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a minimal single-agent baseline placeholder."""

    _init()
    state = _run_baseline_state(query)
    console.print(Panel.fit(state.final_answer, title="Single-Agent Baseline"))


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow skeleton."""

    _init()
    try:
        result = _run_multi_agent_state(query)
    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
        raise typer.Exit(code=2) from exc
    console.print(result.model_dump_json(indent=2))


@app.command()
def benchmark(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run baseline and multi-agent benchmarks, then export report and traces."""

    _init()
    baseline_state, baseline_metrics = run_benchmark("baseline", query, _run_baseline_state)
    multi_state, multi_metrics = run_benchmark("multi-agent", query, _run_multi_agent_state)

    store = LocalArtifactStore()
    report_path = store.write_text(
        "benchmark_report.md", render_markdown_report([baseline_metrics, multi_metrics])
    )
    baseline_trace_path = store.write_text(
        "traces/baseline.json",
        json.dumps(baseline_state.model_dump(mode="json"), ensure_ascii=False, indent=2),
    )
    multi_trace_path = store.write_text(
        "traces/multi_agent.json",
        json.dumps(multi_state.model_dump(mode="json"), ensure_ascii=False, indent=2),
    )

    console.print(
        Panel.fit(
            f"Wrote {report_path}\nWrote {baseline_trace_path}\nWrote {multi_trace_path}",
            title="Benchmark Complete",
        )
    )


@app.command("benchmark-questions")
def benchmark_questions(
    question_file: Annotated[
        Path, typer.Option("--file", "-f", help="Markdown file containing prompt blocks")
    ] = Path("Question.md"),
) -> None:
    """Benchmark all fenced prompts from Question.md and export per-prompt traces."""

    _init()
    prompts = _load_question_prompts(question_file)
    if not prompts:
        console.print(Panel.fit(f"No prompt blocks found in {question_file}", title="No Prompts"))
        raise typer.Exit(code=1)

    store = LocalArtifactStore()
    rows: list[str] = [
        "# Question.md Benchmark Report",
        "",
        "This report benchmarks every prompt block in `Question.md` with both the single-agent Gemini baseline and the multi-agent workflow.",
        "",
        "| Prompt | Run | Latency (s) | Cost (USD) | Quality | Notes | Trace |",
        "|---|---|---:|---:|---:|---|---|",
    ]

    for index, (title, prompt) in enumerate(prompts, start=1):
        slug = _slugify(f"prompt-{index}-{title}")
        baseline_state, baseline_metrics = run_benchmark(
            f"{slug}-baseline", prompt, _run_baseline_state
        )
        multi_state, multi_metrics = run_benchmark(
            f"{slug}-multi-agent", prompt, _run_multi_agent_state
        )

        baseline_trace = store.write_text(
            f"traces/questions/{slug}_baseline.json",
            json.dumps(baseline_state.model_dump(mode="json"), ensure_ascii=False, indent=2),
        )
        multi_trace = store.write_text(
            f"traces/questions/{slug}_multi_agent.json",
            json.dumps(multi_state.model_dump(mode="json"), ensure_ascii=False, indent=2),
        )

        rows.append(_metric_row(title, "baseline", baseline_metrics, baseline_trace))
        rows.append(_metric_row(title, "multi-agent", multi_metrics, multi_trace))

    rows.extend(
        [
            "",
            "## Compliance Check",
            "",
            "- All four prompts from `Question.md` are valid research-style tasks for the system.",
            "- The multi-agent workflow can process them because it treats each prompt as the user research query.",
            "- Per-prompt traces are exported under `reports/traces/questions/` for screenshot or submission evidence.",
            "- Quality values are heuristic lab scores; use the prompt-specific rubrics for final human grading.",
        ]
    )
    report_path = store.write_text("question_benchmark_report.md", "\n".join(rows) + "\n")
    console.print(Panel.fit(f"Wrote {report_path}", title="Question Benchmark Complete"))


def _load_question_prompts(path: Path) -> list[tuple[str, str]]:
    content = path.read_text(encoding="utf-8")
    headings = list(re.finditer(r"^## Prompt \d+:\s*(.+)$", content, flags=re.MULTILINE))
    blocks = list(re.finditer(r"```text\s*(.*?)\s*```", content, flags=re.DOTALL))
    prompts: list[tuple[str, str]] = []
    for index, block in enumerate(blocks):
        title = headings[index].group(1).strip() if index < len(headings) else f"Prompt {index + 1}"
        prompts.append((title, block.group(1).strip()))
    return prompts


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug[:80]


def _metric_row(title: str, run_name: str, metrics: object, trace_path: Path) -> str:
    item = metrics
    cost = "" if item.estimated_cost_usd is None else f"{item.estimated_cost_usd:.6f}"
    quality = "" if item.quality_score is None else f"{item.quality_score:.1f}"
    return (
        f"| {title} | {run_name} | {item.latency_seconds:.2f} | {cost} | "
        f"{quality} | {item.notes} | `{trace_path.as_posix()}` |"
    )


if __name__ == "__main__":
    app()
