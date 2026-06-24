"""Domain-specific errors for the lab skeleton."""


class LabError(Exception):
    """Base error for the lab package."""


class StudentTodoError(LabError):
    """Raised where learners are expected to implement core logic."""


class AgentExecutionError(LabError):
    """Raised when an agent fails after retries/fallbacks."""


class ConfigurationError(LabError):
    """Raised when runtime settings are missing or unsupported."""


class ValidationError(LabError):
    """Raised when state or output validation fails."""
