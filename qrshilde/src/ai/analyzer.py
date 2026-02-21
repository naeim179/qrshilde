import re, datetime, os, asyncio
from qrshilde.src.ai.openai_client import ask_model 
from qrshilde.src.tools.malicious_pattern_detector import scan_for_patterns
from qrshilde.src.tools.wifi_auto_connect_detector import detect_wifi_threats

async def capture_screenshot(url, report_id):
    """التقاط صورة للموقع المشبوه كدليل بصري"""
    try:
        from playwright.async_api import async_playwright
        screenshot_name = f"evidence_{report_id}.png"
        # المسار يجب أن يكون داخل static/uploads ليظهر في الويب
        screenshot_path = os.path.join("static", "uploads", screenshot_name)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            # انتظار 10 ثوانٍ كحد أقصى لتحميل الموقع
            await page.goto(url, timeout=10000, wait_until="networkidle")
            await page.screenshot(path=screenshot_path)
            await browser.close()
        return f"/static/uploads/{screenshot_name}"
    except Exception as e:
        print(f"[⚠️] Screenshot skipped: {e}")
        return None

async def analyze_qr_payload(payload, report_id):
    findings = []
    risk_score = 0
    payload_lower = payload.lower()

    # 1. القواعد المحلية (Local Rules)
    pattern_issues = scan_for_patterns(payload)
    if pattern_issues:
        findings.extend(pattern_issues)
        risk_score += 40

    brands = ["paypal", "google", "microsoft", "apple", "netflix", "binance"]
    for brand in brands:
        if brand in payload_lower and f"{brand}.com" not in payload_lower:
            findings.append(f"Phishing: Possible {brand.capitalize()} impersonation")
            risk_score += 60

    if any(word in payload_lower for word in ["urgent", "login", "verify", "update", "secure"]):
        findings.append("NLP: High-urgency intent detected")
        risk_score += 25

    # 2. التقاط صورة الموقع (Evidence)
    evidence_img = None
    if payload.startswith(("http", "www")):
        print(f"[*] Capturing screenshot for evidence...")
        evidence_img = await capture_screenshot(payload, report_id)

    # 3. استدعاء الذكاء الاصطناعي للتحليل العميق
    print(f"[*] Fetching AI Analysis...")
    ai_opinion = ask_model(f"Analyze this QR payload and provide a security verdict: {payload}")
    
    risk_score = min(risk_score, 100)
    category = "MALICIOUS" if risk_score >= 70 else "SUSPICIOUS" if risk_score >= 35 else "SAFE"

    return {
        "category": category,
        "risk_score": risk_score,
        "findings": findings,
        "ai_analysis": ai_opinion if ai_opinion else "AI Analysis unavailable.",
        "payload": payload,
        "evidence_img": evidence_img, # رابط صورة الموقع
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }