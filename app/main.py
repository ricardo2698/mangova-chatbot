"""
Servidor FastAPI — punto de entrada del bot de Mangova.

Endpoints:
  POST /webhook        — mensajes entrantes desde Wati
  POST /notify/status  — llamado por el dashboard para notificar cambios de estado
  GET  /health         — healthcheck
"""

import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from app.agent import process_message
from app.whatsapp import send_text_message, send_order_status_message

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Mangova WhatsApp Bot")


# ---------------------------------------------------------------------------
# Webhook — mensajes entrantes desde Wati
# ---------------------------------------------------------------------------

@app.post("/webhook")
async def receive_message(body: dict):
    """
    Wati envía aquí cada mensaje que llega al número de WhatsApp.

    Payload de Wati:
    {
      "text": "hola quiero pedir",
      "type": "text",
      "waId": "573001234567",
      "owner": false,        <- false = mensaje del cliente, true = del agente
      "senderName": "Juan",
      ...
    }
    """
    try:
        # Solo procesamos mensajes del cliente (owner: false)
        if body.get("owner", True):
            return {"status": "ignored"}

        msg_type = body.get("type", "")

        # Solo texto por ahora
        if msg_type != "text":
            from_phone = body.get("waId", "")
            if from_phone:
                send_text_message(
                    to=from_phone,
                    text="Por el momento solo proceso mensajes de texto. Escribime tu pedido y te ayudo enseguida.",
                )
            return {"status": "ignored"}

        from_phone = body.get("waId", "")
        text = body.get("text", "").strip()

        if not from_phone or not text:
            return {"status": "ignored"}

        logger.info(f"Mensaje de {from_phone}: {text[:80]}")

        response = process_message(phone=from_phone, message=text)

        send_text_message(to=from_phone, text=response)

        logger.info(f"Respuesta enviada a {from_phone}: {response[:80]}")

    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Notificaciones de estado desde el dashboard (Next.js → este servidor)
# ---------------------------------------------------------------------------

class StatusNotification(BaseModel):
    customer_phone: str
    order_code: str
    status: str


@app.post("/notify/status")
async def notify_order_status(notification: StatusNotification):
    """
    El dashboard llama a este endpoint cuando cambia el estado de un pedido.
    El bot envía un mensaje al cliente informando el nuevo estado.
    """
    try:
        send_order_status_message(
            to=notification.customer_phone,
            order_code=notification.order_code,
            status=notification.status,
        )
        return {"status": "sent"}
    except Exception as e:
        logger.error(f"Error al notificar estado: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Healthcheck
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "service": "mangova-bot"}
