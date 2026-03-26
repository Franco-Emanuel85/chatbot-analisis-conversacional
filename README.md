# Chatbot Conversacional con Clasificación ML y A/B Testing

Proyecto desarrollado en Python que implementa un asistente virtual orientado a la industria aseguradora. Clasifica intenciones del usuario mediante **Machine Learning (TF-IDF + SVM)**, registra interacciones en base de datos, y cuenta con un sistema de **A/B Testing** para optimizar respuestas mediante experimentación controlada.

Desarrollado como proyecto de portafolio aplicado al dominio de automatización conversacional y análisis de datos.

---

## Decisiones técnicas

### ¿Por qué TF-IDF + SVM para clasificar intents?

El enfoque inicial del proyecto usaba detección por frases exactas: si el mensaje del usuario no coincidía literalmente con un patrón del `intents.json`, el bot no respondía. Eso es un problema real en producción, donde los usuarios escriben de formas impredecibles.

La reemplazé por un pipeline **TF-IDF + LinearSVC** por tres razones concretas:

- **Generaliza a frases no vistas**: "quisiera cotizar mi auto" es reconocida como `cotizacion_seguro` aunque nunca apareció en el entrenamiento.
- **Eficiente con pocos datos**: SVM funciona bien incluso con datasets pequeños, que es el caso real de cualquier chatbot en sus primeras etapas.
- **N-gramas de caracteres**: el vectorizador usa `char_wb` (bigramas a 4-gramas de caracteres), lo que lo hace robusto a errores tipográficos y variaciones de escritura en español.

El modelo incluye un **umbral de confianza configurable**: si el score de la predicción está por debajo del umbral, el bot responde que no entendió en lugar de adivinar. Esto evita falsos positivos.

### ¿Por qué SQLite Y MySQL?

El proyecto incluye una capa de abstracción (`db_manager.py`) que soporta ambos backends con una sola línea de configuración. SQLite es ideal para desarrollo local sin dependencias; MySQL es el estándar en entornos productivos.

La separación permite que el mismo código corra en ambos contextos sin modificaciones, que es el comportamiento esperado en un pipeline de datos real.

---

## Funcionalidades

- Clasificación de intents por ML (TF-IDF + SVM) con umbral de confianza
- Soporte para SQLite (desarrollo) y MySQL (producción)
- Sistema de A/B Testing con asignación persistente por sesión
- Registro de conversaciones en log estructurado y base de datos
- Pipeline ETL desde logs hacia base de datos relacional
- Consultas SQL para análisis de interacciones y resultados de tests
- Comando `explain` para inspeccionar scores del clasificador en tiempo real

---

## Tecnologías

| Tecnología | Uso |
|---|---|
| Python 3 | Lógica principal |
| scikit-learn | Clasificador TF-IDF + SVM para detección de intents |
| SQLite | Base de datos para desarrollo local |
| MySQL | Base de datos para entorno productivo |
| SQL | Consultas analíticas y reporting |
| JSON | Definición de intents y patrones de entrenamiento |
| Git / GitHub | Control de versiones |

---

## Estructura del proyecto

```
chatbot-analisis-conversacional/
├── chatbot.py              # Lógica principal: clasificación ML + A/B testing
├── intent_classifier.py    # Módulo de clasificación TF-IDF + SVM
├── db_manager.py           # Abstracción de base de datos (SQLite / MySQL)
├── ab_testing.py           # Módulo de A/B testing
├── intents.json            # Dataset de entrenamiento: intents, patrones y respuestas
├── cargar_logs_sql.py      # Script ETL: carga logs a base de datos
├── analisis_ab.sql         # Consultas SQL para análisis de A/B tests
├── requirements.txt        # Dependencias del proyecto
├── .gitignore              # Archivos excluidos del repositorio
└── README.md               # Este archivo
```

---

## Instalación

