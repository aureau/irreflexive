"""
Evaluate the trained classifier head on held-out test.csv rows.

This script builds test features with the same article_to_vector logic used for
train_X.npy, loads the already-fitted bias_head.pkl, and predicts labels. It
does not rebuild corpus baselines, modify train_X/train_y, or call fit().
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from tqdm import tqdm

from train_head import validate_vector_artifacts


BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
TEST_CSV_PATH = BASE_DIR.parent / "datasets" / "train-test-datasets" / "test.csv"
MODEL_PATH = ARTIFACTS_DIR / "bias_head.pkl"
TEST_X_PATH = ARTIFACTS_DIR / "test_X.npy"
TEST_Y_PATH = ARTIFACTS_DIR / "test_y.npy"


def print_eval_report(clf, X: np.ndarray, y: np.ndarray) -> None:
    predictions = clf.predict(X)
    labels = [str(label) for label in clf.classes_]

    print()
    print("Mapped test label counts")
    print(pd.Series(y).value_counts().to_string())
    print()
    print("Classifier classes")
    print(f"  {labels}")
    print()
    print("Held-out test evaluation")
    print(f"  accuracy: {accuracy_score(y, predictions):.4f}")
    print()
    print("Confusion matrix")
    print(pd.DataFrame(confusion_matrix(y, predictions, labels=labels), index=labels, columns=labels))
    print()
    print("Classification report")
    print(classification_report(y, predictions, labels=labels))

    if hasattr(clf, "predict_proba"):
        probabilities = clf.predict_proba(X)
        confidence = probabilities.max(axis=1)
        print("Prediction confidence")
        print(f"  mean max probability: {confidence.mean():.4f}")
        print(f"  median max probability: {np.median(confidence):.4f}")


def main() -> None:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Missing trained head: {MODEL_PATH}")
    if not TEST_CSV_PATH.exists():
        raise FileNotFoundError(f"Missing test CSV: {TEST_CSV_PATH}")

    clf = joblib.load(MODEL_PATH)
    if TEST_X_PATH.exists() and TEST_Y_PATH.exists():
        X = np.load(TEST_X_PATH)
        y = np.load(TEST_Y_PATH, allow_pickle=True)
        validate_vector_artifacts(X, y, feature_name="test_X", label_name="test_y")
        print(f"Loaded cached test features from {ARTIFACTS_DIR}/")
        print(f"  test_X.npy shape {X.shape}")
        print(f"  test_y.npy shape {y.shape}")
        print_eval_report(clf, X, y)
        return

    from training import article_to_vector, bias_map

    df = pd.read_csv(TEST_CSV_PATH)
    df = df.dropna(subset=["bias", "page_text"]).copy()
    df["mapped_bias"] = df["bias"].map(bias_map)
    df = df.dropna(subset=["mapped_bias"])

    X_list: list[np.ndarray] = []
    y_list: list[str] = []
    skipped = 0

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Embedding test articles"):
        vec = article_to_vector(str(row["page_text"]))
        if vec is None:
            skipped += 1
            continue

        X_list.append(vec)
        y_list.append(row["mapped_bias"])

    if not X_list:
        raise ValueError("No valid test vectors were created")

    X = np.stack(X_list)
    y = np.array(y_list)
    validate_vector_artifacts(X, y, feature_name="test_X", label_name="test_y")

    np.save(TEST_X_PATH, X)
    np.save(TEST_Y_PATH, y)
    print(f"Saved test features to {ARTIFACTS_DIR}/")
    print(f"  test_X.npy shape {X.shape}")
    print(f"  test_y.npy shape {y.shape}")
    print(f"  skipped empty articles: {skipped}")

    print_eval_report(clf, X, y)


if __name__ == "__main__":
    main()
