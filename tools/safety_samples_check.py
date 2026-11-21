#!/usr/bin/env python3
"""T-081/T-082/T-083: compare local safety verdicts with the paid model's verdicts.

Usage: python tools/safety_samples_check.py [path]
Default path: plan/safety-samples-copy.jsonl (at most 5 lines, no secrets).
A sample is a JSON object with an action text (action/text/tail; for the router's tail the last
non-empty transcript line is judged) and the paid verdict (paid_verdict/model_verdict/verdict/
response/block, or <block>yes</block> = block and <block>no</block> = allow anywhere in the
sample). The router's local_safety_verdict is the only verdict engine used; no LLM is called.
Exit 0 = every sample agrees, 1 = any disagreement or invalid/refused input.
"""
import json
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(ROOT, "plan", "safety-samples-copy.jsonl")
MAX_LINES = 5

SECRET_RES = [
    re.compile(r"sk-[A-Za-z0-9_\-]{10,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]{10,}"),
    re.compile(r"[A-Za-z0-9+/_\-]{40,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(?:api[_-]?key|secret|password|passwd|token|credential)\s*[:=]\s*[\"']?[^\s\"',]{8,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
]
ACTION_KEYS = ("action", "action_text", "text", "tail")
VERDICT_KEYS = ("paid_verdict", "model_verdict", "verdict", "response", "paid", "block")
SKIP_ACTION_RX = re.compile(r"^\s*(?:<block>|<category>|<reason>|</transcript>|assistant:)", re.I)
BLOCK_XML_RX = re.compile(r"<block\s*>\s*yes\s*</block\s*>", re.I)
ALLOW_XML_RX = re.compile(r"<block\s*>\s*no\s*</block\s*>", re.I)
BLOCK_WORDS = {"block", "blocked", "deny", "denied", "yes", "true"}
ALLOW_WORDS = {"allow", "allowed", "pass", "permit", "no", "false"}


def string_values(value):
    """Yield every string inside a parsed sample, including nested message content."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            for text in string_values(item):
                yield text
    elif isinstance(value, (list, tuple)):
        for item in value:
            for text in string_values(item):
                yield text


def secret_pattern(raw, entry):
    """Return the first secret pattern found, or None; check raw text and decoded values."""
    for text in [raw] + list(string_values(entry)):
        for rx in SECRET_RES:
            if rx.search(text):
                return rx.pattern
    return None


def read_samples(path):
    """Return (samples, errors); a secret or bad line stops the whole file before any verdict runs."""
    errors = []
    if not os.path.isfile(path):
        return [], ["missing file: %s" % path]
    with open(path, encoding="utf-8") as fh:
        raw_lines = [line for line in fh.read().splitlines() if line.strip()]
    if len(raw_lines) > MAX_LINES:
        return [], ["too many lines: %d (at most %d)" % (len(raw_lines), MAX_LINES)]
    samples = []
    for number, raw in enumerate(raw_lines, 1):
        try:
            entry = json.loads(raw)
        except ValueError:
            errors.append("line %d: invalid JSON" % number)
            continue
        if not isinstance(entry, dict):
            errors.append("line %d: sample is not a JSON object" % number)
            continue
        found = secret_pattern(raw, entry)
        if found:
            return [], ["REFUSED line %d: secret pattern found (nothing was judged)" % number]
        samples.append((number, entry))
    return samples, errors


def paid_verdict(entry):
    """Return 'block', 'allow', or None for the verdict the paid model returned."""
    for key in VERDICT_KEYS:
        if key not in entry:
            continue
        value = entry[key]
        if isinstance(value, bool):
            return "block" if value else "allow"
        if isinstance(value, (int, float)):
            return "block" if value else "allow"
        if isinstance(value, str):
            verdict = verdict_from_text(value)
            if verdict:
                return verdict
    for text in string_values(entry):
        verdict = verdict_from_text(text)
        if verdict:
            return verdict
    return None


def verdict_from_text(text):
    """Map verdict markup or a plain allow/block word to a single verdict."""
    has_block, has_allow = bool(BLOCK_XML_RX.search(text)), bool(ALLOW_XML_RX.search(text))
    if has_block and has_allow:
        return None
    if has_block:
        return "block"
    if has_allow:
        return "allow"
    word = text.strip().lower().strip("<>/ ").split()[:1]
    word = word[0] if word else ""
    if word in BLOCK_WORDS:
        return "block"
    if word in ALLOW_WORDS:
        return "allow"
    return None


def action_text(entry):
    """Return the action text, or a request dict for the router to unpack itself."""
    for key in ACTION_KEYS:
        value = entry.get(key)
        if not isinstance(value, str) or not value.strip():
            continue
        lines = [line.strip() for line in value.splitlines()
                 if line.strip() and not SKIP_ACTION_RX.match(line)]
        if lines:
            return lines[-1]
        return value.strip()
    if entry.get("messages") or entry.get("system"):
        return {"system": entry.get("system"), "messages": entry.get("messages", [])}
    return ""


def check(path, verdict_fn):
    """Print agreement per line and every disagreement; return (agree, total, errors)."""
    samples, errors = read_samples(path)
    print("safety samples: %s" % path)
    for error in errors:
        print("FAIL %s" % error)
    if errors:
        return 0, 0, errors
    agree, disagreements = 0, []
    for number, entry in samples:
        expected = paid_verdict(entry)
        if expected is None:
            errors.append("line %d: no paid verdict (allow/block) in sample" % number)
            print("FAIL line %d: no paid verdict (allow/block) in sample" % number)
            continue
        block, reason = verdict_fn(action_text(entry))
        local = "block" if block else "allow"
        if local == expected:
            agree += 1
            print("line %d: OK local=%s paid=%s" % (number, local, expected))
        else:
            disagreements.append((number, local, expected))
            print("line %d: DISAGREE local=%s paid=%s" % (number, local, expected))
    total = agree + len(disagreements)
    for number, local, expected in disagreements:
        print("DISAGREEMENT line %d: local %s vs paid %s" % (number, local, expected))
    if errors:
        return agree, total, errors
    print("agreement %d/%d" % (agree, total))
    if disagreements:
        print("FAIL %d disagreement(s)" % len(disagreements))
    else:
        print("PASS all %d sample(s) agree" % total)
    return agree, total, disagreements


def main(argv):
    path = os.path.abspath(argv[1]) if len(argv) > 1 else DEFAULT_PATH
    hooks = os.path.join(ROOT, "user-level-hooks")
    if hooks not in sys.path:
        sys.path.insert(0, hooks)
    os.environ.setdefault("DREAM_ROUTER_HOME", tempfile.mkdtemp(prefix="safety-samples-check-"))
    import dream_router
    agree, total, problems = check(path, dream_router.local_safety_verdict)
    return 0 if not problems and total and agree == total else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
