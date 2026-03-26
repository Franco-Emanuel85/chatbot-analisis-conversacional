import sqlite3

# Conectar a la base
conexion = sqlite3.connect("chatbot.db")
cursor = conexion.cursor()

# Leer archivo log
with open("conversaciones.log", "r", encoding="utf-8") as archivo:

    for linea in archivo:

        try:
            # Separar partes
            partes = linea.strip().split(" | ")

            timestamp = partes[0]

            usuario = partes[1].replace("Usuario: ", "")

            intent = partes[2].replace("Intent: ", "")

            respuesta = partes[3].replace("Bot: ", "")

            # Insertar en base
            cursor.execute("""
                INSERT INTO conversaciones 
                (timestamp, usuario, intent, respuesta)
                VALUES (?, ?, ?, ?)
            """, (timestamp, usuario, intent, respuesta))

        except Exception as e:
            print("Error procesando línea:", linea)

# Guardar cambios
conexion.commit()

# Cerrar conexión
conexion.close()

print("Logs cargados correctamente.")
