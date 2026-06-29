"""
Line classifier: financial transaction vs. noise.

Uses sklearn's RandomForest. The model is saved to model.pkl next to this
file and reloaded on each call (small file, fast read).

If the model has not been trained yet, predict() returns 0.5 (uncertain)
and is_trained() returns False.
"""
import os
import pickle

from sklearn.ensemble import RandomForestClassifier

from .features import extract

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")


def is_trained() -> bool:
    return os.path.exists(MODEL_PATH)


def predict(line: str, bank: str = "") -> float:
    """Return probability (0–1) that this line is a transaction."""
    if not is_trained():
        return 0.5
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    X = [extract(line, bank)]
    proba = model.predict_proba(X)[0]
    return float(proba[1])


def train(examples: list[dict]) -> int:
    """
    Train the classifier on labeled examples.

    Each example must have:
      - 'line': str
      - 'bank': str
      - 'is_transaction': bool

    Returns the number of examples used.
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
