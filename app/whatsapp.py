"""
Cliente para enviar mensajes via Wati API.
"""

import os
import httpx


def _get_headers() -> dict:
    token = os.getenv("WATI_API_TOKEN")
    return {
        "Authorization": f"Bearer {token}",
    }


def _get_base_url() -> str:
    return os.getenv("WATI_BASE_URL", "").rstrip("/")


def send_text_message(to: str, text: str) -> dict:
    """
    Envía un mensaje de texto a un número de WhatsApp via Wati.

    Args:
        to: Número de destino con código de país, sin + (ej: 573001234567)
        text: Texto del mensaje
    """
    url = f"{_get_base_url()}/api/v1/sendSessionMessage/{to}"

    # Wati espera form-data, no JSON
    with httpx.Client(timeout=10.0) as client:
        response = client.post(url, data={"messageText": text}, headers=_get_headers())
        response.raise_for_status()
        return response.json()


def send_order_status_message(to: str, order_code: str, status: str) -> dict:
    """
    Envía una notificación de cambio de estado de pedido al cliente.
    """
    status_messages = {
        "confirmado": f"Tu pedido {order_code} fue confirmado. Pronto lo empezamos a preparar.",
        "preparando": f"Tu pedido {order_code} ya esta en preparacion.",
        "en_ruta": f"Tu pedido {order_code} esta en camino. Ya sale para tu direccion.",
        "entregado": f"Tu pedido {order_code} fue entregado. Gracias por elegir Mangova.",
        "cancelado": f"Tu pedido {order_code} fue cancelado. Si tenes dudas, escribinos.",
    }

    message = status_messages.get(
        status,
        f"Tu pedido {order_code} cambio de estado: {status}.",
    )

    return send_text_message(to, message)
