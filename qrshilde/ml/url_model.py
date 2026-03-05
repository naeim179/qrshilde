import os
import joblib
from qrshilde.ml.url_features import extract_url_features

MODEL_PATH = os.path.join(os.path.dirname(__file__), "url_model.pkl")


def model_exists() -> bool:
    return os.path.exists(MODEL_PATH)


def _load_model():
    return joblib.load(MODEL_PATH)


def get_threshold() -> float:
    """
    Default threshold = 0.6 (matches url_model_meta.json suggested_threshold).
    Override with env var URL_MAL_THRESHOLD.
    """
    try:
        return float(os.getenv("URL_MAL_THRESHOLD", "0.6"))
    except Exception:
        return 0.6


def predict_url(url: str) -> dict:
    model = _load_model()
    feats, names = extract_url_features(url)

    # Predict probability safely using model.classes_
    proba_row = model.predict_proba([feats])[0]
    classes = list(getattr(model, "classes_", []))

    # We treat class "1" as malicious/other per label_mapping in meta.json
    if 1 in classes:
        idx_mal = classes.index(1)
        p = float(proba_row[idx_mal])
    else:
        # Fallback (shouldn't usually happen): assume 2nd column is "positive"
        p = float(proba_row[1]) if len(proba_row) > 1 else float(proba_row[0])

    threshold = get_threshold()
    label = "malicious" if p >= threshold else "benign"

    # Explainability:
    reasons = []
    try:
        if hasattr(model, "coef_"):
            coefs = model.coef_[0]
            impacts = []
            for i, fname in enumerate(names):
                impacts.append((fname, float(coefs[i] * feats[i])))
            impacts.sort(key=lambda x: abs(x[1]), reverse=True)
            reasons = [{"feature": f, "impact": v} for f, v in impacts[:5]]
        elif hasattr(model, "feature_importances_"):
            imps = list(getattr(model, "feature_importances_", []))
            pairs = [(names[i], float(imps[i])) for i in range(min(len(names), len(imps)))]
            pairs.sort(key=lambda x: x[1], reverse=True)
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