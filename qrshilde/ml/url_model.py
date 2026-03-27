import os
import joblib
from qrshilde.ml.url_features import extract_url_features

MODEL_PATH = os.path.join(os.path.dirname(__file__), "url_model.pkl")

# ✅ Cache الموديل — يُحمل مرة وحدة فقط
_cached_model = None


def model_exists() -> bool:
    return os.path.exists(MODEL_PATH)


def _load_model():
    global _cached_model
    if _cached_model is None:
        _cached_model = joblib.load(MODEL_PATH)
    return _cached_model


def get_threshold() -> float:
    try:
        return float(os.getenv("URL_MAL_THRESHOLD", "0.6"))
    except Exception:
        return 0.6


def predict_url(url: str) -> dict:
    model = _load_model()
    feats, names = extract_url_features(url)

    proba_row = model.predict_proba([feats])[0]
    classes = list(getattr(model, "classes_", []))

    if 1 in classes:
        idx_mal = classes.index(1)
        p = float(proba_row[idx_mal])
    else:
        p = float(proba_row[1]) if len(proba_row) > 1 else float(proba_row[0])

    threshold = get_threshold()
    label = "malicious" if p >= threshold else "benign"

    reasons = []
    try:
        if hasattr(model, "coef_"):
            coefs = model.coef_[0]
            impacts = sorted(
                [(names[i], float(coefs[i] * feats[i])) for i in range(len(names))],
                key=lambda x: abs(x[1]),
                reverse=True,
            )
            reasons = [{"feature": f, "impact": v} for f, v in impacts[:5]]

        elif hasattr(model, "feature_importances_"):
            imps = list(model.feature_importances_)
            pairs = sorted(
                [(names[i], float(imps[i])) for i in range(min(len(names), len(imps)))],
                key=lambda x: x[1],
                reverse=True,
            )
            reasons = [{"feature": f, "impact": v} for f, v in pairs[:5]]

    except Exception:
        reasons = []

    return {
        "malicious_probability": p,
        "phishing_probability": p,  # backward compatibility
        "threshold": threshold,
        "label": label,
        "reasons": reasons,
    }