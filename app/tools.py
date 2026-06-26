"""
Herramientas (tools) que el agente LangChain puede invocar.
Cada tool es una función decorada con @tool de langchain_core.
"""

import json
from langchain_core.tools import tool
from app.knowledge import get_neighborhood_fee, NEIGHBORHOODS, PRODUCTS
from app.firestore_client import (
    create_mangova_order,
    get_order_by_code,
    get_latest_order_by_phone,
)


@tool
def obtener_fee_domicilio(barrio: str) -> str:
    """
    Retorna la tarifa de domicilio para un barrio de Santa Marta.
    Si el barrio no está en la lista, retorna un mensaje indicando que no se encontró.

    Args:
        barrio: Nombre del barrio o sector del cliente.
    """
    fee = get_neighborhood_fee(barrio)
    if fee is not None:
        return f"La tarifa de domicilio para {barrio} es ${fee:,} COP."
    barrio_list = ", ".join(n["name"] for n in NEIGHBORHOODS)
    return (
        f"No encontré '{barrio}' en la lista de barrios con tarifa definida. "
        f"Los barrios disponibles son: {barrio_list}. "
        "Si el barrio del cliente no está, indicale que alguien del equipo le confirmará el precio del domicilio."
    )


@tool
def crear_pedido(
    items_json: str,
    delivery_type: str,
    payment_method: str,
    customer_name: str,
    customer_phone: str,
    neighborhood: str = "",
    address: str = "",
) -> str:
    """
    Registra un pedido confirmado en Firestore y retorna el código de pedido.
    Usá esta herramienta SOLO cuando el cliente haya confirmado todos los detalles.

    Args:
        items_json: Lista de items en formato JSON. Ejemplo:
                    '[{"name": "Mangova Chamoy", "quantity": 2, "price": 15000}]'
        delivery_type: "domicilio" o "tienda"
        payment_method: "Transferencia" o "Efectivo"
        customer_name: Nombre del cliente
        customer_phone: Número de WhatsApp del cliente (con código de país, ej: 573001234567)
        neighborhood: Barrio (solo para domicilio)
        address: Dirección exacta (solo para domicilio)
    """
    try:
        items = json.loads(items_json)
    except json.JSONDecodeError:
        return "Error: items_json no es un JSON válido."

    subtotal = sum(i.get("price", 0) * i.get("quantity", 1) for i in items)
    delivery_fee = 0

    if delivery_type == "domicilio" and neighborhood:
        fee = get_neighborhood_fee(neighborhood)
        delivery_fee = fee if fee is not None else 0

    total = subtotal + delivery_fee

    order = create_mangova_order(
        items=items,
        delivery_type=delivery_type,
        payment_method=payment_method,
        customer_name=customer_name,
        customer_phone=customer_phone,
        neighborhood=neighborhood,
        address=address,
        delivery_fee=delivery_fee,
        subtotal=subtotal,
        total=total,
    )

    return (
        f"Pedido creado exitosamente.\n"
        f"Código: {order['orderCode']}\n"
        f"Subtotal: ${subtotal:,}\n"
        f"Domicilio: ${delivery_fee:,}\n"
        f"Total: ${total:,}\n"
        f"Estado: {order['status']}"
    )


@tool
def consultar_pedido(identificador: str, customer_phone: str = "") -> str:
    """
    Consulta el estado de un pedido por código MG-XXXX o por el teléfono del cliente.

    Args:
        identificador: Código del pedido (MG-XXXX) o "ultimo" para buscar por teléfono.
        customer_phone: Teléfono del cliente. Requerido si identificador es "ultimo".
    """
    if identificador.upper().startswith("MG-"):
        order = get_order_by_code(identificador)
    elif identificador.lower() == "ultimo" and customer_phone:
        order = get_latest_order_by_phone(customer_phone)
    else:
        return "No pude identificar el pedido. Pedile al cliente el código MG-XXXX o consultá por su teléfono."

    if not order:
        return "No encontré ningún pedido con esa información."

    status_labels = {
        "pendiente": "Pendiente de confirmación",
        "confirmado": "Confirmado",
        "preparando": "En preparación",
        "en_ruta": "En ruta",
        "entregado": "Entregado",
        "cancelado": "Cancelado",
    }
    status = status_labels.get(order.get("status", ""), order.get("status", ""))

    items_text = ", ".join(
        f"{i.get('quantity', 1)}x {i.get('name', '')}" for i in order.get("items", [])
    )

    return (
        f"Pedido {order.get('orderCode')}\n"
        f"Estado: {status}\n"
        f"Productos: {items_text}\n"
        f"Total: ${order.get('total', 0):,}\n"
        f"Entrega: {order.get('deliveryType')}"
    )


ALL_TOOLS = [obtener_fee_domicilio, crear_pedido, consultar_pedido]
