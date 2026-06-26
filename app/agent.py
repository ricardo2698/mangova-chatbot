"""
Agente LangChain para Mangova.
Mantiene historial de conversación por número de teléfono (en memoria).
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from app.knowledge import SYSTEM_PROMPT
from app.tools import ALL_TOOLS

# Historial de conversación por número de teléfono.
# En producción esto debería persistirse en Firestore.
_sessions: dict[str, list] = {}

_model = ChatOpenAI(model="gpt-4.1-mini", temperature=0.3)
_graph = create_react_agent(_model, ALL_TOOLS)


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

    messages = (
        [SystemMessage(content=SYSTEM_PROMPT)]
        + history
        + [HumanMessage(content=message)]
    )

    result = _graph.invoke({"messages": messages})
    response = result["messages"][-1].content

    # Actualizar historial (máximo 20 turnos)
    history.append(HumanMessage(content=message))
    history.append(AIMessage(content=response))
    if len(history) > 40:
        history = history[-40:]

    _sessions[phone] = history
    return response


def clear_session(phone: str) -> None:
    """Limpia el historial de conversación de un número."""
    _sessions.pop(phone, None)
