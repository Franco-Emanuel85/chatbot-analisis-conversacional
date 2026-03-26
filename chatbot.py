"""
Chatbot conversacional con:
  - Clasificación de intents por ML (TF-IDF + SVM)  ← NUEVO
  - Soporte SQLite y MySQL                           ← NUEVO
  - Sistema de A/B testing
  - Logging de conversaciones
"""

import json
import random
from datetime import datetime

from intent_classifier import IntentClassifier   # ← clasificador ML
from db_manager import DatabaseManager           # ← abstracción de BD
from ab_testing import ABTesting


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN — editá solo esta sección
# ══════════════════════════════════════════════════════════════════════════════

# Cambiá a "mysql" y completá los datos para usar MySQL en lugar de SQLite
DB_BACKEND = "sqlite"        # "sqlite" | "mysql"
DB_CONFIG = {
    # Solo se usan si DB_BACKEND == "mysql"
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "tu_password",
    "database": "chatbot_db",
    # Solo se usa si DB_BACKEND == "sqlite"
    "db_path":  "chatbot.db",
}

INTENTS_PATH = "intents.json"
LOG_FILE     = "conversaciones.log"

# ══════════════════════════════════════════════════════════════════════════════
# INICIALIZACIÓN
# ══════════════════════════════════════════════════════════════════════════════

# Base de datos
db = DatabaseManager(backend=DB_BACKEND, **DB_CONFIG)
db.create_tables()

# Clasificador ML — entrena automáticamente al iniciarse
classifier = IntentClassifier(intents_path=INTENTS_PATH)

# A/B Testing (sigue usando DatabaseManager internamente)
ab = ABTesting(db_path=DB_CONFIG.get("db_path", "chatbot.db"))


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES
# ══════════════════════════════════════════════════════════════════════════════

def guardar_log(usuario: str, bot: str, intent_tag: str, variant: str = None):
    """Guarda la interacción en el archivo de log y en la base de datos."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Log en archivo de texto
    if variant:
        linea = f"{timestamp} | Usuario: {usuario} | Intent: {intent_tag} | Variant: {variant} | Bot: {bot}\n"
    else:
        linea = f"{timestamp} | Usuario: {usuario} | Intent: {intent_tag} | Bot: {bot}\n"

    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(linea)

    # Log en base de datos
    sql = db.adapt_query("""
        INSERT INTO conversaciones (timestamp, usuario, intent, variant, respuesta)
        VALUES (?, ?, ?, ?, ?)
    """)
    with db.connection() as (conn, cursor):
        cursor.execute(sql, (timestamp, usuario, intent_tag, variant, bot))


def responder_con_ab(intent: dict, session_id: str) -> tuple[str, int, str | None]:
    """Selecciona respuesta según variante A/B asignada al usuario."""
    responses = intent["responses"]
    tag = intent["tag"]

    if len(responses) <= 1:
        return responses[0], 0, None

    variant_index = ab.assign_variant(session_id, tag, len(responses))
    respuesta = responses[variant_index]
    variant_letter = chr(65 + variant_index)
    return respuesta, variant_index, variant_letter


def mostrar_ayuda():
    print("\nComandos disponibles:")
    print("  reporte      → resultados de A/B testing")
    print("  sesion       → ver ID de sesión actual")
    print("  nueva_sesion → reiniciar sesión")
    print("  explain <frase> → ver scores del clasificador para esa frase")
    print("  salir        → terminar\n")


# ══════════════════════════════════════════════════════════════════════════════
# LOOP PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

print("\nChatbot iniciado.")
mostrar_ayuda()

session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
print(f"ID de sesión: {session_id}\n")

contador = 0

while True:
    try:
        mensaje_usuario = input("Vos: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nBot: Hasta luego.")
        break

    if not mensaje_usuario:
        continue

    # ── Comandos especiales ──────────────────────────────────────────────
    if mensaje_usuario.lower() == "salir":
        print("Bot: Hasta luego.")
        break

    if mensaje_usuario.lower() == "ayuda":
        mostrar_ayuda()
        continue

    if mensaje_usuario.lower() == "reporte":
        with open(INTENTS_PATH, "r", encoding="utf-8") as f:
            intents_data = json.load(f)
        for intent in intents_data["intents"]:
            if len(intent["responses"]) > 1:
                ab.print_report(intent["tag"])
        continue

    if mensaje_usuario.lower() == "sesion":
        print(f"ID de sesión: {session_id}")
        continue

    if mensaje_usuario.lower() == "nueva_sesion":
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"Nueva sesión: {session_id}")
        continue

    if mensaje_usuario.lower().startswith("explain "):
        frase = mensaje_usuario[8:].strip()
        classifier.explain(frase)
        continue

    # ── Clasificación ML ─────────────────────────────────────────────────
    intent = classifier.predict(mensaje_usuario)
    contador += 1

    if intent:
        tag = intent["tag"]

        if len(intent["responses"]) > 1:
            respuesta, variant_index, variant_letter = responder_con_ab(intent, session_id)
            print(f"Bot: {respuesta}")
            guardar_log(mensaje_usuario, respuesta, tag, variant_letter)

            if tag == "cotizacion_seguro":
                ab.track_event(session_id, tag, variant_index, "conversion", "cotizacion_solicitada")
        else:
            respuesta = random.choice(intent["responses"])
            print(f"Bot: {respuesta}")
            guardar_log(mensaje_usuario, respuesta, tag)
    else:
        respuesta = "No entendí la consulta. ¿Podrías reformularla o usar 'ayuda' para ver los comandos?"
        print(f"Bot: {respuesta}")
        guardar_log(mensaje_usuario, respuesta, "desconocido")

# ── Resumen de sesión ────────────────────────────────────────────────────────
print(f"\nSesión finalizada. Interacciones: {contador}")
with open(INTENTS_PATH, "r", encoding="utf-8") as f:
    intents_data = json.load(f)
for intent in intents_data["intents"]:
    if len(intent["responses"]) > 1:
        ab.print_report(intent["tag"])
