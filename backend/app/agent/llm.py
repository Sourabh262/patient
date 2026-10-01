import re
import uuid
from typing import Any, List, Optional, Dict, Sequence
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    BaseMessage,
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatResult, ChatGeneration
from app.core.config import settings
from app.core.logging import logger


class MockClinicalChatModel(BaseChatModel):
    """High-fidelity deterministic Mock Chat Model for offline testing and local evaluation.
    Conforms to LangChain's BaseChatModel interface and produces structured tool calls
    based on intent recognition, or answers based on ToolMessage results.
    """

    model_name: str = "mock-clinical-agent"
    bound_tools: List[Any] = []

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        last_message = messages[-1] if messages else HumanMessage(content="")

        # If last message is a ToolMessage, summarize or conclude
        if isinstance(last_message, ToolMessage):
            tool_name = last_message.name
            tool_content = str(last_message.content)

            # Check if this was an intermediate step in a chain (e.g. send_email after calculate/get)
            # Find the user's initial prompt in the conversation
            user_msg = next((m.content for m in messages if isinstance(m, HumanMessage)), "")
            user_text_lower = user_msg.lower()

            # If user wanted to send email and we just finished calculating report or getting patient
            if "send" in user_text_lower and "email" in user_text_lower and tool_name != "send_email":
                # Find patient_id from tool_content or user text
                match = re.search(r"P\d{3}", user_msg, re.IGNORECASE)
                pid = match.group(0).upper() if match else "P015"
                call_id = f"call_{uuid.uuid4().hex[:8]}"
                ai_msg = AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "send_email",
                            "args": {"patient_id": pid},
                            "id": call_id,
                            "type": "tool_call",
                        }
                    ],
                )
                return ChatResult(generations=[ChatGeneration(message=ai_msg)])

            # Otherwise, form a comprehensive summary response
            if "not found" in tool_content.lower():
                response_text = f"I could not locate any records for the specified patient. Details: {tool_content}"
            elif tool_name == "get_patient":
                response_text = f"Here is the patient's information:\n\n{tool_content}"
            elif tool_name == "get_glucose_readings":
                response_text = f"Here is the patient's recent glucose telemetry:\n\n{tool_content}"
            elif tool_name in ("calculate_glucose_report", "generate_report"):
                response_text = f"Clinical 4-Week Glucose Report:\n\n{tool_content}"
            elif tool_name == "send_email":
                response_text = f"The patient report has been successfully dispatched via email:\n\n{tool_content}"
            else:
                response_text = f"Tool result for {tool_name}:\n{tool_content}"

            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=response_text))])

        # If user message, inspect intent and generate structured tool call
        user_text = last_message.content if isinstance(last_message.content, str) else str(last_message.content)
        user_lower = user_text.lower()

        # Extract patient ID (e.g. P015, P001, P999, etc.)
        match = re.search(r"\b(P\d+|PT[a-f0-9]+)\b", user_text, re.IGNORECASE)
        patient_id = match.group(0).upper() if match else None

        if not patient_id:
            # Check if user mentioned "patient 15" or similar
            num_match = re.search(r"patient\s*(\d+)", user_lower)
            if num_match:
                patient_id = f"P{int(num_match.group(1)):03d}"

        if not patient_id:
            return ChatResult(
                generations=[
                    ChatGeneration(
                        message=AIMessage(
                            content="Please provide a valid Patient ID (e.g., P015) so I can assist you with clinical records and glucose reports."
                        )
                    )
                ]
            )

        call_id = f"call_{uuid.uuid4().hex[:8]}"

        # Intent: Emailing report
        if any(w in user_lower for w in ["send", "mail", "email"]):
            ai_msg = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "send_email",
                        "args": {"patient_id": patient_id},
                        "id": call_id,
                        "type": "tool_call",
                    }
                ],
            )
        # Intent: Report generation / calculation / summary
        elif any(w in user_lower for w in ["report", "average", "stage", "summary", "trend", "last 4 weeks", "4 weeks"]):
            ai_msg = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "generate_report",
                        "args": {"patient_id": patient_id},
                        "id": call_id,
                        "type": "tool_call",
                    }
                ],
            )
        # Intent: Raw telemetry readings / glucose history
        elif any(w in user_lower for w in ["history", "readings", "telemetry", "glucose level"]):
            ai_msg = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_glucose_readings",
                        "args": {"patient_id": patient_id},
                        "id": call_id,
                        "type": "tool_call",
                    }
                ],
            )
        # Intent: Patient demographics / info
        elif any(w in user_lower for w in ["info", "information", "details", "patient", "who is"]):
            ai_msg = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_patient",
                        "args": {"patient_id": patient_id},
                        "id": call_id,
                        "type": "tool_call",
                    }
                ],
            )
        else:
            # Default to get_patient
            ai_msg = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_patient",
                        "args": {"patient_id": patient_id},
                        "id": call_id,
                        "type": "tool_call",
                    }
                ],
            )

        return ChatResult(generations=[ChatGeneration(message=ai_msg)])

    @property
    def _llm_type(self) -> str:
        return "mock-clinical-chat-model"

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> "MockClinicalChatModel":
        self.bound_tools = list(tools)
        return self


def get_llm(temperature: float = 0.0) -> BaseChatModel:
    """Returns the configured LLM instance with structured tool calling support."""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "openai" and settings.OPENAI_API_KEY:
        try:
            from langchain_openai import ChatOpenAI

            logger.info("Initializing OpenAI LLM with model %s", settings.OPENAI_MODEL)
            return ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=temperature,
                api_key=settings.OPENAI_API_KEY,
            )
        except Exception as e:
            logger.warning("Failed to initialize ChatOpenAI (%s). Falling back to mock model.", e)

    elif provider == "google" and settings.GOOGLE_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            logger.info("Initializing Google GenAI LLM")
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=temperature,
                google_api_key=settings.GOOGLE_API_KEY,
            )
        except Exception as e:
            logger.warning("Failed to initialize ChatGoogleGenerativeAI (%s). Falling back.", e)

    # Fallback to MockClinicalChatModel
    logger.info("Using MockClinicalChatModel for deterministic tool-calling execution.")
    return MockClinicalChatModel()
