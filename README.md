# QrShilde (QR Secure) — Rules + ML QR Payload Analyzer

A lightweight QR security scanner that analyzes decoded QR payloads using:
- Rule-based heuristics
- Optional machine-learning URL classifier

No external LLMs.
No browser automation.
Designed for offline-friendly security analysis.

---

## Features

- Detects payload type (URL, WiFi, SMS, TEL, Email, vCard, Deep link)
- URL heuristics:
  - Shortener detection
  - Brand impersonation hints
  - HTTP (no TLS)
  - DNS resolution check
- WiFi risk detection (WEP / NoPass / Hidden)
- Smishing keyword detection
- ML phishing probability (optional)

---

## Setup (Windows)

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py

Server runs on:
http://127.0.0.1:8000

---

## API Example

POST /api/analyze

{
  "payload": "https://example.com/login"
}

---

## Train URL Model (Optional)

python -m qrshilde.src.ml.train_url_model

Model files are ignored by git.

---

## License

MIT
