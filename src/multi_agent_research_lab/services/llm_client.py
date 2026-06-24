"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from dataclasses import dataclass
from time import sleep

from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.errors import ConfigurationError


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client skeleton."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion.

        Keep retry, timeout, and token logging here rather than inside agents.
        """

        provider = self.settings.llm_provider.lower()
        if provider != "gemini":
            raise ConfigurationError(f"Unsupported LLM_PROVIDER={self.settings.llm_provider!r}")

        return self._complete_with_gemini(system_prompt, user_prompt)

    def _complete_with_gemini(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        if not self.settings.gemini_api_key:
            raise ConfigurationError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")

        try:
            from google import genai
        except ImportError as exc:
            raise ConfigurationError(
                "Missing Gemini SDK. Install it with: pip install -e \".[llm,dev]\""
            ) from exc

        client = genai.Client(api_key=self.settings.gemini_api_key)
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=self.settings.gemini_model,
                    contents=user_prompt,
                    config={"system_instruction": system_prompt},
                )
                break
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    sleep(2**attempt)
        else:
            raise ConfigurationError(f"Gemini request failed: {last_error}") from last_error

        usage = getattr(response, "usage_metadata", None)
        input_tokens = getattr(usage, "prompt_token_count", None) if usage else None
        output_tokens = getattr(usage, "candidates_token_count", None) if usage else None

        return LLMResponse(
            content=response.text or "",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
