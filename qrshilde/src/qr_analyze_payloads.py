# Analyze QR content for attacks
import re

class PayloadAnalyzer:
    """
    يقوم هذا الكلاس بتحليل النص محلياً للبحث عن:
    1. تسريب بيانات حساسة (API Keys, Tokens).
    2. أنماط هجوم معروفة (SQLi, XSS, Command Injection).
    """
    def __init__(self):
        self.patterns = {
            # كشف التوكنات والأسرار
            "JWT Token": r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+',
            "Google API Key": r'AIza[0-9A-Za-z-_]{35}',
            "Private Key": r'-----BEGIN (?:RSA|DSA|EC|PGP) PRIVATE KEY-----',
            "AWS Access Key": r'AKIA[0-9A-Z]{16}',
            
            # كشف الهجمات
            "SQL Injection": r'(?i)(\' OR 1=1|UNION SELECT|DROP TABLE|--)',
            "XSS Payload": r'(?i)(<script>|javascript:|onerror=)',
            "Command Injection": r'(?i)(;|\||&&|\$\(|\`)(cat|nc|wget|curl|rm|whoami)',
            "Path Traversal": r'(\.\./\.\./|/etc/passwd|c:\\windows)',
            
            # هجمات QR خاصة
            "Wifi Config": r'(?i)WIFI:.*',
            "Suspicious Scheme": r'(?i)(tel:|sms:|facetime:)'
        }

    def scan(self, text):
        findings = []
        risk_score = 0
        
        for name, pattern in self.patterns.items():
            if re.search(pattern, text):
                findings.append(f"⚠️ DETECTED: {name}")
                risk_score += 1
        
        return findings, risk_score