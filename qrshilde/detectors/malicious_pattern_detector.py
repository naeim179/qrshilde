import re
from typing import Any

PATTERN_RULES: list[dict[str, Any]] = [
    # Dangerous URI schemes
    {
        "name": "dangerous_scheme_javascript",
        "category": "Dangerous Scheme",
        "regex": r"(?i)\bjavascript\s*:",
        "score": 35,
        "message": "Dangerous URI scheme 'javascript:' detected.",
    },
    {
        "name": "dangerous_scheme_data",
        "category": "Dangerous Scheme",
        "regex": r"(?i)\bdata\s*:",
        "score": 30,
        "message": "Dangerous URI scheme 'data:' detected.",
    },
    {
        "name": "dangerous_scheme_file",
        "category": "Dangerous Scheme",
        "regex": r"(?i)\b(?:file|vbscript|intent)\s*:",
        "score": 30,
        "message": "Potentially unsafe URI scheme detected (file/vbscript/intent).",
    },

    # XSS / script injection
    {
        "name": "xss_script_tag",
        "category": "XSS",
        "regex": r"(?i)<\s*script\b",
        "score": 30,
        "message": "Possible XSS payload: <script> tag detected.",
    },
    {
        "name": "xss_inline_handler",
        "category": "XSS",
        "regex": r"(?i)\bon(?:error|load|click|mouseover)\s*=",
        "score": 25,
        "message": "Possible XSS payload: inline event handler detected.",
    },
    {
        "name": "xss_encoded_script",
        "category": "XSS",
        "regex": r"(?i)%3c\s*script|%3c%2fscript|%3e",
        "score": 20,
        "message": "Encoded script/XSS markers detected.",
    },

    # SQL Injection
    {
        "name": "sqli_union_select",
        "category": "SQL Injection",
        "regex": r"(?i)\bunion\b\s+\bselect\b",
        "score": 30,
        "message": "Possible SQL injection pattern: UNION SELECT detected.",
    },
    {
        "name": "sqli_time_delay",
        "category": "SQL Injection",
        "regex": r"(?i)\bwaitfor\s+delay\b|\bsleep\s*\(",
        "score": 30,
        "message": "Possible time-based SQL injection pattern detected.",
    },
    {
        "name": "sqli_boolean_bypass",
        "category": "SQL Injection",
        "regex": r"(?i)(?:'|\")?\s*or\s+1\s*=\s*1",
        "score": 25,
        "message": "Possible SQL injection pattern: boolean bypass detected.",
    },

    # Command / shell injection
    {
        "name": "cmd_shell_pipe",
        "category": "Command Injection",
        "regex": r"(?i)\|\s*(?:bash|sh|cmd(?:\.exe)?)\b",
        "score": 35,
        "message": "Possible command injection: shell pipe execution detected.",
    },
    {
        "name": "cmd_dangerous_command",
        "category": "Command Injection",
        "regex": r"(?i)(?:;\s*|\&\&\s*)(?:rm\s+-rf|del\s+/f|format\s+[a-z]:|powershell(?:\.exe)?)",
        "score": 35,
        "message": "Possible command injection: dangerous system command detected.",
    },
    {
        "name": "cmd_download_exec",
        "category": "Command Injection",
        "regex": r"(?i)\b(?:curl|wget)\b.+(?:\||&&|;)\s*(?:bash|sh)\b",
        "score": 35,
        "message": "Possible command injection: download-and-execute pattern detected.",
    },

    # Path traversal / local file abuse
    {
        "name": "path_traversal",
        "category": "Path Traversal",
        "regex": r"(?:\.\./|\.\.\\)",
        "score": 20,
        "message": "Path traversal sequence detected (../ or ..\\).",
    },

    # Sensitive data exposure
    {
        "name": "private_key",
        "category": "Sensitive Data",
        "regex": r"(?i)BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY",
        "score": 40,
        "message": "Sensitive material detected: private key content.",
    },
    {
        "name": "password_assignment",
        "category": "Sensitive Data",
        "regex": r"(?i)\bpassword\s*[=:]",
        "score": 20,
        "message": "Sensitive credential pattern detected: password= / password: .",
    },
    {
        "name": "token_assignment",
        "category": "Sensitive Data",
        "regex": r"(?i)\b(?:api[_-]?key|access[_-]?token|secret)\s*[=:]",
        "score": 20,
        "message": "Sensitive token/key assignment detected.",
    },

    # Malicious file lure
    {
        "name": "dangerous_file_extension",
        "category": "Executable Lure",
        "regex": r"(?i)\.(?:exe|msi|apk|bat|cmd|ps1|jar|js|vbs)(?:$|[?#])",
        "score": 25,
        "message": "Potential executable or script file reference detected.",
    },
]


def scan_for_patterns_detailed(text: str) -> list[dict[str, Any]]:
    """
    Returns structured detections with category, score, and human-readable message.
    """
    content = text or ""
    findings: list[dict[str, Any]] = []
    seen: set[str] = set()

    for rule in PATTERN_RULES:
        if re.search(rule["regex"], content):
            if rule["name"] in seen:
                continue
            seen.add(rule["name"])
            findings.append(
                {
                    "name": rule["name"],
                    "category": rule["category"],
                    "score": int(rule["score"]),
                    "message": str(rule["message"]),
                    "pattern": str(rule["regex"]),
                }
            )

    return findings


def scan_for_patterns(text: str) -> list[str]:
    """
    Backward-compatible helper that returns only text messages.
    """
    return [item["message"] for item in scan_for_patterns_detailed(text)]