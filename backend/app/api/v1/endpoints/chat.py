from fastapi import APIRouter, HTTPException, status
from app.schemas.chat import ChatRequest, ChatResponse
from app.agent.workflow import run_agent
from app.core.logging import logger

router = APIRouter()


@router.post("", response_model=ChatResponse, summary="Query the LangGraph clinical AI agent")
async def chat_with_agent(payload: ChatRequest):
    try:
        result = await run_agent(payload.message)
        # Convert messages to serializable format
        serializable_msgs = []
        for m in result.get("messages", []):
            serializable_msgs.append(
                {
                    "type": getattr(m, "type", "message"),
                    "content": getattr(m, "content", str(m)),
                }
            )

        return ChatResponse(
            response=result["response"],
            messages=serializable_msgs,
            error=result.get("error"),
        )
    except Exception as e:
        logger.error("Chat endpoint error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent error: {str(e)}",
        )
