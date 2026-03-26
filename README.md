# Chatbot Conversacional con Análisis SQL

Proyecto desarrollado en Python que simula un chatbot basado en intents y registra interacciones en un archivo log, posteriormente procesadas hacia una base de datos SQLite para análisis.

## Funcionalidades

- Chatbot basado en intents (NLP básico)
- Registro automático de conversaciones
- Procesamiento ETL desde logs hacia base SQLite
- Consultas SQL para análisis de interacciones

## Tecnologías utilizadas

- Python 3
- SQLite
- JSON
- SQL

## Archivos principales

- chatbot.py → lógica principal del chatbot
- intents.json → base de intents
- conversaciones.log → registro de conversaciones
- chatbot.db → base SQLite
- cargar_logs_sql.py → script ETL para cargar logs

## Cómo usar el proyecto

Ejecutar chatbot:

python3 chatbot.py

Cargar logs a base:

python3 cargar_logs_sql.py

Consultar base SQLite:

sqlite3 chatbot.db

## Autor

Franco Emanuel Tabares
