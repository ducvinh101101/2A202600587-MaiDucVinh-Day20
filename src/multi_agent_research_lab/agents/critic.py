"""Optional critic agent skeleton for bonus work."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append lightweight findings."""

        findings: list[str] = []
        if not state.final_answer:
            findings.append("Missing final answer.")
        if state.sources and state.final_answer:
            cited = sum(
                1 for index in range(1, len(state.sources) + 1) if f"[{index}]" in state.final_answer
            )
            findings.append(f"Citation coverage: {cited}/{len(state.sources)} sources cited.")
        if state.errors:
            findings.append(f"Workflow reported {len(state.errors)} errors.")
        if not findings:
            findings.append("No blocking quality issues found by the lightweight critic.")

        content = "\n".join(f"- {finding}" for finding in findings)
        state.agent_results.append(
            AgentResult(agent=AgentName.CRITIC, content=content, metadata={"lightweight": True})
        )
        state.add_trace_event(self.name, {"findings": len(findings)})
        return state
