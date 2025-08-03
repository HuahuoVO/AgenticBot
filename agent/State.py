from langchain_core.tools import BaseTool
from langgraph.prebuilt.chat_agent_executor import AgentState


class AgenticBotState(AgentState):
    variable: dict[str, str]