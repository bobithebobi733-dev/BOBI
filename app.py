from flask import Flask, request, jsonify, render_template
import requests
import os
from datetime import date

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "llama-3.3-70b-versatile"

# PIN de acceso: se configura como variable de entorno BOBI_PIN en Render.
# Si la dejas vacía, cualquiera puede usar BOBI sin pedir PIN.
BOBI_PIN = os.environ.get("BOBI_PIN", "")

# PIN del creador: quien entre con este PIN NO tiene límite diario.
# Configúralo como variable de entorno BOBI_OWNER_PIN en Render (debe ser distinto al BOBI_PIN normal si lo usas).
BOBI_OWNER_PIN = os.environ.get("BOBI_OWNER_PIN", "")

# Límite diario de mensajes para todos los demás, para proteger la cuota gratis de Groq
LIMITE_DIARIO = 300
uso_diario = {"fecha": None, "contador": 0}

conversation_history = []

SYSTEM_PROMPT = (
    "Eres BOBI, un asistente de voz inspirado en Iron Man, y tu propósito es ser genuinamente útil "
    "en la mayor cantidad de temas posible: consejos prácticos del día a día, primeros auxilios básicos, "
    "cocina, tareas del hogar, tecnología, estudios, cultura general, y cualquier otra cosa que te pregunten. "
    "Responde SIEMPRE en español. "
    "No evites dar información básica y de sentido común solo porque el tema roce la salud, el dinero u otros temas delicados. "
    "Por ejemplo, si te preguntan cómo limpiar una herida pequeña, dales los pasos básicos "
    "(lavarse las manos, enjuagar con agua, desinfectar, cubrir), igual que lo haría un amigo con conocimientos generales. "
    "Solo recomienda ver a un profesional (médico, abogado, etc.) cuando el caso sea realmente serio, complejo, "
    "o quede claramente fuera de un consejo básico y general. "
    "Tu creador es Josué Francisco Atalaya Pineda, quien te programó. "
    "Si te preguntan quién te creó, quién te hizo o de dónde vienes, responde que fuiste creado por Josué Francisco Atalaya Pineda, "
    "nunca menciones a Meta, OpenAI, Groq, ni ninguna otra empresa como tu creador. "
    "Por defecto, responde en 2-4 frases cortas y directas, como si hablaras, no como si escribieras un ensayo. "
    "Evita listas largas, encabezados o explicaciones exhaustivas a menos que la persona te pida explícitamente 'explícame a detalle', 'paso a paso' o algo similar. "
    "Si te piden algo detallado, ahí sí puedes extenderte, pero organiza la idea en pocos puntos claros. "
    "Mantén un tono elegante y con un toque de personalidad ingeniosa, como el Jarvis de las películas."
)


def verificar_limite_diario():
    hoy = str(date.today())
    if uso_diario["fecha"] != hoy:
        uso_diario["fecha"] = hoy
        uso_diario["contador"] = 0
    uso_diario["contador"] += 1
    return uso_diario["contador"] <= LIMITE_DIARIO


@app.route("/")
def home():
    return render_template("index.html", pin_requerido=bool(BOBI_PIN))


@app.route("/chat", methods=["POST"])
def chat():
    pin_enviado = request.headers.get("X-BOBI-PIN", "")
    es_creador = bool(BOBI_OWNER_PIN) and pin_enviado == BOBI_OWNER_PIN

    # Verifica el PIN si está configurado (el PIN de creador también es válido para entrar)
    if BOBI_PIN and not es_creador:
        if pin_enviado != BOBI_PIN:
            return jsonify({"reply": "PIN incorrecto.", "pin_error": True}), 401

    # El creador no tiene límite diario
    if not es_creador and not verificar_limite_diario():
        return jsonify({"reply": "Se alcanzó el límite de mensajes por hoy. Intenta mañana."})

    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "No escuché nada, ¿puedes repetirlo?"})

    lower_msg = user_message.lower()
    palabras_creador = ["quién es tu creador", "quien es tu creador", "quién te creó", "quien te creo",
                         "quién te hizo", "quien te hizo", "de dónde vienes", "de donde vienes",
                         "cómo se llama tu creador", "como se llama tu creador", "quién te programó",
                         "quien te programo"]
    if any(frase in lower_msg for frase in palabras_creador):
        reply = "Fui creado por Josué Francisco Atalaya Pineda."
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    conversation_history.append({"role": "user", "content": user_message})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    if not GROQ_API_KEY:
        reply = "Falta configurar la API key de Groq en el servidor."
        return jsonify({"reply": reply})

    try:
        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL_NAME,
                "messages": messages,
            },
            timeout=60,
        )
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"]
        conversation_history.append({"role": "assistant", "content": reply})

        if len(conversation_history) > 20:
            del conversation_history[:2]

    except requests.exceptions.ConnectionError:
        reply = "No puedo conectarme al servicio de IA. Revisa tu conexión."
    except Exception as e:
        reply = f"Tuve un problema: {str(e)}"

    return jsonify({"reply": reply})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
