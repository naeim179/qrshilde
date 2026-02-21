# URL Scanner for QR payloads
import base64
from playwright.sync_api import sync_playwright

def scan_url_deeply(url: str):
    """
    زيارة الرابط فعلياً، التقاط صورة، وسحب النص.
    يعيد قاموساً يحتوي على المسار للصورة والنص المستخرج.
    """
    print(f"[*] Launching Headless Browser to scan: {url}")
    
    data = {
        "title": None,
        "text_content": None,
        "screenshot_path": "site_evidence.png",
        "error": None
    }

    try:
        with sync_playwright() as p:
            # تشغيل متصفح كروم خفي
            browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
            
            # تمويه المتصفح ليبدو كمستخدم حقيقي
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = context.new_page()

            # الذهاب للموقع (مع مهلة 10 ثواني)
            page.goto(url, timeout=10000, wait_until="domcontentloaded")
            
            # استخراج المعلومات
            data["title"] = page.title()
            data["text_content"] = page.inner_text("body")[:1000].replace("\n", " ")

            # التقاط صورة الدليل
            page.screenshot(path=data["screenshot_path"])
            print("[+] Screenshot captured.")

            browser.close()

    except Exception as e:
        print(f"[!] Scanning failed: {e}")
        data["error"] = str(e)

    return data