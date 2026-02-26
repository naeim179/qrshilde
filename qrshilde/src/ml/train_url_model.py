import os, json, datetime
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from qrshilde.src.ml.url_features import extract_url_features
from qrshilde.src.ml.url_model import MODEL_PATH


DATA_PATH = os.path.join("data", "malicious_phish_Dataset.csv")
META_PATH = os.path.join(os.path.dirname(MODEL_PATH), "url_model_meta.json")


def main():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    # columns are: url, type (confirmed from your output)
    df = df[["url", "type"]].dropna()
    df["url"] = df["url"].astype(str)
    df["type"] = df["type"].astype(str).str.lower()

    # binary label: benign=0, anything else=1
    y = df["type"].map(lambda v: 0 if v == "benign" else 1).astype(int).to_list()

    X = []
    for u in df["url"].tolist():
        feats, _ = extract_url_features(u)
        X.append(feats)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = LogisticRegression(max_iter=2000, class_weight="balanced")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }

    joblib.dump(model, MODEL_PATH)

    meta = {
        "trained_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dataset": os.path.abspath(DATA_PATH),
        "rows": int(len(df)),
        "label_mapping": {"benign": 0, "other": 1},
        "metrics": metrics,
    }

    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"[+] Trained and saved model: {MODEL_PATH}")
    print(f"[+] Saved meta: {META_PATH}")
    print("[+] Metrics:", metrics)


if __name__ == "__main__":
    main()