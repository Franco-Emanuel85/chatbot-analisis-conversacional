import sqlite3

def crear_tabla_conversaciones(cursor):
    """Crea la tabla de conversaciones si no existe."""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            usuario TEXT,
            intent TEXT,
            variant TEXT,
            respuesta TEXT
        )
    ''')

# Conectar a la base
conexion = sqlite3.connect("chatbot.db")
cursor = conexion.cursor()

# Crear tabla si no existe
crear_tabla_conversaciones(cursor)

# Leer archivo log
with open("conversaciones.log", "r", encoding="utf-8") as archivo:
    for linea in archivo:
        try:
            partes = linea.strip().split(" | ")

            timestamp = partes[0]

            # Extraer usuario
            usuario = partes[1].replace("Usuario: ", "")

            # Extraer intent
            intent_part = partes[2].replace("Intent: ", "")

            # Verificar si hay variant
            variant = None
            if "Variant:" in linea:
                # Formato con variant
                intent_part = partes[2].replace("Intent: ", "")
                variant = partes[3].replace("Variant: ", "")
                respuesta = partes[4].replace("Bot: ", "")
            else:
                # Formato sin variant
                respuesta = partes[3].replace("Bot: ", "")

            # Insertar en base
            cursor.execute("""
                INSERT INTO conversaciones 
                (timestamp, usuario, intent, variant, respuesta)
                VALUES (?, ?, ?, ?, ?)
            """, (timestamp, usuario, intent_part, variant, respuesta))

        except Exception as e:
            print(f"Error procesando línea: {linea.strip()}")
            print(f"Error: {e}")

# Guardar cambios
conexion.commit()

# Cerrar conexión
conexion.close()

print("Logs cargados correctamente.")
