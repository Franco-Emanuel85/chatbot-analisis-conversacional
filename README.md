# Chatbot Conversacional con Análisis SQL y A/B Testing

Proyecto desarrollado en Python que simula un chatbot basado en intents, registra interacciones en un archivo log y cuenta con un **sistema de A/B Testing** para optimizar las respuestas mediante experimentación controlada.

## Funcionalidades

- Chatbot basado en intents (NLP básico)
- Registro automático de conversaciones en archivo log
- **Sistema de A/B Testing** para experimentar con variantes de respuestas
- Procesamiento ETL desde logs hacia base SQLite
- Consultas SQL para análisis de interacciones y resultados de A/B tests
- Comandos especiales durante la ejecución para monitoreo

## Tecnologías utilizadas

| Tecnología | Uso |
|------------|-----|
| Python 3 | Lógica principal del chatbot |
| SQLite | Base de datos para almacenamiento |
| JSON | Archivo de intents y respuestas |
| SQL | Consultas analíticas |
| Git / GitHub | Control de versiones |

## Estructura del proyecto

```
chatbot-analisis-conversacional/
├── chatbot.py              # Lógica principal con A/B testing
├── ab_testing.py           # Módulo de A/B testing
├── intents.json            # Base de intents, patterns y respuestas
├── cargar_logs_sql.py      # Script ETL para cargar logs a SQLite
├── analisis_ab.sql         # Consultas SQL para análisis de A/B tests
├── conversaciones.log      # Registro de conversaciones (generado)
├── chatbot.db              # Base SQLite (generada)
├── .gitignore              # Archivos ignorados por git
└── README.md               # Este archivo
```

## Cómo usar el proyecto

### 1. Ejecutar el chatbot

```bash
python3 chatbot.py
```

**Comandos especiales durante la conversación:**

| Comando | Función |
|---------|---------|
| `reporte` | Muestra los resultados actuales de A/B testing |
| `sesion` | Muestra el ID de sesión actual |
| `nueva_sesion` | Genera un nuevo ID de sesión para probar variantes |
| `salir` | Finaliza la conversación |

### 2. Cargar logs a la base de datos

```bash
python3 cargar_logs_sql.py
```

Este script lee el archivo `conversaciones.log` y carga los datos en `chatbot.db`.

### 3. Consultar la base de datos

```bash
sqlite3 chatbot.db
```

Dentro de SQLite, podés ejecutar consultas como:

```sql
-- Ver todas las conversaciones
SELECT * FROM conversaciones;

-- Ver resultados de A/B testing
SELECT intent, variant, COUNT(*) as total_respuestas
FROM conversaciones
WHERE variant IS NOT NULL
GROUP BY intent, variant;
```

Para análisis más detallados, ejecutá las consultas del archivo `analisis_ab.sql`:

```bash
sqlite3 chatbot.db < analisis_ab.sql
```

## ¿Cómo funciona el A/B Testing?

El sistema asigna automáticamente variantes de respuesta a los usuarios cuando un intent tiene múltiples respuestas en `intents.json`.

### Ejemplo

En `intents.json`, el intent "saludo" tiene dos respuestas posibles:

```json
{
  "tag": "saludo",
  "patterns": ["hola", "buen día", "buenas", "qué tal"],
  "responses": [
    "Hola, ¿en qué puedo ayudarte?",
    "¡Buen día! ¿Qué consulta tenés?"
  ]
}
```

Cuando un usuario saluda:
- **Variante A** recibe: "Hola, ¿en qué puedo ayudarte?"
- **Variante B** recibe: "¡Buen día! ¿Qué consulta tenés?"

Si luego el usuario solicita una cotización (conversión), el sistema registra qué variante vió ese usuario. Al acumular datos, se puede determinar qué variante genera más conversiones.

### Tablas generadas

| Tabla | Función |
|-------|---------|
| `ab_assignments` | Registra qué variante vió cada usuario por intent |
| `ab_events` | Registra eventos de conversión por usuario y variante |
| `conversaciones` | Log completo de todas las interacciones |

## Consultas SQL para análisis

El archivo `analisis_ab.sql` incluye consultas predefinidas para:

1. Ver asignaciones por intent
2. Ver conversiones por intent y variante
3. Calcular tasa de conversión por variante
4. Identificar la mejor variante por intent

## Ejemplo de reporte

Al ejecutar el comando `reporte` dentro del chatbot, se muestra:

```
==================================================
A/B TEST REPORT: saludo
==================================================

Variante A:
  Usuarios asignados: 12
  Conversiones: 5
  Tasa de conversión: 41.67%

Variante B:
  Usuarios asignados: 10
  Conversiones: 2
  Tasa de conversión: 20.0%

==================================================
🏆 Variante ganadora: A
   Tasa de conversión: 41.67%
==================================================
```

## Instalación

1. Clonar el repositorio:

```bash
git clone https://github.com/Franco-Emanuel85/chatbot-analisis-conversacional.git
cd chatbot-analisis-conversacional
```

2. Asegurarse de tener Python 3 instalado:

```bash
python3 --version
```

3. Ejecutar el chatbot:

```bash
python3 chatbot.py
```

## Autor

**Franco Emanuel Tabares**

- GitHub: [Franco-Emanuel85](https://github.com/Franco-Emanuel85)
- Email: francotabares85@gmail.com

## Licencia

Este proyecto es de uso educativo y de portafolio.
