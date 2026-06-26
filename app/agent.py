"""
Agente LangChain para Mangova.
Mantiene historial de conversación por número de teléfono (en memoria).
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import create_tool_calling_agent, AgentExecutor

from app.knowledge import SYSTEM_PROMPT
from app.tools import ALL_TOOLS

# Historial de conversación por número de teléfono.
# En producción esto debería persistirse en Redis o Firestore.
_sessions: dict[str, list] = {}

_model = ChatOpenAI(model="gpt-4.1-mini", temperature=0.3)

_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

_agent = create_tool_calling_agent(_model, ALL_TOOLS, _prompt)
_executor = AgentExecutor(agent=_agent, tools=ALL_TOOLS, verbose=False)


def process_message(phone: str, message: str) -> str:
    """
    Procesa un mensaje entrante de WhatsApp y retorna la respuesta del agente.

    Args:
        phone: Número de teléfono del cliente (ej: 573001234567)
        message: Texto del mensaje recibido

    Returns:
        Respuesta del agente como string
    """
    history = _sessions.get(phone, [])

    result = _executor.invoke({
        "input": message,
        "history": history,
    })

    response = result["output"]

    # Actualizar historial (máximo 20 turnos para no inflar el contexto)
    history.append(HumanMessage(content=message))
    history.append(AIMessage(content=response))
    if len(history) > 40:
        history = history[-40:]

    _sessions[phone] = history

    return response


def clear_session(phone: str) -> None:
    """Limpia el historial de conversación de un número."""
    _sessions.pop(phone, None)
