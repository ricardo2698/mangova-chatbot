"""
Cliente de Firestore usando Firebase Admin SDK.
Se inicializa una sola vez (singleton) para no crear múltiples apps.
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone

_db = None


def get_db():
    global _db
    if _db is not None:
        return _db

    if not firebase_admin._apps:
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_path:
            cred = credentials.Certificate(cred_path)
        else:
            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": os.getenv("FIREBASE_PROJECT_ID"),
                "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
                "token_uri": "https://oauth2.googleapis.com/token",
            })
        firebase_admin.initialize_app(cred)

    _db = firestore.client()
    return _db


def get_next_order_code() -> str:
    """Genera el siguiente código MG-XXXX usando el contador en Firestore."""
    db = get_db()
    counter_ref = db.collection("mangova_counters").document("orders")

    @firestore.transactional
    def increment(transaction, ref):
        snapshot = ref.get(transaction=transaction)
        current = snapshot.get("count") if snapshot.exists else 0
        next_val = current + 1
        transaction.set(ref, {"count": next_val})
        return next_val

    transaction = db.transaction()
    number = increment(transaction, counter_ref)
    return f"MG-{number:04d}"


def create_mangova_order(
    items: list[dict],
    delivery_type: str,
    payment_method: str,
    customer_name: str,
    customer_phone: str,
    neighborhood: str = "",
    address: str = "",
    delivery_fee: int = 0,
    subtotal: int = 0,
    total: int = 0,
) -> dict:
    """Crea un pedido en mangova_orders y retorna el documento creado."""
    db = get_db()
    order_code = get_next_order_code()

    order_data = {
        "orderCode": order_code,
        "items": items,
        "deliveryType": delivery_type,
        "paymentMethod": payment_method,
        "customerName": customer_name,
        "customerPhone": customer_phone,
        "neighborhood": neighborhood,
        "address": address,
        "deliveryFee": delivery_fee,
        "subtotal": subtotal,
        "total": total,
        "status": "pendiente",
        "source": "whatsapp_bot",
        "createdAt": datetime.now(timezone.utc),
    }

    db.collection("mangova_orders").document(order_code).set(order_data)
    return {**order_data, "orderCode": order_code}


def get_order_by_code(order_code: str) -> dict | None:
    """Busca un pedido por su código MG-XXXX."""
    db = get_db()
    doc = db.collection("mangova_orders").document(order_code.upper()).get()
    if doc.exists:
        return doc.to_dict()
    return None


def get_latest_order_by_phone(phone: str) -> dict | None:
    """Busca el pedido más reciente de un número de teléfono."""
    db = get_db()
    docs = (
        db.collection("mangova_orders")
        .where("customerPhone", "==", phone)
        .order_by("createdAt", direction=firestore.Query.DESCENDING)
        .limit(1)
        .stream()
    )
    for doc in docs:
        return doc.to_dict()
    return None
