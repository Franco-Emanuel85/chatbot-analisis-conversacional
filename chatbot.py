import json
import random
from datetime import datetime
from ab_testing import ABTesting

# Cargar dataset
with open("intents.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# Inicializar sistema de A/B testing
ab = ABTesting()

# Función para guardar logs
def guardar_log(usuario, bot, intent_tag, variant=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if variant:
        linea = f"{timestamp} | Usuario: {usuario} | Intent: {intent_tag} | Variant: {variant} | Bot: {bot}\n"
    else:
        linea = f"{timestamp} | Usuario: {usuario} | Intent: {intent_tag} | Bot: {bot}\n"

    with open("conversaciones.log", "a", encoding="utf-8") as log:
        log.write(linea)

# Detectar intención
def detectar_intencion(mensaje):
    mensaje = mensaje.lower()

    for intent in data["intents"]:
        for pattern in intent["patterns"]:
            if pattern in mensaje:
                return intent

    return None

# Responder con soporte A/B testing
def responder_con_ab(intent, session_id):
    responses = intent["responses"]
    tag = intent["tag"]

    if len(responses) <= 1:
        return responses[0], 0, None

    variant_index = ab.assign_variant(session_id, tag, len(responses))
    respuesta = responses[variant_index]
    variant_letter = chr(65 + variant_index)

    return respuesta, variant_index, variant_letter

# Contador de interacciones
contador_interacciones = 0

print("Chatbot iniciado. Escribí 'salir' para terminar.")
print("Comandos especiales: 'reporte' para ver resultados A/B, 'sesion' para ver ID de sesión, 'nueva_sesion' para cambiar de sesión\n")

# Generar ID de sesión único para esta ejecución
session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
print(f"ID de sesión: {session_id}\n")

while True:
    mensaje_usuario = input("Vos: ")

    if mensaje_usuario.lower() == "salir":
        print("Bot: Hasta luego.")
        break

    if mensaje_usuario.lower() == "reporte":
        for intent in data["intents"]:
            if len(intent["responses"]) > 1:
                ab.print_report(intent["tag"])
        continue

    if mensaje_usuario.lower() == "sesion":
        print(f"ID de sesión: {session_id}")
        continue

    if mensaje_usuario.lower() == "nueva_sesion":
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"Nuevo ID de sesión: {session_id}")
        continue

    intent = detectar_intencion(mensaje_usuario)

    contador_interacciones += 1

    if intent:
        tag = intent["tag"]
        responses_count = len(intent["responses"])

        if responses_count > 1:
            respuesta, variant_index, variant_letter = responder_con_ab(intent, session_id)
            print("Bot:", respuesta)
            guardar_log(mensaje_usuario, respuesta, tag, variant_letter)

            if tag == "cotizacion_seguro":
                ab.track_event(session_id, tag, variant_index, "conversion", "cotizacion_solicitada")
        else:
            respuesta = random.choice(intent["responses"])
            print("Bot:", respuesta)
            guardar_log(mensaje_usuario, respuesta, tag)

    else:
        respuesta = "No entendí la consulta. ¿Podrías reformularla?"
        print("Bot:", respuesta)
        guardar_log(mensaje_usuario, respuesta, "desconocido")

print("\nSesión finalizada.")
print(f"Total de interacciones: {contador_interacciones}")

for intent in data["intents"]:
    if len(intent["responses"]) > 1:
        ab.print_report(intent["tag"])
