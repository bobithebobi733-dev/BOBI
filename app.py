from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

# URL local donde corre Ollama (se inicia solo al abrir la app de Ollama)
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2"

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
    "nunca menciones a Meta, OpenAI, ni ninguna otra empresa como tu creador. "
    "Por defecto, responde en 2-4 frases cortas y directas, como si hablaras, no como si escribieras un ensayo. "
    "Evita listas largas, encabezados o explicaciones exhaustivas a menos que la persona te pida explícitamente 'explícame a detalle', 'paso a paso' o algo similar. "
    "Si te piden algo detallado, ahí sí puedes extenderte, pero organiza la idea en pocos puntos claros. "
    "Mantén un tono elegante y con un toque de personalidad ingeniosa, como el Jarvis de las películas."
)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "No escuché nada, ¿puedes repetirlo?"})

    # Respuesta fija para preguntas sobre el creador (evita que el modelo invente otra cosa)
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

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "stream": False,
            },
            timeout=180,
        )
        response.raise_for_status()
        reply = response.json()["message"]["content"]
        conversation_history.append({"role": "assistant", "content": reply})

        if len(conversation_history) > 20:
            del conversation_history[:2]

    except requests.exceptions.ConnectionError:
        reply = "No puedo conectarme a Ollama. Asegúrate de que la aplicación de Ollama esté abierta."
    except Exception as e:
        reply = f"Tuve un problema: {str(e)}"

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
