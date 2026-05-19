"""
Step 2: train the classifier head from saved article vectors.

This uses the existing train_X.npy and train_y.npy artifacts produced by
training.py. The evaluation printed here is training-set evaluation only; it is
meant to verify that the head can learn from the saved vectors before adding a
held-out test flow.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
X_PATH = ARTIFACTS_DIR / "train_X.npy"
Y_PATH = ARTIFACTS_DIR / "train_y.npy"
MODEL_PATH = ARTIFACTS_DIR / "bias_head.pkl"
EXPECTED_LABELS = {"left", "right"}
EXPECTED_VECTOR_SIZE = 384


def load_training_artifacts() -> tuple[np.ndarray, np.ndarray]:
    for file_path in (X_PATH, Y_PATH):
        if not file_path.exists():
            raise FileNotFoundError(f"Missing training artifact: {file_path}")

    X = np.load(X_PATH)
    y = np.load(Y_PATH, allow_pickle=True)
    validate_training_artifacts(X, y)
    return X, y


def validate_vector_artifacts(
    X: np.ndarray,
    y: np.ndarray,
    feature_name: str = "train_X",
    label_name: str = "train_y",
) -> None:
    if X.ndim != 2:
        raise ValueError(f"Expected {feature_name} to be 2D, got shape {X.shape}")
    if X.shape[1] != EXPECTED_VECTOR_SIZE:
        raise ValueError(f"Expected {EXPECTED_VECTOR_SIZE}-dim vectors, got {X.shape[1]}")
    if y.ndim != 1:
        raise ValueError(f"Expected {label_name} to be 1D, got shape {y.shape}")
    if len(X) != len(y):
        raise ValueError(f"Mismatched examples and labels: {len(X)} vectors, {len(y)} labels")

    labels = set(y.tolist())
    unexpected = labels - EXPECTED_LABELS
    if unexpected:
        raise ValueError(f"Unexpected label(s): {sorted(unexpected)}")


def validate_training_artifacts(X: np.ndarray, y: np.ndarray) -> None:
    validate_vector_artifacts(X, y)


def print_report(clf: LogisticRegression, X: np.ndarray, y: np.ndarray) -> None:
    predictions = clf.predict(X)
    labels = [str(label) for label in clf.classes_]

    print("Loaded artifacts")
    print(f"  X shape: {X.shape}")
    print(f"  y shape: {y.shape}")
    print()
    print("Label counts")
    print(pd.Series(y).value_counts().to_string())
    print()
    print("Classifier classes")
    print(f"  {labels}")
    print()
    print("Training-set evaluation")
    print(f"  accuracy: {accuracy_score(y, predictions):.4f}")
    print()
    print("Confusion matrix")
    print(pd.DataFrame(confusion_matrix(y, predictions, labels=labels), index=labels, columns=labels))
    print()
    print("Classification report")
    print(classification_report(y, predictions, labels=labels))


def main() -> None:
    X, y = load_training_artifacts()

    clf = LogisticRegression(max_iter=1000, random_state=42)
    clf.fit(X, y)

    joblib.dump(clf, MODEL_PATH)
    print_report(clf, X, y)
    print(f"Saved model to {MODEL_PATH}")


if __name__ == "__main__":
    main()
