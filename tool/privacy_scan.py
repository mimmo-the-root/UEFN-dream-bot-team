#!/usr/bin/env python3
"""privacy_scan.py - fail if the repo contains something that must never be published.

Checks (every tracked-looking file under the repo root, .git excluded):
  1. real token formats (GitHub, Anthropic, OpenAI-style, AWS, Slack, Google, JWT, private keys)
  2. generic "api_key = <long value>" assignments (skipped under tests/, where fixtures live)
  3. personal absolute paths: C:\\Users\\<name>, /Users/<name>, /home/<name> (placeholders allowed)
  4. files that must not be committed: .mcp.json, .env*, *.pem, *.key, *.bak, *.verse, local/ data
  5. a user's e-mail address (noreply addresses and the placeholders are allowed)

Usage: python tool/privacy_scan.py [root]      exit 0 = clean, 1 = findings (printed)
Add an allowed line with the marker `privacy-scan: allow` in a comment on that line.
"""
import os, re, sys

ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKIP_DIRS = {".git", "__pycache__", "node_modules"}
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".zip", ".pdf", ".woff", ".woff2"}
ALLOW_MARK = "privacy-scan: allow"

TOKEN_RES = [
    ("GitHub token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{30,}\b")),
    ("Anthropic/OpenAI key", re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{24,}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}\b")),
    ("private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
]
GENERIC_RE = re.compile(r"""(?i)\b(?:api[_-]?key|secret|token|passw(?:or)?d)\b\s*[:=]\s*["']?([A-Za-z0-9_\-/+=]{20,})""")
PATH_RES = [
    re.compile(r"[A-Za-z]:\\+Users\\+([^\\/\s\"'`<>%$]+)"),
    re.compile(r"(?<![A-Za-z0-9_])/Users/([^/\s\"'`<>$]+)"),  # privacy-scan: allow
    re.compile(r"(?<![A-Za-z0-9_])/home/([^/\s\"'`<>$]+)"),  # privacy-scan: allow
]
PATH_OK = {"you", "user", "username", "your-name", "yourname", "name", "me", "public", "default", "runner", "<you>", "<user>", "claude", "x", "someone"}
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+\.)+[A-Za-z]{2,}\b")
EMAIL_OK_DOMAINS = {"example.com", "example.org", "users.noreply.github.com", "noreply.github.com", "anthropic.com", "github.com"}
BAD_NAMES = re.compile(r"(^|/)(\.mcp\.json|\.env(\..*)?|.*\.pem|.*\.key|.*\.bak|.*\.verse|.*\.uasset|.*\.umap)$")


def iter_files():
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            yield os.path.join(d, f)


def main():
    findings = []
    for p in iter_files():
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        if BAD_NAMES.search(rel) or re.search(r"(^|/)genre/[^/]+/local/", rel):
            findings.append((rel, 0, "file that must not be committed"))
            continue
        if os.path.splitext(p)[1].lower() in BINARY_EXT:
            continue
        try:
            text = open(p, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        in_tests = rel.startswith("tests/")
        for n, line in enumerate(text.splitlines(), 1):
            if ALLOW_MARK in line:
                continue
            for label, rx in TOKEN_RES:
                if rx.search(line):
                    findings.append((rel, n, label))
            if not in_tests and GENERIC_RE.search(line):
                v = GENERIC_RE.search(line).group(1)
                if not re.fullmatch(r"[A-Za-z_\-]+", v) and not v.startswith(("<", "$", "%")):
                    findings.append((rel, n, "secret-like assignment"))
            for rx in PATH_RES:
                for m in rx.finditer(line):
                    if m.group(1).lower() not in PATH_OK:
                        findings.append((rel, n, "personal path: " + m.group(0)))
            for m in EMAIL_RE.finditer(line):
                dom = m.group(0).split("@", 1)[1].lower()
                if dom not in EMAIL_OK_DOMAINS and not m.group(0).lower().startswith(("noreply@", "you@", "user@", "name@")):
                    findings.append((rel, n, "e-mail address: " + m.group(0)))
    if findings:
        print("privacy_scan: %d finding(s)" % len(findings))
        for rel, n, why in sorted(set(findings)):
            print("  %s%s  %s" % (rel, (":%d" % n) if n else "", why))
        return 1
    print("privacy_scan: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
