from typing import List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from app.agent.state import AgentState
from app.agent.nodes import call_model_node, execute_tools_node, route_model_output
from app.core.logging import logger


def build_clinical_graph():
    """Builds and compiles the LangGraph agent state graph."""
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("agent", call_model_node)
    graph.add_node("tools", execute_tools_node)

    # Set start
    graph.set_entry_point("agent")

    # Routing
    graph.add_conditional_edges(
        "agent",
        route_model_output,
        {
            "tools": "tools",
            "__end__": END,
        },
    )

    # Tool execution loops back to agent for synthesis
    graph.add_edge("tools", "agent")

    return graph.compile()


clinical_agent = build_clinical_graph()


async def run_agent(
    user_query: str,
    chat_history: Optional[List[BaseMessage]] = None,
) -> Dict[str, Any]:
    """Runs the LangGraph clinical agent with conversational history."""
    messages: List[BaseMessage] = list(chat_history or [])
    messages.append(HumanMessage(content=user_query))

    initial_state: AgentState = {
        "messages": messages,
        "patient_id": None,
        "context_data": {},
        "error": None,
    }

    try:
        final_state = await clinical_agent.ainvoke(initial_state)
        final_messages = final_state.get("messages", [])
        last_message = final_messages[-1] if final_messages else AIMessage(content="No response generated.")

        return {
            "response": last_message.content,
            "messages": final_messages,
            "error": final_state.get("error"),
        }
    except Exception as e:
        logger.error("Error executing clinical agent workflow: %s", str(e))
        return {
            "response": f"Encountered an internal error processing request: {str(e)}",
            "messages": messages,
            "error": str(e),
        }
