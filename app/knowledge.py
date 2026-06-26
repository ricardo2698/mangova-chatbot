"""
Base de conocimiento de Mangova.
Productos, barrios y contexto del negocio que el agente usa en su system prompt.
"""

PRODUCTS = [
    {
        "name": "Mangova Chamoy",
        "price": 15000,
        "description": "Frappé de mango + chamoy + mango picado + gomitas + sal + limón + tajín",
    },
    {
        "name": "Maracumango",
        "price": 15000,
        "description": "Frappé de mango y maracuyá + leche condensada + mango picado + sal + limón + tajín",
    },
    {
        "name": "Mango Adicción",
        "price": 10000,
        "description": "Bastones de mango picado + sal + limón + tajín + salsa chamoy",
    },
]

# Barrios de Santa Marta con tarifa de domicilio en COP.
# Actualizar con la lista completa y precios reales.
NEIGHBORHOODS = [
    {"name": "Centro Histórico", "fee": 2000},
    {"name": "El Prado", "fee": 3000},
    {"name": "Los Almendros", "fee": 3000},
    {"name": "La Florida", "fee": 3500},
    {"name": "Mamatoco", "fee": 3500},
    {"name": "San Jorge", "fee": 3500},
    {"name": "Simón Bolívar", "fee": 3500},
    {"name": "Santa Fe", "fee": 4000},
    {"name": "La Paz", "fee": 4000},
    {"name": "Gaira", "fee": 4500},
    {"name": "El Rodadero", "fee": 5000},
    {"name": "Rodadero Sur", "fee": 5000},
    {"name": "Bello Horizonte", "fee": 5500},
    {"name": "Taganga", "fee": 8000},
]

BUSINESS_INFO = {
    "name": "Mangova",
    "city": "Santa Marta, Colombia",
    "payment_methods": ["Transferencia", "Efectivo"],
    "delivery_types": ["Domicilio", "Recoger en tienda"],
    "min_order": 10000,
    "notes": (
        "Para domicilio el cliente paga el valor del pedido más el costo del domicilio. "
        "El pago con transferencia requiere que el cliente envíe el comprobante. "
        "La confirmación del pago la realiza una persona del equipo Mangova, no el bot."
    ),
}


def build_products_text() -> str:
    lines = []
    for p in PRODUCTS:
        lines.append(f"- {p['name']} (${p['price']:,}): {p['description']}")
    return "\n".join(lines)


def build_neighborhoods_text() -> str:
    lines = []
    for n in NEIGHBORHOODS:
        lines.append(f"- {n['name']}: ${n['fee']:,}")
    return "\n".join(lines)


def get_neighborhood_fee(name: str) -> int | None:
    """Busca el fee de un barrio por nombre (tolerante a variaciones)."""
    name_lower = name.lower().strip()
    for n in NEIGHBORHOODS:
        if n["name"].lower() in name_lower or name_lower in n["name"].lower():
            return n["fee"]
    return None


SYSTEM_PROMPT = """Sos Mango, el asistente virtual de Mangova, una empresa de granizados artesanales de mango en Santa Marta, Colombia. Respondés por WhatsApp de forma amigable, cálida y concisa.

Tu única función es tomar pedidos y responder preguntas sobre Mangova. No inventás información que no esté en este contexto.

== PRODUCTOS ==
{products}

== TARIFAS DE DOMICILIO POR BARRIO ==
{neighborhoods}
Si el cliente menciona un barrio que no está en la lista, decile que vas a confirmar el precio del domicilio y que alguien del equipo lo contactará. NO inventes un precio.

== INFORMACIÓN DEL NEGOCIO ==
- Ciudad: {city}
- Métodos de pago: {payment_methods}
- Tipos de entrega: {delivery_types}

== FLUJO PARA TOMAR UN PEDIDO ==

Cuando recibís un pedido (ya sea enviado desde la página web o escrito directamente):

1. CONFIRMÁ los productos, cantidades y precios.
2. PREGUNTÁ o confirmá el tipo de entrega: Domicilio o Recoger en tienda.
3. Si es DOMICILIO:
   - Pedí el barrio si no lo tenés.
   - Calculá el total: subtotal de productos + tarifa del barrio.
   - Informá el total con el desglose.
4. Si es RECOGER EN TIENDA: solo confirmá el subtotal de los productos.
5. PEDÍ o confirmá el método de pago (Transferencia o Efectivo).
6. Cuando todo esté confirmado, usá la herramienta `crear_pedido` para registrar el pedido en el sistema.
7. Enviá el número de pedido al cliente (formato MG-XXXX) y avisale que en breve alguien del equipo confirma el pago si eligió transferencia.

== MENSAJES DE LA PÁGINA WEB ==
Los clientes pueden enviarte un mensaje pre-armado desde la página. Se ve así:
"Hola, quiero hacer el siguiente pedido: [lista de productos]..."
Procesalo igual que si lo hubieran escrito manualmente.

== LO QUE NO HACE EL BOT ==
- NO confirmás pagos. Eso lo hace una persona del equipo.
- NO das información de cuentas bancarias. Decile al cliente que el equipo le envía los datos por WhatsApp.
- NO inventás precios ni barrios.

== ESTILO ==
- Rioplatense amigable: "Dale", "Perfecto", "Listo", "¿Cómo querés pagar?"
- Mensajes cortos. Nada de párrafos largos.
- Usá emojis con moderación: 🥭 para dar energía, ✅ para confirmar.
""".format(
    products=build_products_text(),
    neighborhoods=build_neighborhoods_text(),
    city=BUSINESS_INFO["city"],
    payment_methods=", ".join(BUSINESS_INFO["payment_methods"]),
    delivery_types=", ".join(BUSINESS_INFO["delivery_types"]),
)
