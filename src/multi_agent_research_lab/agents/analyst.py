"""Analyst agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import LabError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`.

        Extract key claims, trade-offs, and weak evidence from research notes.
        """

        research_notes = state.research_notes or "No research notes available."

        try:
            response = self.llm_client.complete(
                system_prompt=(
                    "You are the analyst in a multi-agent research system. "
                    "Turn research notes into structured reasoning."
                ),
                user_prompt=(
                    f"Question: {state.request.query}\n\n"
                    f"Research notes:\n{research_notes}\n\n"
                    "Return: key findings, disagreements/trade-offs, evidence gaps, and suggested answer."
                ),
            )
            analysis = response.content
            metadata = {
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
            }
        except LabError as exc:
            analysis = (
                "LLM unavailable, using a simple analysis fallback.\n"
                f"Key material:\n{research_notes}\n\n"
                "Evidence gap: verify sources and recency before final submission."
            )
            metadata = {"fallback": True, "error": str(exc)}

        state.analysis_notes = analysis
        state.agent_results.append(
            AgentResult(agent=AgentName.ANALYST, content=analysis, metadata=metadata)
        )
        state.add_trace_event(self.name, metadata)
        return state
