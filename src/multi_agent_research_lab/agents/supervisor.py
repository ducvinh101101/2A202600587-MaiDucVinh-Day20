"""Supervisor / router skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route.

        The starter policy is deliberately simple and inspectable:
        researcher -> analyst -> writer -> done.
        """

        settings = get_settings()
        if state.iteration >= settings.max_iterations:
            next_route = "done"
        elif not state.research_notes:
            next_route = "researcher"
        elif not state.analysis_notes:
            next_route = "analyst"
        elif not state.final_answer:
            next_route = "writer"
        else:
            next_route = "done"

        state.record_route(next_route)
        state.add_trace_event(self.name, {"next_route": next_route})
        return state
