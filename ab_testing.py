"""
Módulo de A/B Testing para el chatbot.
Permite experimentar con diferentes respuestas para un mismo intent.
"""

import sqlite3
import hashlib
import random
from datetime import datetime


class ABTesting:
    """
    Sistema de A/B testing para flujos conversacionales.
    """

    def __init__(self, db_path="chatbot.db"):
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        """Crea las tablas necesarias para A/B testing si no existen."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabla de asignaciones (qué usuario vio qué variante)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ab_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                intent_tag TEXT NOT NULL,
                variant TEXT NOT NULL,
                variant_index INTEGER NOT NULL,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla de eventos (conversiones, abandonos, etc.)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ab_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                intent_tag TEXT NOT NULL,
                variant TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def assign_variant(self, session_id, intent_tag, variants_count):
        """
        Asigna una variante a un usuario para un intent específico.
        Retorna el índice de la variante (0, 1, 2...)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Verificar si ya tiene asignación para este intent
        cursor.execute('''
            SELECT variant_index FROM ab_assignments
            WHERE session_id = ? AND intent_tag = ?
        ''', (session_id, intent_tag))

        result = cursor.fetchone()

        if result:
            variant_index = result[0]
        else:
            # Asignación aleatoria para pruebas
            variant_index = random.randint(0, variants_count - 1)

            variant_letter = chr(65 + variant_index)  # A, B, C...

            cursor.execute('''
                INSERT INTO ab_assignments (session_id, intent_tag, variant, variant_index)
                VALUES (?, ?, ?, ?)
            ''', (session_id, intent_tag, variant_letter, variant_index))
            conn.commit()

        conn.close()
        return variant_index

    def track_event(self, session_id, intent_tag, variant_index, event_type, event_value=None):
        """Registra un evento (conversión, abandono, etc.)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        variant_letter = chr(65 + variant_index)

        cursor.execute('''
            INSERT INTO ab_events (session_id, intent_tag, variant, event_type, event_value)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, intent_tag, variant_letter, event_type, event_value))

        conn.commit()
        conn.close()

    def get_test_results(self, intent_tag):
        """Obtiene resultados agregados para un test específico."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Asignaciones por variante
        cursor.execute('''
            SELECT variant, COUNT(DISTINCT session_id)
            FROM ab_assignments
            WHERE intent_tag = ?
            GROUP BY variant
        ''', (intent_tag,))
        assignments = dict(cursor.fetchall())

        # Conversiones por variante
        cursor.execute('''
            SELECT variant, COUNT(DISTINCT session_id)
            FROM ab_events
            WHERE intent_tag = ? AND event_type = 'conversion'
            GROUP BY variant
        ''', (intent_tag,))
        conversions = dict(cursor.fetchall())

        conn.close()

        results = {}
        for variant, total in assignments.items():
            conv = conversions.get(variant, 0)
            rate = (conv / total * 100) if total > 0 else 0
            results[variant] = {
                "assignments": total,
                "conversions": conv,
                "conversion_rate": round(rate, 2)
            }

        return results

    def print_report(self, intent_tag):
        """Imprime un reporte formateado."""
        results = self.get_test_results(intent_tag)
        print(f"\n{'='*50}")
        print(f"A/B TEST REPORT: {intent_tag}")
        print(f"{'='*50}")

        if not results:
            print("No hay datos suficientes para este test aún.")
            print("Hacé más interacciones para generar datos.")
        else:
            for variant, data in results.items():
                print(f"\nVariante {variant}:")
                print(f"  Usuarios asignados: {data['assignments']}")
                print(f"  Conversiones: {data['conversions']}")
                print(f"  Tasa de conversión: {data['conversion_rate']}%")

            print(f"\n{'='*50}")

            # Determinar la variante ganadora
            if results:
                winner = max(results.keys(), key=lambda v: results[v]["conversion_rate"])
                print(f"🏆 Variante ganadora: {winner}")
                print(f"   Tasa de conversión: {results[winner]['conversion_rate']}%")
            print(f"{'='*50}\n")
