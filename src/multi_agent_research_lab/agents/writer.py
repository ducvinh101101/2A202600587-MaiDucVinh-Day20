"""Writer agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import LabError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`.

        Synthesize a clear response with source references.
        """

        source_refs = "\n".join(
            f"[{index}] {source.title} - {source.url or 'local note'}"
            for index, source in enumerate(state.sources, start=1)
        )

        try:
            response = self.llm_client.complete(
                system_prompt=(
                    "You are the writer in a multi-agent research system. "
                    "Write a clear, grounded final answer for the requested audience."
                ),
                user_prompt=(
                    f"Question: {state.request.query}\n"
                    f"Audience: {state.request.audience}\n\n"
                    f"Research notes:\n{state.research_notes or ''}\n\n"
                    f"Analysis notes:\n{state.analysis_notes or ''}\n\n"
                    f"Sources:\n{source_refs}\n\n"
                    "Write the final answer in Vietnamese. Cite sources with [1], [2] when relevant."
                ),
            )
            final_answer = response.content
            metadata = {
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
            }
        except LabError as exc:
            final_answer = (
                f"Cau hoi: {state.request.query}\n\n"
                f"Tom tat nghien cuu:\n{state.research_notes or 'Chua co research notes.'}\n\n"
                f"Phan tich:\n{state.analysis_notes or 'Chua co analysis notes.'}\n\n"
                f"Nguon:\n{source_refs}"
            )
            metadata = {"fallback": True, "error": str(exc)}

        state.final_answer = final_answer
        state.agent_results.append(
            AgentResult(agent=AgentName.WRITER, content=final_answer, metadata=metadata)
        )
        state.add_trace_event(self.name, metadata)
        return state
