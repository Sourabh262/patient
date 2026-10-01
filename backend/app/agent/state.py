from typing import Annotated, Sequence, TypedDict, Optional, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """LangGraph agent state containing conversational message history and structured context."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    patient_id: Optional[str]
    context_data: Optional[Dict[str, Any]]
    error: Optional[str]
