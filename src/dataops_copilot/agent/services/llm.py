"""Shared helpers for Claude-backed investigation steps."""

from collections.abc import Callable
from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

DEFAULT_MODEL = "claude-opus-5-5"

type Effort = Literal["low", "medium", "high", "xhigh", "max"]


def make_chat_model(model: str = DEFAULT_MODEL, effort: Effort = "medium") -> ChatAnthropic:
    """Create the Claude chat model used by every investigation step.

    Thinking is always on for current Opus models; effort is the depth control.
    """
    return ChatAnthropic(model_name=model, max_tokens=16000, effort=effort)


def make_structured_call[T: BaseModel](
    llm: ChatAnthropic,
    schema: type[T],
    system_prompt: str,
) -> Callable[[str], T]:
    """Return a function that sends one user message and parses the reply into schema.

    Uses Claude's native structured outputs (`json_schema`) rather than forced
    tool calling, which current models reject.
    """
    structured_llm = llm.with_structured_output(schema, method="json_schema")

    def call(user_content: str) -> T:
        response = structured_llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_content)]
        )
        return schema.model_validate(response)

    return call


def available_columns(column_rates: dict[str, float]) -> str:
    """Render the dataset's column names for a prompt."""
    return ", ".join(sorted(column_rates)) or "(unknown)"
