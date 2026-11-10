import os
import re
import math
from typing import List, Dict, Any, Tuple
from ..models import SecretFinding, SecretSeverity


# Shannon Entropy calculation for detecting randomized passwords and keys
def calculate_shannon_entropy(data: str) -> float:
    if not data:
        return 0.0
    entropy = 0.0
    length = len(data)
    frequencies: Dict[str, int] = {}
    for char in data:
        frequencies[char] = frequencies.get(char, 0) + 1
    for count in frequencies.values():
        prob = count / length
        entropy -= prob * math.log2(prob)
    return round(entropy, 3)


# High-value secret detection rules
SECRET_RULES: List[Dict[str, Any]] = [
    {
        "id": "AWS_KEY",
        "description": "AWS Access Key ID",
        "pattern": re.compile(r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}"),
        "severity": SecretSeverity.CRITICAL,
        "min_entropy": 2.5,
    },
    {
        "id": "GITHUB_PAT",
        "description": "GitHub Personal Access Token",
        "pattern": re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,255}"),
        "severity": SecretSeverity.CRITICAL,
        "min_entropy": 3.0,
    },
    {
        "id": "PRIVATE_KEY",
        "description": "Unencrypted Private Key Block",
        "pattern": re.compile(r"-----BEGIN (?:RSA|DSA|EC|OPENSSH|PGP) PRIVATE KEY-----"),
        "severity": SecretSeverity.CRITICAL,
        "min_entropy": 1.0,
    },
    {
        "id": "GOOGLE_API_KEY",
        "description": "Google Cloud / API Key",
        "pattern": re.compile(r"AIza[0-9A-Za-z\\-_]{35}"),
        "severity": SecretSeverity.HIGH,
        "min_entropy": 3.5,
    },
    {
        "id": "SLACK_TOKEN",
        "description": "Slack Token",
        "pattern": re.compile(r"xox[baprs]-[0-9a-zA-Z]{10,48}"),
        "severity": SecretSeverity.HIGH,
        "min_entropy": 3.0,
    },
    {
        "id": "JWT_TOKEN",
        "description": "JSON Web Token (JWT)",
        "pattern": re.compile(r"ey[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}"),
        "severity": SecretSeverity.MEDIUM,
        "min_entropy": 3.8,
    },
    {
        "id": "GENERIC_API_KEY",
        "description": "Generic High-Entropy Credential Assignment",
        "pattern": re.compile(
            r"""(?i)(?:api_key|secret|password|passwd|auth_token|access_token|private_key)\s*[:=]\s*['"]([A-Za-z0-9!@#$%^&*()_+\-=\[\]{}|~]{16,80})['"]"""
        ),
        "severity": SecretSeverity.HIGH,
        "min_entropy": 3.6,
    },
]

# Ignored paths during directory walk
IGNORE_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".pytest_cache", ".idea", ".vscode", "dist", "build", ".gemini"
}

IGNORE_EXTENSIONS = {
    ".pyc", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip",
    ".tar", ".gz", ".exe", ".dll", ".so", ".dylib", ".woff", ".woff2"
}


def mask_secret(secret: str) -> str:
    if len(secret) <= 8:
        return "****"
    return secret[:4] + "*" * (len(secret) - 8) + secret[-4:]


class SecretHunter:
    """Git and codebase leaked secrets scanner (TruffleHog / GitLeaks style)."""

    def scan_text(self, text: str, source_label: str = "inline_text") -> List[SecretFinding]:
        findings: List[SecretFinding] = []
        lines = text.splitlines()

        for line_no, line in enumerate(lines, start=1):
            for rule in SECRET_RULES:
                matches = rule["pattern"].finditer(line)
                for m in matches:
                    matched_str = m.group(0)
                    # If regex has capture group 1, check that value
                    if m.groups():
                        candidate = m.group(1)
                    else:
                        candidate = matched_str

                    entropy = calculate_shannon_entropy(candidate)
                    if entropy >= rule["min_entropy"]:
                        findings.append(
                            SecretFinding(
                                file_path=source_label,
                                line_number=line_no,
                                rule_id=rule["id"],
                                description=rule["description"],
                                matched_snippet=mask_secret(matched_str),
                                entropy=entropy,
                                severity=rule["severity"],
                            )
                        )
        return findings

    def scan_path(self, target_path: str, max_file_size_bytes: int = 1024 * 1024) -> List[SecretFinding]:
        results: List[SecretFinding] = []

        if os.path.isfile(target_path):
            return self._scan_single_file(target_path, max_file_size_bytes)

        if os.path.isdir(target_path):
            for root, dirs, files in os.walk(target_path):
                # Prune ignored directories in-place
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in IGNORE_EXTENSIONS:
                        continue
                    full_path = os.path.join(root, file)
                    results.extend(self._scan_single_file(full_path, max_file_size_bytes))

        return results

    def _scan_single_file(self, file_path: str, max_size: int) -> List[SecretFinding]:
        try:
            if os.path.getsize(file_path) > max_size:
                return []
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return self.scan_text(content, source_label=file_path)
        except Exception:
            return []
