from __future__ import annotations

import re
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

DB_PATH = Path(__file__).resolve().parent.parent / "qrshilde_memory.db"
_LOCK = threading.Lock()

# ✅ flag عشان init_db ما تتكرر
_DB_INITIALIZED = False

URL_ANYWHERE_RE = re.compile(r'((?:https?://|www\.)[^\s<>"\']+)', re.IGNORECASE)


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    global _DB_INITIALIZED
    # ✅ تشتغل مرة وحدة بس طول عمر التطبيق
    if _DB_INITIALIZED:
        return

    with _LOCK:
        if _DB_INITIALIZED:
            return
        conn = _connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payload TEXT NOT NULL,
                    normalized_payload TEXT NOT NULL,
                    domain TEXT,
                    payload_type TEXT,
                    verdict TEXT,
                    risk_score INTEGER,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_analyses_normalized_payload "
                "ON analyses(normalized_payload)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_analyses_domain "
                "ON analyses(domain)"
            )
            conn.commit()
        finally:
            conn.close()
        _DB_INITIALIZED = True


def normalize_payload(payload: str | None) -> str:
    """
    ✅ بنعمل normalize للـ URL والنص العادي بس.
    الـ WIFI payloads حساسة للحالة (passwords) فنحافظ على الـ case.
    """
    text = (payload or "").strip()

    # WIFI: نحافظ على الـ case كاملاً — الباسورد حساس
    if text.upper().startswith("WIFI:"):
        return re.sub(r"\s+", " ", text)

    # باقي الـ payloads: lowercase
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text


def extract_domain(payload: str | None) -> str | None:
    text = (payload or "").strip()
    if not text:
        return None

    candidate = text
    if "://" not in candidate and candidate.lower().startswith("www."):
        candidate = "https://" + candidate

    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower().strip(".")
    if host.startswith("www."):
        host = host[4:]
    if host:
        return host

    match = URL_ANYWHERE_RE.search(text)
    if not match:
        return None

    candidate = match.group(1).strip()
    if "://" not in candidate and candidate.lower().startswith("www."):
        candidate = "https://" + candidate

    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower().strip(".")
    if host.startswith("www."):
        host = host[4:]
    return host or None


def lookup_known_indicator(payload: str | None) -> dict | None:
    init_db()

    normalized_payload = normalize_payload(payload)
    domain = extract_domain(payload)

    with _LOCK:
        conn = _connect()
        try:
            # Exact payload match
            exact_row = conn.execute(
                """
                SELECT payload, verdict, risk_score, created_at
                FROM analyses
                WHERE normalized_payload = ?
                  AND risk_score >= 50
                ORDER BY risk_score DESC, created_at DESC
                LIMIT 1
                """,
                (normalized_payload,),
            ).fetchone()

            if exact_row is not None:
                exact_count = conn.execute(
                    """
                    SELECT COUNT(*) AS cnt
                    FROM analyses
                    WHERE normalized_payload = ?
                      AND risk_score >= 50
                    """,
                    (normalized_payload,),
                ).fetchone()["cnt"]

                return {
                    "match_type": "exact_payload",
                    "matched_value": normalized_payload,
                    "seen_count": int(exact_count),
                    "max_risk": int(exact_row["risk_score"] or 0),
                    "last_verdict": exact_row["verdict"] or "UNKNOWN",
                    "last_seen": exact_row["created_at"] or "",
                    "message": (
                        f"This exact payload was seen before and flagged "
                        f"as {exact_row['verdict']}."
                    ),
                }

            # Domain match
            if domain:
                domain_row = conn.execute(
                    """
                    SELECT payload, verdict, risk_score, created_at
                    FROM analyses
                    WHERE domain = ?
                      AND risk_score >= 60
                    ORDER BY risk_score DESC, created_at DESC
                    LIMIT 1
                    """,
                    (domain,),
                ).fetchone()

                if domain_row is not None:
                    domain_count = conn.execute(
                        """
                        SELECT COUNT(*) AS cnt
                        FROM analyses
                        WHERE domain = ?
                          AND risk_score >= 60
                        """,
                        (domain,),
                    ).fetchone()["cnt"]

                    return {
                        "match_type": "domain",
                        "matched_value": domain,
                        "seen_count": int(domain_count),
                        "max_risk": int(domain_row["risk_score"] or 0),
                        "last_verdict": domain_row["verdict"] or "UNKNOWN",
                        "last_seen": domain_row["created_at"] or "",
                        "message": (
                            f"This domain was seen before in a previously "
                            f"flagged analysis."
                        ),
                    }

            return None
        finally:
            conn.close()


def save_analysis_result(result: dict) -> None:
    init_db()

    payload = (result.get("payload") or "").strip()
    normalized_payload = normalize_payload(payload)

    url_analysis = result.get("url_analysis") or {}
    # ✅ domain من url_analysis أو نحسبه مرة وحدة
    domain = (url_analysis.get("domain") or extract_domain(payload) or "").strip() or None
    payload_type = (result.get("payload_type") or "").strip()
    verdict = (result.get("verdict") or "").strip()
    risk_score = int(result.get("risk_score") or 0)
    created_at = result.get("generated_at") or _utc_now()

    with _LOCK:
        conn = _connect()
        try:
            conn.execute(
                """
                INSERT INTO analyses (
                    payload,
                    normalized_payload,
                    domain,
                    payload_type,
                    verdict,
                    risk_score,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload,
                    normalized_payload,
                    domain,
                    payload_type,
                    verdict,
                    risk_score,
                    created_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()


# ✅ initialize عند الـ import مباشرة
init_db()