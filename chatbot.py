import json
import random
from datetime import datetime

# Cargar dataset
with open("intents.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# Función para guardar logs
def guardar_log(usuario, bot, intent_tag):

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    linea = f"{timestamp} | Usuario: {usuario} | Intent: {intent_tag} | Bot: {bot}\n"

    with open("conversaciones.log", "a", encoding="utf-8") as log:
        log.write(linea)

# Detectar intención
def detectar_intencion(mensaje):

    mensaje = mensaje.lower()

    mensaje_tokens = mensaje.split()

    for intent in data["intents"]:

        for pattern in intent["patterns"]:

            for palabra in mensaje_tokens:

                if pattern in palabra:

                    return intent

    return None

# Responder
def responder(intent):

    return random.choice(intent["responses"])

# Contador de interacciones
contador_interacciones = 0

print("Chatbot iniciado. Escribí 'salir' para terminar.\n")

while True:

    mensaje_usuario = input("Vos: ")

    if mensaje_usuario.lower() == "salir":

        print("Bot: Hasta luego.")
        break

    intent = detectar_intencion(mensaje_usuario)

    contador_interacciones += 1

    if intent:

        respuesta = responder(intent)

        print("Bot:", respuesta)

        guardar_log(
            mensaje_usuario,
            respuesta,
            intent["tag"]
        )

    else:

        respuesta = "No entendí la consulta. ¿Podrías reformularla?"

        print("Bot:", respuesta)

        guardar_log(
            mensaje_usuario,
            respuesta,
            "desconocido"
        )

# Mostrar métricas al finalizar

print("\nSesión finalizada.")
print(f"Total de interacciones: {contador_interacciones}")
