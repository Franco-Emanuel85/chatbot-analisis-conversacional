"""
Capa de abstracción de base de datos.
Soporta SQLite (por defecto, sin dependencias) y MySQL.

Uso:
    # SQLite (default, sin configuración extra)
    db = DatabaseManager()

    # MySQL
    db = DatabaseManager(
        backend="mysql",
        host="localhost",
        port=3306,
        user="root",
        password="tu_password",
        database="chatbot_db",
    )

El resto del código (ABTesting, cargar_logs) no necesita cambios:
trabaja siempre contra DatabaseManager, sin importar el backend.
"""

import sqlite3
from contextlib import contextmanager


# ── Intentar importar el driver de MySQL (opcional) ──────────────────────────
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False


class DatabaseManager:
    """
    Gestiona conexiones y consultas para SQLite o MySQL.

    Expone una interfaz unificada: execute() y fetchall(),
    para que el resto del proyecto no dependa del backend.
    """

    SUPPORTED_BACKENDS = ("sqlite", "mysql")

    def __init__(self, backend: str = "sqlite", **kwargs):
        """
        Args:
            backend: "sqlite" o "mysql"
            **kwargs para SQLite:
                db_path (str): ruta al archivo .db  [default: "chatbot.db"]
            **kwargs para MySQL:
                host     (str): servidor             [default: "localhost"]
                port     (int): puerto               [default: 3306]
                user     (str): usuario              [default: "root"]
                password (str): contraseña           [default: ""]
                database (str): nombre de la BD      [default: "chatbot_db"]
        """
        if backend not in self.SUPPORTED_BACKENDS:
            raise ValueError(f"Backend '{backend}' no soportado. Usá: {self.SUPPORTED_BACKENDS}")

        if backend == "mysql" and not MYSQL_AVAILABLE:
            raise ImportError(
                "mysql-connector-python no está instalado.\n"
                "Instalalo con:  pip install mysql-connector-python"
            )

        self.backend = backend
        self._sqlite_path = kwargs.get("db_path", "chatbot.db")
        self._mysql_config = {
            "host":     kwargs.get("host",     "localhost"),
            "port":     kwargs.get("port",     3306),
            "user":     kwargs.get("user",     "root"),
            "password": kwargs.get("password", ""),
            "database": kwargs.get("database", "chatbot_db"),
        }

    # ── Conexión ──────────────────────────────────────────────────────────

    @contextmanager
    def connection(self):
        """
        Context manager que abre y cierra la conexión automáticamente.

        Uso:
            with db.connection() as (conn, cursor):
                cursor.execute("SELECT ...")
                conn.commit()
        """
        if self.backend == "sqlite":
            conn = sqlite3.connect(self._sqlite_path)
            conn.row_factory = sqlite3.Row   # acceso por nombre de columna
            cursor = conn.cursor()
            try:
                yield conn, cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

        else:  # mysql
            conn = mysql.connector.connect(**self._mysql_config)
            cursor = conn.cursor(dictionary=True)   # resultados como dicts
            try:
                yield conn, cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()
                conn.close()

    # ── Helpers ───────────────────────────────────────────────────────────

    def placeholder(self) -> str:
        """
        Devuelve el placeholder correcto para parámetros según el backend.
        SQLite usa ?, MySQL usa %s.
        """
        return "?" if self.backend == "sqlite" else "%s"

    def adapt_query(self, sql: str) -> str:
        """
        Convierte una query escrita con ? al placeholder del backend activo.
        Permite escribir las queries una sola vez en formato SQLite.
        """
        if self.backend == "mysql":
            return sql.replace("?", "%s")
        return sql

    # ── DDL: creación de tablas ───────────────────────────────────────────

    def create_tables(self):
        """Crea todas las tablas del proyecto si no existen."""
        tables = self._get_create_statements()
        with self.connection() as (conn, cursor):
            for sql in tables:
                cursor.execute(sql)
        print(f"[DB] Tablas verificadas/creadas en {self.backend.upper()}.")

    def _get_create_statements(self) -> list[str]:
        """
        Devuelve los CREATE TABLE adaptados al backend activo.
        MySQL necesita ENGINE=InnoDB y tipos ligeramente distintos.
        """
        if self.backend == "sqlite":
            return [
                """
                CREATE TABLE IF NOT EXISTS conversaciones (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    usuario   TEXT,
                    intent    TEXT,
                    variant   TEXT,
                    respuesta TEXT
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS ab_assignments (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id   TEXT NOT NULL,
                    intent_tag   TEXT NOT NULL,
                    variant      TEXT NOT NULL,
                    variant_index INTEGER NOT NULL,
                    assigned_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS ab_events (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id  TEXT NOT NULL,
                    intent_tag  TEXT NOT NULL,
                    variant     TEXT NOT NULL,
                    event_type  TEXT NOT NULL,
                    event_value TEXT,
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
            ]
        else:  # mysql
            return [
                """
                CREATE TABLE IF NOT EXISTS conversaciones (
                    id        INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp VARCHAR(30),
                    usuario   TEXT,
                    intent    VARCHAR(100),
                    variant   VARCHAR(5),
                    respuesta TEXT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS ab_assignments (
                    id            INT AUTO_INCREMENT PRIMARY KEY,
                    session_id    VARCHAR(50)  NOT NULL,
                    intent_tag    VARCHAR(100) NOT NULL,
                    variant       VARCHAR(5)   NOT NULL,
                    variant_index TINYINT      NOT NULL,
                    assigned_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS ab_events (
                    id          INT AUTO_INCREMENT PRIMARY KEY,
                    session_id  VARCHAR(50)  NOT NULL,
                    intent_tag  VARCHAR(100) NOT NULL,
                    variant     VARCHAR(5)   NOT NULL,
                    event_type  VARCHAR(50)  NOT NULL,
                    event_value TEXT,
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
            ]
