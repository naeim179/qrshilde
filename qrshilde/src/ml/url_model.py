import os
import joblib
from qrshilde.src.ml.url_features import extract_url_features

MODEL_PATH = os.path.join(os.path.dirname(__file__), "url_model.pkl")


def model_exists() -> bool:
    return os.path.exists(MODEL_PATH)


def _load_model():
    # model is stored directly (e.g., LogisticRegression)
    return joblib.load(MODEL_PATH)


def get_threshold() -> float:
    # default tuned threshold
    try:
        return float(os.getenv("URL_MAL_THRESHOLD", "0.31"))
    except Exception:
        return 0.31


def predict_url(url: str) -> dict:
    model = _load_model()
    feats, names = extract_url_features(url)

    p = float(model.predict_proba([feats])[0][1])
    threshold = get_threshold()
    label = "phishing" if p >= threshold else "benign"

    # Explainability for linear models: coef * feature_value
    reasons = []
    try:
        coefs = model.coef_[0]
        impacts = []
        for i, fname in enumerate(names):
            impacts.append((fname, float(coefs[i] * feats[i])))
        impacts.sort(key=lambda x: abs(x[1]), reverse=True)
        reasons = [{"feature": f, "impact": v} for f, v in impacts[:5]]
    except Exception:
        reasons = []

    return {
        "phishing_probability": p,
        "threshold": threshold,
        "label": label,
        "reasons": reasons,
    }