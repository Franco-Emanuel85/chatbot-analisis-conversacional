"""
Clasificador de intenciones con Machine Learning.
Usa TF-IDF + SVM para reconocer intents sin necesitar frases exactas.

Reemplaza la función detectar_intencion() del chatbot original.
"""

import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
import numpy as np


class IntentClassifier:
    """
    Clasificador de intenciones basado en TF-IDF + SVM.

    A diferencia de la detección por frases exactas, este modelo
    generaliza a partir de los patrones de entrenamiento y puede
    reconocer frases similares que nunca vio antes.

    Ejemplo:
        "quisiera cotizar mi auto" → intent: cotizacion_seguro  ✓
        "me interesa un precio"   → intent: cotizacion_seguro  ✓
        (Antes necesitabas escribir exactamente "cotizar seguro", etc.)
    """

    # Umbral mínimo de confianza. Por debajo de esto, el modelo
    # devuelve None en lugar de adivinar.
    CONFIDENCE_THRESHOLD = 0.35

    def __init__(self, intents_path="intents.json"):
        self.intents_path = intents_path
        self.intents_data = None      # JSON completo
        self.tag_to_intent = {}       # tag → dict del intent
        self.pipeline = None          # TF-IDF + SVM
        self.label_encoder = LabelEncoder()
        self._load_and_train()

    # ── Carga y entrenamiento ─────────────────────────────────────────────

    def _load_and_train(self):
        """Carga intents.json y entrena el modelo."""
        with open(self.intents_path, "r", encoding="utf-8") as f:
            self.intents_data = json.load(f)

        X_train = []  # frases de entrenamiento
        y_train = []  # etiquetas (tags)

        for intent in self.intents_data["intents"]:
            tag = intent["tag"]
            self.tag_to_intent[tag] = intent
            for pattern in intent["patterns"]:
                X_train.append(pattern.lower())
                y_train.append(tag)

        # Codificar etiquetas a números
        y_encoded = self.label_encoder.fit_transform(y_train)

        # Pipeline: vectorización TF-IDF → clasificador SVM lineal
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                analyzer="char_wb",   # n-gramas de caracteres: robusto a errores tipográficos
                ngram_range=(2, 4),   # bigramas a 4-gramas
                sublinear_tf=True,    # log-scaling de frecuencias
            )),
            ("svm", LinearSVC(
                C=1.0,
                max_iter=2000,
                dual="auto",
            )),
        ])

        self.pipeline.fit(X_train, y_encoded)
        print(f"[Clasificador] Modelo entrenado con {len(X_train)} ejemplos "
              f"para {len(self.tag_to_intent)} intents.")

    # ── Predicción ────────────────────────────────────────────────────────

    def predict(self, mensaje: str) -> dict | None:
        """
        Clasifica un mensaje y devuelve el intent dict, o None si
        la confianza es menor al umbral.

        Args:
            mensaje: texto libre del usuario

        Returns:
            dict del intent (con "tag", "patterns", "responses")
            o None si no se supera el umbral de confianza.
        """
        mensaje_norm = mensaje.lower().strip()
        if not mensaje_norm:
            return None

        # decision_function devuelve distancia al hiperplano (= confianza)
        scores = self.pipeline.decision_function([mensaje_norm])[0]

        # Con más de 2 clases, scores es un array; tomamos el máximo
        if hasattr(scores, "__len__"):
            best_idx = int(np.argmax(scores))
            confidence = float(scores[best_idx])
        else:
            best_idx = 0
            confidence = float(scores)

        predicted_tag = self.label_encoder.inverse_transform([best_idx])[0]

        if confidence < self.CONFIDENCE_THRESHOLD:
            return None  # no hay suficiente certeza

        return self.tag_to_intent[predicted_tag]

    # ── Utilidad de diagnóstico ───────────────────────────────────────────

    def explain(self, mensaje: str):
        """
        Muestra los scores de todos los intents para un mensaje.
        Útil para ajustar el umbral o depurar casos difíciles.
        """
        mensaje_norm = mensaje.lower().strip()
        scores = self.pipeline.decision_function([mensaje_norm])[0]

        if not hasattr(scores, "__len__"):
            scores = [scores]

        tags = self.label_encoder.inverse_transform(range(len(scores)))
        ranked = sorted(zip(tags, scores), key=lambda x: x[1], reverse=True)

        print(f"\n[explain] Mensaje: '{mensaje}'")
        for tag, score in ranked:
            bar = "█" * max(0, int(score * 5))
            print(f"  {tag:<25} score={score:+.3f}  {bar}")
        print()
