#!/usr/bin/env python3
"""debug_bundle.py - build a sanitized debug zip (logs, problems, config, versions) to attach to a GitHub issue.

API: build_bundle(project=None, out=None) -> dict {ok, path, files, redactions, findings, error}
     sanitize_text(text, project=None) -> str     scan_text(text) -> list of finding names
Flow: collect files -> sanitize (secrets and personal paths become placeholders) -> scan the sanitized
text again -> if the scan still finds anything the zip is NOT written (ok=False). Never raises. Stdlib only.
CLI: python tools/debug_bundle.py [project_dir] [out.zip]     exit 0 = zip written, 1 = refused
"""
import json, os, platform, re, sys, time, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_config  # noqa: E402

MAX_FILE = 512 * 1024  # keep the tail of big logs
SENSITIVE_KEY = re.compile(r"(key|token|secret|passw|pwd|login|user(name)?|e-?mail|auth|cookie|credential)", re.I)

# (name, regex, replacement) - applied in order by sanitize_text
RULES = [
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(-----END [A-Z ]*PRIVATE KEY-----|\Z)", re.S), "<REDACTED:private-key>"),
    ("bearer", re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}"), r"\1 <REDACTED:token>"),
    ("api_key", re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9_-]{8,}"), "<REDACTED:api-key>"),
    ("key_token", re.compile(r"\bkey_[A-Za-z0-9_-]{8,}"), "<REDACTED:api-key>"),
    ("github", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{16,})"), "<REDACTED:token>"),
    ("slack", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{8,}"), "<REDACTED:token>"),
    ("aws", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"), "<REDACTED:token>"),
    ("google", re.compile(r"\bAIza[A-Za-z0-9_-]{30,}"), "<REDACTED:token>"),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}"), "<REDACTED:token>"),
    ("url_login", re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://)[^/\s:@]+:[^/\s@]+@"), r"\1<REDACTED:login>@"),
    ("assignment", re.compile(r"""(?ix)\b([\w.-]*(?:api[_-]?key|apikey|token|secret|passw(?:or)?d|pwd|login|username|user|auth(?:orization)?|cookie|credentials?)[\w.-]*)(["']?\s*[:=]\s*["']?)(?!<REDACTED)[^\s"',;}\]]{3,}"""), r"\1\2<REDACTED:value>"),
    ("email", re.compile(r"\b[\w.+-]+@(?!users\.noreply\.github\.com)[\w-]+(?:\.[\w-]+)+\b"), "<REDACTED:email>"),
    ("path_win", re.compile(r"(?i)\b[A-Z]:[\\/]+Users[\\/]+[^\\/\s\"']+"), r"<USER_HOME>"),
    ("path_unix", re.compile(r"(?<![\w.])/(?:Users|home)/(?!<)[^/\s\"']+"), r"<USER_HOME>"),
]
# after sanitizing, any of these still matching means the zip must not be written
SCAN = [(n, r) for n, r, _ in RULES if n not in ("assignment", "email", "url_login")] + [
    ("assignment", re.compile(r"""(?ix)\b[\w.-]*(?:api[_-]?key|apikey|token|secret|passw(?:or)?d|pwd|login|username)[\w.-]*["']?\s*[:=]\s*["']?(?!<REDACTED)[^\s"',;}\]]{3,}""")),
    ("url_login", re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://(?!<REDACTED)[^/\s:@]+:[^/\s@]+@")),
    ("email", re.compile(r"\b[\w.+-]+@(?!users\.noreply\.github\.com)[\w-]+(?:\.[\w-]+)+\b")),
]


def sanitize_text(text, project=None):
    counts = sanitize_counted(text, project)
    return counts[0]


def sanitize_counted(text, project=None):
    n = 0
    homes = {os.path.expanduser("~")}
    try:
        homes.add(os.path.abspath(kit_config.project_dir(project)))
    except Exception:
        pass
    for h in sorted((h for h in homes if h and len(h) > 3), key=len, reverse=True):
        for variant in {h, h.replace("\\", "/"), h.replace("/", "\\")}:
            c = text.count(variant)
            if c:
                n += c
                text = text.replace(variant, "<PROJECT_DIR>" if variant != os.path.expanduser("~") else "<USER_HOME>")
    for _name, rx, rep in RULES:
        text, c = rx.subn(rep, text)
        n += c
    return text, n


def scan_text(text):
    return [name for name, rx in SCAN if rx.search(text)]


def _sanitize_json_value(v):
    if isinstance(v, dict):
        return {k: ("<REDACTED:value>" if SENSITIVE_KEY.search(str(k)) and not isinstance(val, (dict, list, bool)) else _sanitize_json_value(val)) for k, val in v.items()}
    if isinstance(v, list):
        return [_sanitize_json_value(x) for x in v]
    return v


def _read(path):
    with open(path, "rb") as f:
        data = f.read()
    if len(data) > MAX_FILE:
        data = b"[... truncated, tail kept ...]\n" + data[-MAX_FILE:]
    return data.decode("utf-8", errors="replace")


def _kit_version(project_dir):
    try:
        with open(os.path.join(project_dir, "CHANGELOG.md"), encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.search(r"\d+\.\d+\.\d+", line) if line.startswith("#") else None
                if m:
                    return m.group(0)
    except Exception:
        pass
    return "unknown"


def collect(project=None):
    """Return {arcname: sanitized_text} and the redaction count."""
    pd = kit_config.project_dir(project)
    raw = {}
    logs = os.path.join(pd, "Claude", "logs")
    if os.path.isdir(logs):
        for name in sorted(os.listdir(logs)):
            p = os.path.join(logs, name)
            if os.path.isfile(p) and name.lower().endswith((".log", ".txt", ".md")):
                raw["logs/" + name] = _read(p)
    prob = os.path.join(pd, "Claude", "plan", "PROBLEMS-FROM-COD.md")
    if os.path.isfile(prob):
        raw["problems/PROBLEMS-FROM-COD.md"] = _read(prob)
    cfg = kit_config.path(project)
    if os.path.isfile(cfg):
        try:
            data = _sanitize_json_value(json.loads(_read(cfg)))
            raw["config/kit-settings.json"] = json.dumps(data, indent=2, ensure_ascii=False)
        except Exception:
            raw["config/kit-settings.json"] = _read(cfg)
    raw["versions.json"] = json.dumps({
        "kit_version": _kit_version(pd), "python": platform.python_version(),
        "platform": platform.system() + " " + platform.release(),
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }, indent=2)
    out, total = {}, 0
    for arc, text in raw.items():
        clean, n = sanitize_counted(text, project)
        out[arc], total = clean, total + n
    return out, total


def build_bundle(project=None, out=None):
    try:
        pd = kit_config.project_dir(project)
        out = out or os.path.join(pd, "Claude", "logs", "debug-bundle-%s.zip" % time.strftime("%Y%m%d-%H%M%S"))
        files, redactions = collect(project)
        findings = []
        for arc, text in files.items():
            findings += ["%s:%s" % (arc, n) for n in scan_text(text)]
            findings += ["%s:name" % arc for n in scan_text(arc)]
        if findings:
            return {"ok": False, "path": None, "files": [], "redactions": redactions, "findings": findings, "error": "scan found secrets, zip not written"}
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        tmp = out + ".tmp"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
            for arc, text in files.items():
                zi = zipfile.ZipInfo(arc, (2020, 1, 1, 0, 0, 0))
                zi.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(zi, text.encode("utf-8"))
        os.replace(tmp, out)
        return {"ok": True, "path": out, "files": sorted(files), "redactions": redactions, "findings": [], "error": None}
    except Exception as e:  # never raise
        return {"ok": False, "path": None, "files": [], "redactions": 0, "findings": [], "error": "%s: %s" % (type(e).__name__, e)}


def main(argv):
    r = build_bundle(argv[0] if argv else None, argv[1] if len(argv) > 1 else None)
    print(json.dumps(r, indent=2))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
