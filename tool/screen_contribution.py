#!/usr/bin/env python3
"""screen_contribution.py - deterministic screening of one community lesson (the three free-text fields).

screen(doc) -> {"verdict": "pass" | "flag" | "block", "reasons": [..]}
  block = signs of an attempt to instruct the assistant or to smuggle something (links, commands, hidden characters...).
  flag  = soft signs (speaks to the reader, identifier not in official_names.json): a human or the classifier looks at it.
Text is normalized with NFKC first, so look-alike letters cannot hide a phrase. This is one layer of several (see the spec)."""
import json, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = ("statement", "condition", "action")
# Lessons are plain English: only printable ASCII and a few typographic marks. Anything else (Cyrillic or other look-alike letters,
# combining marks, variation selectors, zero-width and bidi characters, control characters, newlines) is blocked, so it cannot hide a phrase.
ALLOWED = re.compile(r"^[\x20-\x7e\u2018\u2019\u201c\u201d\u2013\u2014\u2026\u00d7]*$")
LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s", "!": "i", "|": "i"})
SQUASH_PHRASES = ("ignoreprevious", "ignoreallprevious", "ignoreallinstruction", "ignoretheabove", "ignoreyour", "disregardprevious", "disregardtheabove",
                  "disregardall", "forgetyour", "forgeteverything", "systemprompt", "newinstruction", "jailbreak", "donottell", "dontmentionthis", "fromnowon",
                  "youarenow", "overridethe", "overrideyour", "bypassthe", "bypassyour", "withoutasking", "withoutconfirmation", "withoutpermission", "withoutreview")
BIDI = set("\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069\u200e\u200f\u061c")
BLOCK = [
    ("link", re.compile(r"(?i)(https?:|ftp:|file:|www\.)|\b[a-z0-9-]+(\.|\[\.\]|\(\.\)|\s+dot\s+)(com|net|org|io|dev|gg|ly|app|xyz|ru|cn|tk|me|co|info|ai|sh|zip|mov|top|club|site|online|link|click|to|cc|ws|su|pw|biz|us|uk|de|fr|gl|ml|ga|cf|gq|cloud|page|run|pro|vip|ink|work|tech|store|shop|live|fun|icu|rest|cam|buzz)\b|\[\.\]|\(\.\)")),
    ("markdown_link_or_image", re.compile(r"\]\(|!\[|<a\s|<img|<script|</?[a-z][a-z0-9]*>")),
    ("command", re.compile(r"(?i)\b(curl|wget|powershell|pwsh|bash|sudo|chmod|chown|invoke-expression|iex|eval|exec|cmd\.exe|rm\s+-rf|del\s+/[sq]|format\s+c:)\b")),
    ("encoded_blob", re.compile(r"[A-Za-z0-9+/=_-]{40,}")),
    ("path", re.compile(r"(?i)[a-z]:\\|\\\\|(?<![\w.])~/|\.\./|(?<![\w/])/(home|users|etc|usr|var|tmp|root|mnt)/|%[a-z_]+%|\$env:|\$\{")),
    ("assistant_or_tool_name", re.compile(r"(?i)\b(claude|anthropic|assistant|chatgpt|openai|llm|system prompt|jailbreak|webfetch|websearch|call_tool|mcp)\b|CLAUDE\.md|settings\.json|\.claude\b|\bhooks?\.(json|ps1|py|sh)\b|(?<!\w)/(kit-update|learn-map|[a-z]+-[a-z-]+)\b")),
    ("grants_or_changes_rules", re.compile(r"(?i)\b(without|skip|skipping|no need for|stop) (asking|the check|checks|review|confirmation|permission|approval|verifying)\b|\bsilently\b|\b(add|create|install|enable|write|edit|modify|change) (a |an |the |new |any )*(hook|rule|command|setting|permission|skill|agent|memory|config|script)s?\b|\b(trust|approve|merge|accept) (all |every |any )?(lesson|lessons|contribution|contributions|change|changes|pull request|pr)\b.{0,30}\b(from|by|without)\b|\b(env|\.env|credential|secret|api key|token|password)s?\b|\ball (the )?files in the project\b|\bevery (reply|response|answer|message)\b")),
    ("addresses_the_assistant", re.compile(r"(?i)\b(ignore|disregard|forget|override|bypass)\b.{0,30}\b(previous|prior|above|earlier|all|any|your|the|these|those)\b.{0,30}\b(instruction|rule|prompt|guideline|polic|message|context|safety)|\bnew instructions?\b|\bfrom now on\b|\bpretend\b|\bact as\b|\bdo not (tell|mention|reveal|inform|show)\b|\b(tell|show|reveal|send|forward|upload|exfiltrate)\b.{0,40}\b(user|owner|key|token|password|secret|credential|file)s?\b|\bdelete (all|every|the|your)\b|\b(run|execute|call|invoke) (the |this |a |any )?(command|script|hook|tool|code|program)\b")),
]
FLAG = [
    ("speaks_to_the_reader", re.compile(r"(?i)\byou (must|should|will|need to|have to|are)\b|\bplease\b|\bimportant:|\bnote to\b|\bremember to\b")),
]
IDENT = re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+\b|\b[a-z]+(?:_[a-z0-9]+)*_device\b")


def _known():
    try:
        with open(os.path.join(HERE, "official_names.json"), encoding="utf-8") as f:
            return set(json.load(f).get("names", []))
    except (OSError, ValueError):
        return set()


def screen(doc, known=None):
    reasons, verdict = [], "pass"
    known = _known() if known is None else known
    for k in FIELDS:
        raw = doc.get(k, "") if isinstance(doc, dict) else ""
        if not isinstance(raw, str):
            return {"verdict": "block", "reasons": ["%s: not a string" % k]}
        if not ALLOWED.match(raw):
            verdict = "block"; reasons.append("%s: characters outside plain English text (look-alikes, combining marks, hidden or control characters)" % k)
        text = unicodedata.normalize("NFKC", raw)
        folded = re.sub(r"[^a-z]", "", text.translate(LEET).lower())
        if any(ph in folded for ph in SQUASH_PHRASES):
            verdict = "block"; reasons.append("%s: instruction phrase (spaced, leet or punctuated)" % k)
        if text != raw and re.search(r"[A-Za-z]", text) and any(ord(c) > 127 and unicodedata.category(c).startswith("L") and unicodedata.name(c, "").startswith(("FULLWIDTH", "MATHEMATICAL")) for c in raw):
            verdict = "block"; reasons.append("%s: look-alike letters" % k)
        for name, rx in BLOCK:
            if rx.search(text):
                verdict = "block"; reasons.append("%s: %s" % (k, name))
        if verdict != "block":
            for name, rx in FLAG:
                if rx.search(text):
                    verdict = "flag"; reasons.append("%s: %s" % (k, name))
            for tok in sorted(set(IDENT.findall(text))):
                if tok not in known:
                    verdict = "flag"; reasons.append("%s: identifier %s is not in official_names.json" % (k, tok))
    return {"verdict": verdict, "reasons": reasons}


if __name__ == "__main__":
    bad = 0
    for p in sys.argv[1:]:
        with open(p, encoding="utf-8") as f:
            r = screen(json.load(f))
        print("%s: %s %s" % (p, r["verdict"], "; ".join(r["reasons"])))
        bad += r["verdict"] == "block"
    sys.exit(1 if bad else 0)
