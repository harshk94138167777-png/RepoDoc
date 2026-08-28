import re
from typing import List, Tuple
from .models import FileInfo, SecurityFinding

PATTERNS = [
    # (Regex, Category, Confidence, Explanation)
    (re.compile(r'(?i)(?:api_?key|secret|token|password)[\s:=]+[\'"]([A-Za-z0-9_\-]{16,})[\'"]'), "API Key or Token", "HIGH", "A variable name suggests an API key or token was hardcoded."),
    (re.compile(r'-----BEGIN [A-Z]+ PRIVATE KEY-----'), "Private Key", "HIGH", "A private cryptographic key is present."),
    (re.compile(r'https?://[a-zA-Z0-9_\-]+:[a-zA-Z0-9_\-]+@[a-zA-Z0-9_\-\.]+'), "Credential URL", "HIGH", "A URL contains embedded basic authentication credentials."),
    (re.compile(r'(sk-[a-zA-Z0-9]{20,})'), "Potential API Key", "HIGH", "Pattern matches common cloud API keys (e.g., sk-...).")
]

def redact(value: str) -> str:
    if len(value) <= 5:
        return "***"
    return value[:3] + "..." + value[-2:]

def scan_security(files: List[FileInfo]) -> List[SecurityFinding]:
    findings = []
    
    for f in files:
        if f.is_binary:
            continue
            
        # Check .env
        if f.filename.startswith(".env"):
            findings.append(SecurityFinding(
                filepath=f.relative_path,
                line_number=0,
                category="Environment File",
                confidence="HIGH",
                explanation="An environment file (e.g., .env) is checked in. This often contains secrets.",
                redacted_value="N/A"
            ))

        try:
            with open(f.path, 'r', encoding='utf-8', errors='ignore') as file:
                for line_idx, line in enumerate(file):
                    for pattern, category, confidence, explanation in PATTERNS:
                        match = pattern.search(line)
                        if match:
                            # For private key header, the match is the whole header
                            val_to_redact = match.group(1) if len(match.groups()) > 0 else match.group(0)
                            
                            findings.append(SecurityFinding(
                                filepath=f.relative_path,
                                line_number=line_idx + 1,
                                category=category,
                                confidence=confidence,
                                explanation=explanation,
                                redacted_value=redact(val_to_redact)
                            ))
        except Exception:
            pass
            
    return findings
