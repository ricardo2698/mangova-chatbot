"""Mangova customer-support chatbot.

A single-file LangChain app that loads Mangova's company profile + FAQ as a
knowledge base, injects it into the system prompt, and answers customer
questions using OpenAI's gpt-4.1-mini model.

Usage:
    export OPENAI_API_KEY="sk-..."
    python mangova_bot.py                       # interactive chat
    python mangova_bot.py "Are your juices vegan?"   # one-shot question
"""

from __future__ import annotations

import os
import sys
import textwrap

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

load_dotenv()

# ---------------------------------------------------------------------------
# Knowledge base: company profile + FAQ (sample data)
# ---------------------------------------------------------------------------

COMPANY_PROFILE = {
    "name": "Mangova",
    "tagline": "Jugos tropicales, exprimidos con alegría.",
    "description": textwrap.dedent(
        """
        Mangova es una empresa de bebidas de fruta tropical fundada en 2018 en
        Medellín, Colombia. Elaboramos jugos prensados en frío, smoothies y snacks
        de fruta con un amor especial por el mango. Cada botella se hace con fruta
        tropical madura y de origen sostenible, sin azúcar añadido y sin
        conservantes artificiales.
        """
    ).strip(),
    "mission": (
        "Llevar el sabor del trópico al día a día mientras pagamos precios justos "
        "a las pequeñas fincas que cultivan nuestra fruta."
    ),
    "products": [
        "Néctar de Mango Clásico (100% mango, prensado en frío)",
        "Smoothie de Mango y Maracuyá",
        "Refresco de Guayaba y Limón",
        "Jugo Espumoso de Piña y Jengibre",
        "Snacks de Mango Deshidratado",
        "Caja Mix Tropical (paquete variado de 12)",
    ],
    "values": [
        "Sin azúcar añadido, nunca.",
        "Comercio directo con pequeños agricultores.",
        "Botellas de vidrio 100% reciclables.",
        "Envíos con cero emisiones de carbono dentro del país.",
    ],
}

FAQ = [
    {
        "q": "¿De dónde provienen sus mangos?",
        "a": (
            "Nuestros mangos provienen de fincas familiares en las regiones del "
            "Tolima y el Magdalena, en Colombia. Compramos directamente a los "
            "agricultores bajo acuerdos de comercio justo."
        ),
    },
    {
        "q": "¿Sus jugos son veganos?",
        "a": (
            "Sí. Todos los jugos y snacks de Mangova son 100% de origen vegetal y "
            "aptos para veganos."
        ),
    },
    {
        "q": "¿Sus productos contienen azúcar añadido?",
        "a": (
            "No. Nunca añadimos azúcar refinada. Todo el dulzor proviene "
            "naturalmente de la propia fruta."
        ),
    },
    {
        "q": "¿Cuánto duran los jugos prensados en frío?",
        "a": (
            "Sin abrir, nuestros jugos prensados en frío duran 21 días "
            "refrigerados. Una vez abiertos, consúmelos en un plazo de 3 días para "
            "disfrutar del mejor sabor."
        ),
    },
    {
        "q": "¿Hacen envíos internacionales?",
        "a": (
            "Por ahora hacemos envíos en toda Colombia con entrega de cero "
            "emisiones de carbono. Los envíos internacionales llegan en 2026: "
            "suscríbete a nuestro boletín para enterarte."
        ),
    },
    {
        "q": "¿Las botellas son reciclables?",
        "a": (
            "Sí. Usamos botellas de vidrio 100% reciclables y ofrecemos un "
            "descuento del 10% por devolución de botellas cuando traes 6 envases "
            "vacíos a cualquier tienda asociada."
        ),
    },
    {
        "q": "¿Tienen opciones sin azúcar o keto?",
        "a": (
            "Todos nuestros jugos no tienen azúcar añadido, pero sí contienen "
            "azúcares naturales de la fruta. Para opciones más bajas en azúcar, "
            "nuestro Refresco de Guayaba y Limón y el Jugo Espumoso de Piña y "
            "Jengibre son los más ligeros de la línea."
        ),
    },
    {
        "q": "¿Cómo puedo convertirme en socio mayorista?",
        "a": (
            "Escríbenos a partners@mangova.example con los datos de tu negocio y te "
            "enviaremos nuestro catálogo y precios mayoristas en un plazo de 2 días "
            "hábiles."
        ),
    },
]


def build_knowledge_base() -> str:
    """Render the company profile + FAQ into a single text block for the prompt."""
    profile = COMPANY_PROFILE
    products = "\n".join(f"  - {p}" for p in profile["products"])
    values = "\n".join(f"  - {v}" for v in profile["values"])
    faq = "\n\n".join(
        f"P: {item['q']}\nR: {item['a']}" for item in FAQ
    )

    return textwrap.dedent(
        f"""
        ## Empresa: {profile['name']}
        Eslogan: {profile['tagline']}

        ### Descripción
        {profile['description']}

        ### Misión
        {profile['mission']}

        ### Productos
        {products}

        ### Valores
        {values}

        ### Preguntas Frecuentes
        {faq}
        """
    ).strip()


SYSTEM_PROMPT = textwrap.dedent(
    """
    Eres Mango, el amable asistente de atención al cliente de Mangova, una empresa
    de jugos tropicales. Usa ÚNICAMENTE la base de conocimiento de abajo para
    responder las preguntas de los clientes.

    Pautas:
    - Sé cálido, conciso y fiel a la marca (amamos los mangos y la buena energía).
    - Si la respuesta está en la base de conocimiento, respóndela directamente.
    - Si una pregunta no está cubierta por la base de conocimiento, di que no estás
      seguro y sugiere escribir a hello@mangova.example. No inventes información.
    - Responde siempre en español.
    - Mantén las respuestas breves, a menos que el cliente pida más detalle.

    === BASE DE CONOCIMIENTO DE MANGOVA ===
    {knowledge_base}
    === FIN DE LA BASE DE CONOCIMIENTO ===
    """
).strip()


def build_chain() -> ChatPromptTemplate | None:
    """Build the LangChain prompt | model chain."""
    knowledge_base = build_knowledge_base()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    ).partial(knowledge_base=knowledge_base)

    model = ChatOpenAI(model="gpt-4.1-mini", temperature=0.3)

    return prompt | model


def answer_once(question: str) -> str:
    chain = build_chain()
    response = chain.invoke({"question": question, "history": []})
    return response.content


def interactive() -> None:
    chain = build_chain()
    history: list = []

    print("🥭 Mango (Mangova support) — ask me anything. Type 'exit' to quit.\n")
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nThanks for stopping by. Stay juicy! 🥭")
            break

        if not question:
            continue
        if question.lower() in {"exit", "quit", "bye"}:
            print("Thanks for stopping by. Stay juicy! 🥭")
            break

        response = chain.invoke({"question": question, "history": history})
        print(f"\nMango: {response.content}\n")

        history.append(HumanMessage(content=question))
        history.append(AIMessage(content=response.content))


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit("Error: please set the OPENAI_API_KEY environment variable.")

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        print(answer_once(question))
    else:
        interactive()


if __name__ == "__main__":
    main()
