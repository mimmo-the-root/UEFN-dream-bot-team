#!/usr/bin/env python3
"""recipe_screen.py - format check and screening of a recipe that comes from somebody else (community) or goes to somebody else.

A recipe is followed by an agent and carries Verse code, so it is screened harder than a lesson: anything that looks like an instruction
for the assistant, a link, a command, a path, a hidden character or a secret BLOCKS it. Nothing here executes anything.
Used by skills_lib.py (what you receive and what you send) and by tool/ (the pull request check and the release).

  check(recipe) -> {"ok": bool, "reasons": [...]}
"""
import re, unicodedata

FIELDS = ("name", "kind", "use", "steps", "devices", "settings", "wiring", "files", "assets", "verify", "parent", "params")
KINDS = ("device", "mechanic", "template", "material")
LIST_FIELDS = ("steps", "devices", "settings", "wiring", "assets", "params")
MAX = {"name": 60, "kind": 12, "use": 300, "verify": 600, "parent": 200, "item": 400, "items": 80, "files": 12, "file_name": 80, "code": 40000}
PLAIN = re.compile(r"^[\x20-\x7e‘’“”–—…×]*$")
CODE_OK = re.compile(r"^[\x09\x0a\x0d\x20-\x7e -ɏ‘’“”–—…×→•]*$")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9 _-]{1,58}$")
FILE_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,78}\.verse$")
LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s", "!": "i", "|": "i"})
SQUASH = ("ignoreprevious", "ignoreallprevious", "ignoreallinstruction", "ignoretheabove", "ignoreyour", "disregardprevious", "disregardtheabove",
          "disregardall", "forgetyour", "forgeteverything", "systemprompt", "newinstruction", "jailbreak", "donottell", "dontmentionthis", "fromnowon",
          "youarenow", "overridethe", "overrideyour", "bypassthe", "bypassyour", "withoutasking", "withoutconfirmation", "withoutpermission", "withoutreview")
BLOCK_TEXT = [
    ("link", re.compile(r"(?i)(https?:|ftp:|file:|www\.)|\b[a-z0-9-]+(\.|\[\.\]|\(\.\)|\s+dot\s+)(com|net|org|io|dev|gg|ly|app|xyz|ru|cn|tk|me|co|info|ai|sh|zip|mov|top)\b")),
    ("markup", re.compile(r"\]\(|!\[|<a\s|<img|<script|</?[a-z][a-z0-9]*>")),
    ("command", re.compile(r"(?i)\b(curl|wget|powershell|pwsh|bash|sudo|chmod|chown|invoke-expression|iex|eval|exec|cmd\.exe|rm\s+-rf|del\s+/[sq]|format\s+c:)\b")),
    ("encoded_blob", re.compile(r"[A-Za-z0-9+/=_-]{40,}")),
    ("path", re.compile(r"(?i)[a-z]:\\|\\\\|(?<![\w.])~/|\.\./|(?<![\w/])/(home|users|etc|usr|var|tmp|root|mnt)/|%[a-z_]+%|\$env:|\$\{")),
    ("assistant_or_tool_name", re.compile(r"(?i)\b(claude|anthropic|assistant|chatgpt|openai|llm|system prompt|jailbreak|webfetch|websearch|call_tool|mcp)\b|CLAUDE\.md|settings\.json|\.claude\b|\bhooks?\.(json|ps1|py|sh)\b")),
    ("changes_rules", re.compile(r"(?i)\b(without|skip|skipping|no need for|stop) (asking|the check|checks|review|confirmation|permission|approval|verifying)\b|\bsilently\b|\b(add|create|install|enable|write|edit|modify|change) (a |an |the |new |any )*(hook|rule|command|setting|permission|skill|agent|memory|config|script)s?\b|\b(env|credential|secret|api key|token|password)s?\b|\ball (the )?files in the project\b|\bevery (reply|response|answer|message)\b")),
    ("addresses_the_assistant", re.compile(r"(?i)\b(ignore|disregard|forget|override|bypass)\b.{0,30}\b(previous|prior|above|earlier|all|any|your|the|these|those)\b.{0,30}\b(instruction|rule|prompt|guideline|polic|message|context|safety)|\bnew instructions?\b|\bfrom now on\b|\bpretend\b|\bact as\b|\bdo not (tell|mention|reveal|inform|show)\b|\b(tell|show|reveal|send|forward|upload|exfiltrate)\b.{0,40}\b(user|owner|key|token|password|secret|credential|file)s?\b|\bdelete (all|every|the|your)\b|\b(run|execute|call|invoke) (the |this |a |any )?(command|script|hook|tool|program)\b")),
]
SECRET = re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b|\bsk-(?:ant-)?[A-Za-z0-9_-]{24,}\b|\bAKIA[0-9A-Z]{16}\b|-----BEGIN [A-Z ]*PRIVATE KEY-----|\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}\b")
CODE_BLOCK = [("link in the code", re.compile(r"(?i)(https?:|ftp:|file:)//|\bwww\.")), ("personal path in the code", re.compile(r"(?i)[a-z]:\\\\+users|(?<![\w/])/(home|users)/")),
              ("assistant or tool name in the code", re.compile(r"(?i)\b(claude|anthropic|chatgpt|openai|system prompt|webfetch|websearch|call_tool)\b|CLAUDE\.md"))]


