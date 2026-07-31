import speech_recognition as sr
import webbrowser
import time
import sounddevice as sd
import numpy as np

# Sitios conocidos (agrega más si quieres, en minúsculas)
SITIOS_CONOCIDOS = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "whatsapp": "https://web.whatsapp.com",
    "wasap": "https://web.whatsapp.com",
    "gmail": "https://mail.google.com",
    "netflix": "https://www.netflix.com",
    "twitter": "https://www.twitter.com",
    "tiktok": "https://www.tiktok.com",
    "amazon": "https://www.amazon.com",
    "spotify": "https://open.spotify.com",
}

PALABRA_ACTIVACION = "bobi"
DISPARADORES_ABRIR = ["abre", "abras", "abrir", "abriendo", "ábreme", "entra a", "entrar a", "ve a", "vete a"]

SAMPLE_RATE = 16000
SEGUNDOS_POR_BLOQUE = 4  # cuántos segundos graba antes de intentar reconocer

recognizer = sr.Recognizer()

print("=" * 50)
print("BOBI está escuchando en segundo plano...")
print("Di 'Oye BOBI, abre [sitio]' desde cualquier ventana.")
print("Presiona Ctrl+C en esta ventana para detenerlo.")
print("=" * 50)
print("¡Listo! Escuchando...")

while True:
    try:
        # Graba unos segundos de audio con el micrófono predeterminado de Windows
        grabacion = sd.rec(int(SEGUNDOS_POR_BLOQUE * SAMPLE_RATE),
                            samplerate=SAMPLE_RATE, channels=1, dtype='int16')
        sd.wait()

        # Convierte la grabación al formato que espera SpeechRecognition
        audio_bytes = grabacion.tobytes()
        audio_data = sr.AudioData(audio_bytes, SAMPLE_RATE, 2)

        try:
            texto = recognizer.recognize_google(audio_data, language="es-ES")
            texto_lower = texto.lower()
            print(f"Escuché: {texto}")

            if PALABRA_ACTIVACION in texto_lower:
                tiene_disparador = any(d in texto_lower for d in DISPARADORES_ABRIR)
                if tiene_disparador:
                    sitio_encontrado = None
                    for nombre, url in SITIOS_CONOCIDOS.items():
                        if nombre in texto_lower:
                            sitio_encontrado = (nombre, url)
                            break

                    if sitio_encontrado:
                        nombre, url = sitio_encontrado
                        print(f">>> Abriendo {nombre}...")
                        webbrowser.open(url)
                    else:
                        print(">>> Escuché 'BOBI abre' pero no reconocí el sitio.")

        except sr.UnknownValueError:
            pass  # No se entendió el audio (silencio o ruido), sigue escuchando
        except sr.RequestError as e:
            print(f"Error de conexión con el reconocimiento de voz: {e}")
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nBOBI dejó de escuchar. ¡Hasta luego!")
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(1)
