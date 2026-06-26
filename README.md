# Chatbot de Mangova 🥭

Un pequeño chatbot de un solo archivo, hecho con LangChain + OpenAI, para
**Mangova**, una empresa (ficticia) de jugos tropicales. El perfil de la empresa
y las preguntas frecuentes están integrados en el *system prompt* como base de
conocimiento, de modo que el modelo responde las preguntas de los clientes
basándose en esos datos.

Construido con [LangChain](https://python.langchain.com/) y el modelo
`gpt-4.1-mini` de OpenAI (económico y rápido).

## Cómo funciona

1. `mangova_bot.py` define un **perfil de empresa** y unas **preguntas
   frecuentes (FAQ)** de ejemplo como datos de Python.
2. `build_knowledge_base()` los convierte en un bloque de texto.
3. Ese bloque de texto se inyecta en el **system prompt**.
4. Una cadena de LangChain `prompt | model` responde las preguntas del usuario,
   usando únicamente la base de conocimiento y evitando inventar información.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env             # luego coloca tu clave en .env
# (o: export OPENAI_API_KEY="sk-...")
```

La aplicación carga automáticamente el archivo `.env` mediante `python-dotenv`,
así que una vez que tu clave esté en `.env` no necesitas exportar nada.

## Uso

Chat interactivo:

```bash
python mangova_bot.py
```

Pregunta única:

```bash
python mangova_bot.py "¿Sus jugos son veganos?"
```

## Ejemplos de respuestas

Estas son respuestas reales generadas por el modelo actualmente:

> **Pregunta:** ¿De dónde vienen sus mangos?
>
> **Mango:** Nuestros mangos provienen de fincas familiares en las regiones del
> Tolima y el Magdalena, en Colombia. Compramos directamente a los agricultores
> bajo acuerdos de comercio justo. ¡Así apoyamos a las pequeñas fincas con mucho
> amor por el mango!

> **Pregunta:** ¿Cuánto duran los jugos prensados en frío?
>
> **Mango:** Sin abrir, nuestros jugos prensados en frío duran 21 días
> refrigerados. Una vez abiertos, consúmelos en un plazo de 3 días para
> disfrutar del mejor sabor. ¡Disfruta con alegría!

> **Pregunta:** ¿Tienen opciones bajas en azúcar?
>
> **Mango:** ¡Claro! Todos nuestros jugos no tienen azúcar añadido, solo el
> dulzor natural de la fruta. Para opciones más bajas en azúcar, te recomiendo
> el Refresco de Guayaba y Limón y el Jugo Espumoso de Piña y Jengibre, que son
> los más ligeros de nuestra línea. ¡Salud tropical!

> **Pregunta:** ¿Puedo comprar al por mayor?
>
> **Mango:** ¡Claro que sí! Para comprar al por mayor, escríbenos a
> partners@mangova.example con los datos de tu negocio y te enviaremos nuestro
> catálogo y precios mayoristas en un plazo de 2 días hábiles. ¡Gracias por
> querer compartir la alegría tropical!

> **Pregunta:** ¿Tienen tienda física en Bogotá? *(fuera de la base de
> conocimiento)*
>
> **Mango:** Hola, gracias por tu interés en Mangova. Por ahora no mencionamos
> tiendas físicas en Bogotá en nuestra base de conocimiento. Te sugiero escribir
> a hello@mangova.example para consultar sobre puntos de venta o tiendas
> físicas. ¡Un abrazo tropical!

## Personalizar la base de conocimiento

Edita las estructuras `COMPANY_PROFILE` y `FAQ` al inicio de `mangova_bot.py`.
No se necesita ningún otro cambio: el prompt se genera a partir de esos datos.
