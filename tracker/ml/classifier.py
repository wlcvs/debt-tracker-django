"""
Classificador de linhas: transação financeira vs. ruído.

Usa RandomForest do sklearn. O modelo é salvo em model.pkl ao lado deste
arquivo e recarregado a cada chamada (arquivo pequeno, leitura rápida).

Se o modelo ainda não foi treinado, predict() retorna confiança 0.5
(incerto) e is_trained() retorna False.
"""
import os
import pickle

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from .features import extract, FEATURE_NAMES

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")


def is_trained() -> bool:
    return os.path.exists(MODEL_PATH)


def predict(line: str, bank: str = "") -> float:
    """Retorna probabilidade (0–1) de que a linha seja uma transação."""
    if not is_trained():
        return 0.5
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    X = [extract(line, bank)]
    proba = model.predict_proba(X)[0]
    return float(proba[1])


def train(examples: list[dict]) -> int:
    """
    Treina o modelo com os exemplos fornecidos.

    Cada exemplo deve ter:
      - 'line': str  (texto da linha)
      - 'bank': str
      - 'is_transaction': bool

    Retorna o número de exemplos usados.
    """
    if len(examples) < 5:
        return 0

    X = [extract(ex["line"], ex.get("bank", "")) for ex in examples]
    y = [int(ex["is_transaction"]) for ex in examples]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    return len(examples)