```bash
git clone https://github.com/Franco-Emanuel85/chatbot-analisis-conversacional.git
cd chatbot-analisis-conversacional

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

---

## Uso

### Ejecutar el chatbot

```bash
python3 chatbot.py
```

Al iniciarse, el clasificador ML entrena automáticamente con los patrones del `intents.json` y la base de datos crea las tablas si no existen.

**Comandos disponibles durante la conversación:**

| Comando | Función |
|---|---|
| `reporte` | Resultados actuales de A/B testing |
| `sesion` | ID de sesión activa |
| `nueva_sesion` | Genera un nuevo ID de sesión |
| `explain <frase>` | Muestra los scores del clasificador para esa frase |
| `salir` | Finaliza la conversación |

El comando `explain` es especialmente útil para entender cómo el modelo toma decisiones:

```
explain quisiera cotizar mi auto

[explain] Mensaje: 'quisiera cotizar mi auto'
  cotizacion_seguro         score=+1.842  █████████
  despedida                 score=-0.634
  saludo                    score=-1.208
```

### Configurar el backend de base de datos

En `chatbot.py`, modificá estas dos líneas:

```python
# Para SQLite (default, sin configuración adicional)
DB_BACKEND = "sqlite"

# Para MySQL
DB_BACKEND = "mysql"
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "tu_usuario",
    "password": "tu_password",
    "database": "chatbot_db",
}
```

Para MySQL, instalá el driver adicional:

```bash
pip install mysql-connector-python
```

### Cargar logs a la base de datos

```bash
python3 cargar_logs_sql.py
```

Lee `conversaciones.log` y carga los registros en la tabla `conversaciones` de la base de datos activa.

### Consultar la base de datos

```bash
sqlite3 chatbot.db
```

```sql
-- Resumen de conversaciones por intent
SELECT intent, COUNT(*) as total
FROM conversaciones
GROUP BY intent
ORDER BY total DESC;

-- Tasa de conversión por variante A/B
SELECT intent, variant, COUNT(*) as interacciones
FROM conversaciones
WHERE variant IS NOT NULL
GROUP BY intent, variant;
```

Para el conjunto completo de consultas analíticas:

```bash
sqlite3 chatbot.db < analisis_ab.sql
```

---

## Cómo funciona el clasificador ML

El módulo `intent_classifier.py` entrena un pipeline al iniciarse:

```
intents.json
    └── patrones de entrenamiento
            └── TfidfVectorizer(char_wb, ngram_range=(2,4))
                    └── LinearSVC
                            └── predicción + umbral de confianza
```

Si la confianza de la predicción no supera el umbral configurado (`CONFIDENCE_THRESHOLD = 0.35`), el bot responde que no entendió en lugar de forzar una clasificación incorrecta.

**Comparación de enfoques:**

| | Detección por frases exactas | Clasificador ML (actual) |
|---|---|---|
| "quiero cotizar" | ✓ reconocida | ✓ reconocida |
| "quisiera cotizar mi auto" | ✗ no reconocida | ✓ reconocida |
| "me interesa un seguro" | ✗ no reconocida | ✓ reconocida |
| "cuánto me saldría asegurar" | ✗ no reconocida | ✓ reconocida |

---

## Cómo funciona el A/B Testing

El sistema asigna una variante de respuesta a cada sesión de usuario de forma persistente: si un usuario vio la variante A en su primera interacción, seguirá viendo la variante A durante toda la sesión. Esto garantiza consistencia en la experiencia y validez estadística del test.

Las conversiones se registran cuando el usuario completa una acción clave (en este caso, solicitar una cotización), permitiendo calcular qué variante de respuesta genera mayor tasa de conversión.

**Tablas en base de datos:**

| Tabla | Contenido |
|---|---|
| `ab_assignments` | Qué variante fue asignada a cada sesión por intent |
| `ab_events` | Eventos de conversión registrados por sesión |
| `conversaciones` | Log completo de todas las interacciones |

**Ejemplo de reporte:**

```
==================================================
A/B TEST REPORT: cotizacion_seguro
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

---

## Autor

**Franco Emanuel Tabares**
GitHub: [Franco-Emanuel85](https://github.com/Franco-Emanuel85)
Email: francotabares85@gmail.com

---

## Licencia

Proyecto de portafolio. Uso educativo y libre.
