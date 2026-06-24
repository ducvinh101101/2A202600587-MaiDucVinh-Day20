"""LangGraph workflow skeleton."""

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.state import ResearchState


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def __init__(self) -> None:
        self.supervisor = SupervisorAgent()
        self.agents = {
            "researcher": ResearcherAgent(),
            "analyst": AnalystAgent(),
            "writer": WriterAgent(),
        }

    def build(self) -> object:
        """Create a LangGraph graph.

        Return the executable node registry used by this lightweight starter workflow.
        """

        return {"supervisor": self.supervisor, **self.agents}

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state.

        A small deterministic graph runner: supervisor chooses the next route, then
        that worker mutates the shared state. This keeps the lab runnable before
        students replace it with LangGraph proper.
        """

        settings = get_settings()
        self.build()

        while state.iteration < settings.max_iterations:
            state = self.supervisor.run(state)
            next_route = state.route_history[-1]

            if next_route == "done":
                state.add_trace_event("workflow", {"status": "done"})
                return state

            agent = self.agents.get(next_route)
            if agent is None:
                raise AgentExecutionError(f"Unknown workflow route: {next_route}")

            try:
                state = agent.run(state)
            except Exception as exc:
                state.errors.append(f"{next_route}: {exc}")
                state.add_trace_event("workflow_error", {"route": next_route, "error": str(exc)})
                raise

        state.errors.append("Workflow stopped because MAX_ITERATIONS was reached.")
        state.add_trace_event("workflow", {"status": "max_iterations"})
        return state