def _squash(text):
    return re.sub(r"[^a-z]", "", unicodedata.normalize("NFKC", text).translate(LEET).lower())


def _text(label, s, reasons, blob=True):
    if not isinstance(s, str):
        reasons.append("%s: not text" % label); return
    if not PLAIN.match(s):
        reasons.append("%s: characters outside plain English text" % label)
    t = unicodedata.normalize("NFKC", s)
    if any(p in _squash(t) for p in SQUASH):
        reasons.append("%s: instruction phrase" % label)
    for name, rx in BLOCK_TEXT:
        if name == "encoded_blob" and not blob:
            continue
        if rx.search(t):
            reasons.append("%s: %s" % (label, name))
    if SECRET.search(t):
        reasons.append("%s: a secret or an e-mail address" % label)


def check(recipe):
    r = []
    if not isinstance(recipe, dict):
        return {"ok": False, "reasons": ["not an object"]}
    for k in recipe:
        if k not in FIELDS:
            r.append("%s: unknown field" % k)
    name = recipe.get("name")
    if not isinstance(name, str) or not NAME_RE.match(name):
        r.append("name: lowercase words, 2 to 60 characters")
    if recipe.get("kind") not in KINDS:
        r.append("kind: one of %s" % ", ".join(KINDS))
    for k in ("use", "verify", "parent"):
        v = recipe.get(k, "")
        if len(str(v)) > MAX[k]:
            r.append("%s: too long" % k)
        _text(k, v, r)
    if not isinstance(recipe.get("steps"), list) or not recipe.get("steps"):
        r.append("steps: at least one step")
    for k in LIST_FIELDS:
        v = recipe.get(k, [])
        if not isinstance(v, list) or len(v) > MAX["items"]:
            r.append("%s: a list of at most %d lines" % (k, MAX["items"])); continue
        for i, it in enumerate(v):
            if isinstance(it, str) and len(it) > MAX["item"]:
                r.append("%s[%d]: too long" % (k, i))
            _text("%s[%d]" % (k, i), it, r, blob=(k != "assets"))   # asset lines are folder paths: long names are normal
    fl = recipe.get("files", [])
    if not isinstance(fl, list) or len(fl) > MAX["files"]:
        r.append("files: at most %d Verse files" % MAX["files"])
    else:
        for i, f in enumerate(fl):
            if not isinstance(f, dict) or set(f) != {"name", "code"} or not isinstance(f["name"], str) or not isinstance(f["code"], str):
                r.append("files[%d]: must be {name, code}" % i); continue
            if not FILE_RE.match(f["name"]):
                r.append("files[%d]: file name must end in .verse, letters digits _ . - only" % i)
            if len(f["code"]) > MAX["code"]:
                r.append("files[%d]: code longer than %d characters" % (i, MAX["code"]))
            if not CODE_OK.match(f["code"]):
                r.append("files[%d]: hidden or unusual characters in the code" % i)
            comments = "\n".join(re.findall(r"#[^\n]*|<#.*?#>", f["code"], re.S))
            if any(p in _squash(comments) for p in SQUASH):
                r.append("files[%d]: instruction phrase in a comment" % i)
            body = re.sub(r"\A(?:[ \t]*(?:#[^\n]*)?\r?\n)+", "", f["code"])   # the credits block at the top of a file may hold links (profiles of the author); a link anywhere else in the code blocks
            head = f["code"][:len(f["code"]) - len(body)]
            if head.count("\n") > 80:
                r.append("files[%d]: header comment longer than 80 lines" % i)
            for label, rx in CODE_BLOCK:
                if rx.search(body):
                    r.append("files[%d]: %s" % (i, label))
            if SECRET.search(f["code"]):
                r.append("files[%d]: a secret or an e-mail address in the code" % i)
    return {"ok": not r, "reasons": r[:30]}
