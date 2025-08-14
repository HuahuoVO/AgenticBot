from typing import Sequence, Annotated, TypedDict, List

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from langgraph.managed import IsLastStep, RemainingSteps
from pydantic.v1 import ListError


class AgenticBotState(TypedDict):
    variables: dict[str, str]
    available_vars: dict[str, str]
    messages: Annotated[Sequence[BaseMessage], add_messages]
    prev_reflect: List[str]
    plan: str
    is_last_step: IsLastStep

    remaining_steps: RemainingSteps
