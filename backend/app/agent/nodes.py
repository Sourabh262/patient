import json
from typing import Dict, Any, List
from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
    AIMessage,
    ToolMessage,
)
from app.agent.state import AgentState
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.llm import get_llm
from app.agent.tools import ALL_AGENT_TOOLS, TOOLS_BY_NAME
from app.core.logging import logger


async def call_model_node(state: AgentState) -> Dict[str, Any]:
    """Invokes the configured LLM with system prompt and available tools."""
    llm = get_llm()
    bound_llm = llm.bind_tools(ALL_AGENT_TOOLS)

    messages = list(state.get("messages", []))

    # Prepend system prompt if not present
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    try:
        response = await bound_llm.ainvoke(messages)
        return {"messages": [response]}
    except Exception as e:
        logger.error("LLM execution error: %s", str(e))
        fallback_msg = AIMessage(
            content=f"An error occurred while communicating with the AI service: {str(e)}. Please retry or consult administrator."
        )
        return {"messages": [fallback_msg], "error": str(e)}


async def execute_tools_node(state: AgentState) -> Dict[str, Any]:
    """Executes requested tool calls safely with isolated error handling and typed responses."""
    messages = state.get("messages", [])
    if not messages:
        return {"messages": []}

    last_message = messages[-1]
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {"messages": []}

    tool_results: List[ToolMessage] = []

    for tool_call in last_message.tool_calls:
        name = tool_call.get("name")
        args = tool_call.get("args", {})
        call_id = tool_call.get("id", "call_id")

        tool_func = TOOLS_BY_NAME.get(name)
        if not tool_func:
            logger.warning("Agent requested unknown tool: %s", name)
            content = json.dumps({"error": f"Tool '{name}' is not recognized or permitted in this clinical environment."})
        else:
            try:
                logger.info("Executing tool %s with arguments: %s", name, args)
                content = await tool_func.ainvoke(args)
            except Exception as e:
                logger.error("Error executing tool %s: %s", name, str(e))
                content = json.dumps({"error": f"Failed executing tool '{name}': {str(e)}"})

        tool_results.append(ToolMessage(content=str(content), tool_call_id=call_id, name=name))

    return {"messages": tool_results}


def route_model_output(state: AgentState) -> str:
    """Evaluates whether the agent produced tool calls or should end the turn."""
    messages = state.get("messages", [])
    if not messages:
        return "__end__"

    last_message = messages[-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"

    return "__end__"
