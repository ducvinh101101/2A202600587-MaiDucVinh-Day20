"""Researcher agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import LabError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(
        self, search_client: SearchClient | None = None, llm_client: LLMClient | None = None
    ) -> None:
        self.search_client = search_client or SearchClient()
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`.

        Search first, then ask the LLM to compress sources into usable notes.
        """

        sources = self.search_client.search(state.request.query, state.request.max_sources)
        state.sources = sources
        source_text = "\n".join(
            f"- {source.title}: {source.snippet} ({source.url or 'no url'})" for source in sources
        )

        try:
            response = self.llm_client.complete(
                system_prompt=(
                    "You are the researcher in a multi-agent research system. "
                    "Extract concise, evidence-grounded notes from the provided sources."
                ),
                user_prompt=(
                    f"Research question: {state.request.query}\n\n"
                    f"Sources:\n{source_text}\n\n"
                    "Return 5-8 bullet notes. Mention uncertainty when evidence is weak."
                ),
            )
            notes = response.content
            metadata = {
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
            }
        except LabError as exc:
            notes = f"LLM unavailable, using source snippets directly.\n{source_text}"
            metadata = {"fallback": True, "error": str(exc)}

        state.research_notes = notes
        state.agent_results.append(
            AgentResult(agent=AgentName.RESEARCHER, content=notes, metadata=metadata)
        )
        state.add_trace_event(self.name, {"sources": len(sources), **metadata})
        return state
