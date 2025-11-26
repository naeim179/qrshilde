# qrshilde
# qrshilde — QR Code Security Toolkit

Security-focused toolkit for **analyzing, decoding, and inspecting QR codes**.

> Built for CTF players, blue teams, and anyone who doesn’t trust “scan this QR” blindly.

---

## 🔍 What is qrshilde?

`qrshilde` is a small offensive / defensive lab project that helps you:

- Decode QR codes safely (offline if you want).
- Inspect what’s really inside (URLs, Wi-Fi configs, SMS, vCard…).
- Detect **malicious patterns** before you ever open the link or join the network.
- Study and document **real QR-based attack vectors**.

It’s designed as a **learning + lab tool** more than a production scanner.

---

## ✨ Features (Planned & Implemented)

- 📥 **Decode QR codes**
  - From image files (`.png`, `.jpg`, …).
  - CLI-based, no need to trust 3rd party websites.

- 🧠 **Payload inspection**
  - Detects if content looks like:
    - URL (HTTP/HTTPS)
    - Wi-Fi auto-connect config
    - vCard / contact
    - SMS / tel: actions
    - Payment-related patterns

- ☠️ **Attack surface mapping**
  - Maps decoded content to known **QR attack vectors**:
    - Phishing URLs
    - QRLjacking candidates (login/session links)
    - Rogue Wi-Fi networks
    - Malicious contact (vCard injection)
    - SMS / call abuse

- 🧪 **CTF & lab friendly**
  - `samples/` folder with example QR codes (phishing, Wi-Fi, vCard, SMS).
  - `docs/` with notes about each attack type and references (McAfee, OWASP, etc.).

> Some modules are **Coming Soon** (marked below) — this repo is meant to grow as the learning grows.

---

## 🧨 QR Attack Types Covered

We separate attacks into two buckets:

### 1️⃣ URL-based attacks

These are attacks where the QR mainly hides a **URL**:

- **Phishing / malware URLs**
  - QR leads to:
    - Fake login portals
    - Fake payment pages
    - Malware download pages

- **QRLjacking (Session Hijacking)**
  - QR encodes a **“Login with QR” / session link**.
  - Attacker tricks the victim into scanning their own login QR.
  - Victim authenticates **attacker’s session** instead of their own.  
  - Reference: OWASP QRLJacking documentation.

- **Tracking / shady redirect chains**
  - QR → Tracking URL → final payload.
  - Used for profiling, analytics or hiding real target.

> These are mainly handled by:  
> `src/qr_inspect.py` + `tools/url_scanner.py` + `tools/malicious_pattern_detector.py`

---

### 2️⃣ Non-URL-based / Action-based attacks

These don’t have to use `http://` or `https://` directly.

1. **QR → SMS / Phone Trigger**
   - Payload like:  
     - `sms:+1234567890?body=...`  
     - `tel:+1234567890`
   - Can be abused to:
     - Send SMS to premium numbers.
     - Auto-dial attacker-controlled numbers.

2. **QR → Rogue Wi-Fi Network**
   - Payload like:
     - `WIFI:T:WPA;S:SuspiciousSSID;P:weakpass123;;`
   - Can silently connect victim to:
     - Evil twin AP.
     - MITM hotspot.

3. **Payment QR Code Fraud (No clear URLs)**
   - Static payment QR (e.g. wallet address, merchant ID) replaced by attacker’s code.
   - Victim pays **legit-looking merchant**, money goes to attacker.

4. **Malicious Contact / vCard Injection**
   - QR encodes a full contact card (vCard).
   - Victim saves contact named like:
     - “Bank Support”
     - “IT Helpdesk”
   - Used later in **social engineering** / phishing.

> These are mainly handled by:  
> `src/qr_analyze_payloads.py` + `tools/wifi_auto_connect_detector.py`

---

## 📂 Project Structure

```bash
qrshilde/
│
├── README.md                # This file
│
├── docs/                    # Theory, attack explanations, references
│   ├── attacks.md           # Overview of all QR attack categories
│   ├── qrljacking.md        # Notes about QRLjacking attack
│   ├── sms_attacks.md       # SMS / telephone trigger attacks
│   └── wifi_attacks.md      # Rogue Wi-Fi QR attacks
│
├── src/                     # Core logic
│   ├── qr_decode.py         # Decode QR images → raw content
│   ├── qr_generate.py       # Generate test QR codes (CTF / labs)
│   ├── qr_inspect.py        # Inspect decoded content (URL? Wi-Fi? SMS? vCard?)
│   └── qr_analyze_payloads.py # Classify content into attack types
│
├── tools/                   # Helper scanners / detectors
│   ├── url_scanner.py       # Check URLs against patterns/blacklists (future)
│   ├── malicious_pattern_detector.py   # Regex-based detection
│   └── wifi_auto_connect_detector.py   # Detect unsafe Wi-Fi configs
│
└── samples/                 # Example QR codes (for labs / docs)
    ├── phishing_qr.png
    ├── wifi_attack_qr.png
    ├── vcard_injection_qr.png
    └── sms_trigger_qr.png
