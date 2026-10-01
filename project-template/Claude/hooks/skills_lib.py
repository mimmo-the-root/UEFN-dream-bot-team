#!/usr/bin/env python3
"""
skills_lib.py — Skill Harness for the UEFN Claude Team Starter Kit (v1.81+).

Makes the GENRE skills (~/.claude/skills/genre/<slug>/) learn from every map you build, with you
approving each lesson. Pure Python standard library, no third-party packages, works on Windows,
macOS and Linux. Used three ways:
  * imported by agent-console-server.py (the Skills page),
  * run as a CLI by agents/hooks:  python skills_lib.py <command> ...   (prints JSON),
  * imported by tests.

Storage layout of one genre skill (three layers — see the README "Skills" section):

  genre/<slug>/SKILL.md            what the coder reads (the Learned-patterns block is GENERATED)
  genre/<slug>/pack/patterns.json  SHAREABLE layer: generalized patterns + support counts. No map
                                   names, codes, task IDs or numbers from your maps.
  genre/<slug>/local/              PRIVATE layer, never exported / never committed:
      maps.json      map key -> real map name (only used to show you where a lesson came from)
      support.json   pattern id -> which maps support / contradict it
      ledger.jsonl   why each pattern was born or changed (provenance)
      evidence/*.md  free-text notes per variant
      overlay.json   what you rejected (never proposed again)
      merged.json    which community packs were already merged (so counts are never double-added)
      inbox/*.json   lessons waiting for your approval
      usage.json     when the coder consulted this skill
      export_check.json  result of the last privacy check

Confidence ladder (computed from YOUR maps only; community support is shown but never counted):
  hypothesis (1 map) -> confirmed (2 maps) -> proven (3+ maps, or 2 + a retention metric).
  Any contradicting map turns a supported pattern into CONTESTED; nothing is silently overwritten.

Design ideas (verification gate, provenance ledger, secret redaction, archive-not-delete,
adherence counters) are adapted from tigerless-labs/autoharness (MIT) — see THIRD-PARTY-NOTICES.md.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import sys

SCHEMA = 1
TIERS = ("hypothesis", "confirmed", "proven")
STATUSES = ("active", "contested", "superseded")
ORIGINS = ("local", "community")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
VARIANT_RE = re.compile(r"^(\*|[a-z0-9][a-z0-9-]{0,40})$")
MAX_STATEMENT, MAX_CONDITION, MAX_ACTION = 200, 140, 200
MAX_PATTERNS_PER_PACK = 200
BEGIN, END = "<!-- PATTERNS:BEGIN -->", "<!-- PATTERNS:END -->"


# ----------------------------------------------------------------------------- paths / io
def skills_root():
    return os.environ.get("UEFN_SKILLS_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "skills")


def genre_root():
    return os.path.join(skills_root(), "genre")


def _slug(slug):
    if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug):
        raise ValueError("invalid genre slug: %r" % (slug,))
    return slug


def gdir(slug):
    return os.path.join(genre_root(), _slug(slug))


def ldir(slug):
    return os.path.join(gdir(slug), "local")


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today():
    return datetime.date.today().isoformat()


def _inside(base, path):
    """Single gate for file access: return the real path of `path` only if it stays inside `base`
    (symlinks and '..' are resolved first). Raises ValueError otherwise, so a blocked path is a
    visible error and never looks like a missing file."""
    root = os.path.realpath(base)
    full = os.path.realpath(path)
    # realpath + startswith on the separator-terminated root: the check static analyzers recognize,
    # and it also rejects a sibling such as /skills-evil when the root is /skills.
    if full != root and not full.startswith(root.rstrip(os.sep) + os.sep):
        raise ValueError("path outside allowed directory")
    return full


def _safe_skills_path(path):
    return _inside(skills_root(), path)


def _read_json(path, default, base=None):
    full = _inside(base or skills_root(), path)
    try:
        with open(full, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):  # missing or corrupt file -> default
        return default


def _write_json(path, obj, base=None):
    full = _inside(base or skills_root(), path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    tmp = _inside(os.path.dirname(full), full + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, full)


def _append_jsonl(path, obj, base=None):
    _append_text(path, json.dumps(obj, ensure_ascii=False) + "\n", base)


def _read_jsonl(path, base=None):
    full = _inside(base or skills_root(), path)
    out = []
    try:
        with open(full, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        pass
    except OSError:
        pass
    return out


def _append_text(path, text, base=None):
    full = _inside(base or skills_root(), path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "a", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _write_text(path, text, base=None):
    full = _inside(base or skills_root(), path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _makedirs(path, base=None):
    os.makedirs(_inside(base or skills_root(), path), exist_ok=True)


def _listdir(path, base=None):
    return os.listdir(_inside(base or skills_root(), path))


def _remove_file(path, base=None):
    os.remove(_inside(base or skills_root(), path))


def _isfile(path, base=None):
    try:
        return os.path.isfile(_inside(base or skills_root(), path))
    except ValueError:
        return False


def _isdir(path, base=None):
    try:
        return os.path.isdir(_inside(base or skills_root(), path))
    except ValueError:
        return False


# Paths the owner types on the command line (a pack file to merge, a folder to export into) are
# legitimately OUTSIDE the skills root, so they get their own narrow checks instead of _inside().
_MAX_USER_FILE = 2 * 1024 * 1024


def _user_file(path):
    """An existing .json file chosen by the owner. Returns its real path or raises ValueError."""
    if not isinstance(path, str) or not path.strip() or "\x00" in path:
        raise ValueError("pack file path is empty or invalid")
    full = os.path.realpath(path)
    if not full.lower().endswith(".json"):
        raise ValueError("pack file must be a .json file")
    if not os.path.isfile(full):
        raise ValueError("pack file not found: %s" % os.path.basename(full))
    if os.path.getsize(full) > _MAX_USER_FILE:
        raise ValueError("pack file is too large (limit %d KB)" % (_MAX_USER_FILE // 1024))
    return full


def _read_user_json(path):
    full = _user_file(path)
    with open(full, "r", encoding="utf-8") as f:
        return json.load(f)


def _user_dir(path):
    """A directory chosen by the owner to export into (may not exist yet). Returns its real path."""
    if not isinstance(path, str) or not path.strip() or "\x00" in path:
        raise ValueError("export folder path is empty or invalid")
    full = os.path.realpath(path)
    if os.path.dirname(full) == full:
        raise ValueError("refusing to export into a filesystem root")
    if os.path.exists(full) and not os.path.isdir(full):
        raise ValueError("export path is a file, not a folder")
    return full


# ----------------------------------------------------------------------------- text safety
# Secret / PII rules adapted from autoharness redaction_rules.toml (MIT). Over-redaction is fine.
_SECRET_RULES = [
    ("aws_access_key_id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("github_token", re.compile(r"gh[posru]_[A-Za-z0-9]{20,}")),
    ("slack_token", re.compile(r"xox[abprs]-[A-Za-z0-9-]{10,}")),
    ("bearer_token", re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{20,}")),
    ("api_key_assignment", re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9._\-/+]{12,}")),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
]
# Things that must never appear in a SHAREABLE pattern.
_SHARE_RULES = [
    ("url", re.compile(r"(?i)https?://|www\.")),
    ("code_or_markup", re.compile(r"`|<[A-Za-z/!]|\{\{|\$\(")),
    ("tool_reference", re.compile(r"(?i)mcp__|\bBash\(|\bWrite\(|\bEdit\(|tool_use|<tool")),
    ("shell_command", re.compile(r"(?i)\brm\s+-rf|\bsudo\b|\bcurl\b|\bwget\b|powershell|invoke-|cmd\.exe|\bchmod\b")),
    ("instruction_to_ai", re.compile(
        r"(?i)ignore (all |any |the )?(previous|prior|above|earlier)|disregard|system prompt|"
        r"forget (all|everything)|you must (not )?(ignore|reveal)|act as\b|jailbreak|developer message|"
        r"new instructions|override (the )?(rules|instructions)")),
    ("map_code", re.compile(r"\b\d{4}-\d{4}-\d{4}\b")),
    ("task_or_bug_id", re.compile(r"\b[TB]-\d{2,4}\b")),
    ("control_chars", re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")),
]


def redact(text):
    out = text
    for name, rx in _SECRET_RULES:
        out = rx.sub("[REDACTED:%s]" % name, out)
    return out


def text_findings(text, deny_terms=()):
    """Reasons a string is NOT safe to put in a shareable pattern. Empty list = safe."""
    found = []
    if not isinstance(text, str):
        return ["not_a_string"]
    for name, rx in _SECRET_RULES + _SHARE_RULES:
        if rx.search(text):
            found.append(name)
    low = text.lower()
    for term in deny_terms:
        t = (term or "").strip().lower()
        if len(t) >= 3 and t in low:
            found.append("private_term")
            break
    return found


# ----------------------------------------------------------------------------- patterns
def _norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower()).strip(" .")


def pattern_id(variant, condition, action):
    h = hashlib.sha1(("%s|%s|%s" % (_norm(variant), _norm(condition), _norm(action))).encode("utf-8")).hexdigest()
    return "p-" + h[:12]


def _map_key(name):
    return hashlib.sha1(_norm(name).encode("utf-8")).hexdigest()[:10]


def tier_for(n_for, metric_backed=False):
    if n_for >= 3 or (n_for >= 2 and metric_backed):
        return "proven"
    if n_for >= 2:
        return "confirmed"
    return "hypothesis"


def recompute(pat, sup):
    """Derive tier/status/counts of one pattern from its local support record."""
    s = sup.get(pat["id"], {})
    n_for, n_against = len(s.get("for", [])), len(s.get("against", []))
    if pat.get("origin") == "local" or s:
        pat["support"] = n_for
        pat["against"] = n_against
        pat["tier"] = tier_for(n_for, bool(s.get("metric_backed")))
        if n_for >= 1 and n_against >= 1:
            pat["status"] = "contested"
        elif pat.get("conflicts_with"):
            pat["status"] = "contested"
        elif pat.get("status") != "superseded":
            pat["status"] = "active"
    return pat


def validate_pattern(p, deny_terms=()):
    """Deterministic gate. Returns a list of (field, reason); empty = OK."""
    f = []
    if not isinstance(p, dict):
        return [("pattern", "not_an_object")]
    if not re.fullmatch(r"p-[0-9a-f]{12}", str(p.get("id", ""))):
        f.append(("id", "bad_format"))
    if not VARIANT_RE.fullmatch(str(p.get("variant", ""))):
        f.append(("variant", "bad_format"))
    for field, limit in (("statement", MAX_STATEMENT), ("condition", MAX_CONDITION), ("action", MAX_ACTION)):
        v = p.get(field)
        if not isinstance(v, str) or not v.strip():
            f.append((field, "empty"))
            continue
        if len(v) > limit:
            f.append((field, "too_long(>%d)" % limit))
        for r in text_findings(v, deny_terms):
            f.append((field, r))
    if p.get("tier") not in TIERS:
        f.append(("tier", "unknown"))
    if p.get("status") not in STATUSES:
        f.append(("status", "unknown"))
    for k in ("support", "against", "community_support"):
        if k in p and (not isinstance(p[k], int) or isinstance(p[k], bool) or p[k] < 0 or p[k] > 100000):
            f.append((k, "bad_number"))
    if not f and p.get("id") != pattern_id(p.get("variant"), p.get("condition"), p.get("action")):
        f.append(("id", "does_not_match_content"))
    return f


# ----------------------------------------------------------------------------- store
def _pack_path(slug):
    return os.path.join(gdir(slug), "pack", "patterns.json")


def init_genre(slug):
    """Create the pack/ + local/ layers for a genre skill if missing. Idempotent."""
    slug = _slug(slug)
    _makedirs(os.path.join(gdir(slug), "pack"))
    for sub in ("inbox", "evidence"):
        _makedirs(os.path.join(ldir(slug), sub))
    if not _isfile(_pack_path(slug)):
        _write_json(_pack_path(slug), {"schema": SCHEMA, "genre": slug, "revision": 0, "patterns": []})
    skill = os.path.join(gdir(slug), "SKILL.md")
    if not _isfile(skill):
        _write_text(skill, "---\ngenre_slug: %s\nstatus: draft\nlast_updated: %s\n---\n\n# Genre Skill: %s\n\n"
                    "Fresh genre skill. Content appears only when you approve lessons learned from real maps.\n"
                    % (slug, _today(), slug))
    render_skill(slug)
    return {"ok": True, "genre": slug}


def load_pack(slug):
    pack = _read_json(_pack_path(slug), None)
    if not isinstance(pack, dict) or not isinstance(pack.get("patterns"), list):
        pack = {"schema": SCHEMA, "genre": slug, "revision": 0, "patterns": []}
    return pack


def save_pack(slug, pack):
    pack["schema"] = SCHEMA
    pack["genre"] = slug
    pack["revision"] = int(pack.get("revision", 0)) + 1
    _write_json(_pack_path(slug), pack)


def _support(slug):
    return _read_json(os.path.join(ldir(slug), "support.json"), {})


def _save_support(slug, sup):
    _write_json(os.path.join(ldir(slug), "support.json"), sup)


def _maps(slug):
    return _read_json(os.path.join(ldir(slug), "maps.json"), {})


def _remember_map(slug, name):
    m = _maps(slug)
    k = _map_key(name)
    if k not in m:
        m[k] = {"name": name.strip(), "first_seen": _today()}
        _write_json(os.path.join(ldir(slug), "maps.json"), m)
    return k


def _overlay(slug):
    return _read_json(os.path.join(ldir(slug), "overlay.json"), {"rejected": [], "rejected_support": []})


def _ledger(slug, action, pid, reason, extra=None):
    e = {"ts": _now(), "action": action, "pattern": pid, "reason": reason}
    if extra:
        e.update(extra)
    _append_jsonl(os.path.join(ldir(slug), "ledger.jsonl"), e)


def _deny_terms(slug):
    return [v.get("name", "") for v in _maps(slug).values()]


def _find(pack, pid):
    for p in pack["patterns"]:
        if p.get("id") == pid:
            return p
    return None


# ----------------------------------------------------------------------------- SKILL.md render
def _frontmatter_split(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
    if not m:
        return None, text
    return m.group(1), m.group(2)


def render_skill(slug):
    """Regenerate the Learned-patterns block of SKILL.md from pack/patterns.json."""
    slug = _slug(slug)
    base_dir = gdir(slug)
    path_real = _inside(base_dir, os.path.join(base_dir, "SKILL.md"))
    try:
        with open(path_real, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        text = "---\ngenre_slug: %s\n---\n\n# Genre Skill: %s\n" % (slug, slug)
    fm, body = _frontmatter_split(text)
    if fm is None:
        fm, body = "genre_slug: %s" % slug, text
    pack = load_pack(slug)
    pats = [p for p in pack["patterns"] if p.get("status") != "superseded"]

    def line(p):
        tag = " (community)" if p.get("origin") == "community" else ""
        return "- [%s] When %s → %s%s — %d map(s)" % (p["variant"], _norm(p["condition"]), p["action"].strip(" ."), tag, p.get("support", 0))

    groups = [("Proven", "follow as a rule", [p for p in pats if p["status"] == "active" and p["tier"] == "proven"]),
              ("Confirmed", "follow by default; say why if you deviate", [p for p in pats if p["status"] == "active" and p["tier"] == "confirmed"]),
              ("Hypothesis", "only a suggestion; tell the owner it is unproven", [p for p in pats if p["status"] == "active" and p["tier"] == "hypothesis"]),
              ("Contested", "evidence conflicts; show both options to the owner and ask", [p for p in pats if p["status"] == "contested"])]
    out = [BEGIN, "## Learned patterns (generated — do not edit by hand)",
           "",
           "These come from maps the owner actually built and approved. Patterns the owner has not approved are not listed. "
           "Match the confidence to how you use each one."]
    if not pats:
        out += ["", "_Nothing learned yet. Patterns appear here only after the owner approves a lesson from a real map._"]
    for name, how, items in groups:
        if items:
            out += ["", "### %s — %s" % (name, how)] + [line(p) for p in items]
    out.append(END)
    block = "\n".join(out)
    if BEGIN in body and END in body:
        body = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), lambda _m: block, body, flags=re.S)
    else:
        body = body.rstrip() + "\n\n" + block + "\n"
    counts = {t: sum(1 for p in pats if p["status"] == "active" and p["tier"] == t) for t in TIERS}
    counts["contested"] = sum(1 for p in pats if p["status"] == "contested")
    keys = {"last_updated": _today(),
            "pattern_counts": "proven=%d confirmed=%d hypothesis=%d contested=%d" % (
                counts["proven"], counts["confirmed"], counts["hypothesis"], counts["contested"])}
    lines = fm.splitlines()
    for k, v in keys.items():
        for i, ln in enumerate(lines):
            if ln.startswith(k + ":"):
                lines[i] = "%s: %s" % (k, v)
                break
        else:
            lines.append("%s: %s" % (k, v))
    tmp_real = _inside(base_dir, path_real + ".tmp")
    with open(tmp_real, "w", encoding="utf-8", newline="\n") as f:
        f.write("---\n" + "\n".join(lines) + "\n---\n\n" + body.lstrip("\n"))
    os.replace(tmp_real, path_real)


# ----------------------------------------------------------------------------- proposals
def _inbox_dir(slug):
    return os.path.join(ldir(slug), "inbox")


def _save_proposal(slug, prop):
    _write_json(os.path.join(_inbox_dir(slug), prop["id"] + ".json"), prop)


def _say_new(slug, variant, statement):
    return "In %s / %s: %s" % (slug, variant, statement)


def propose(slug, variant, condition, action, statement, map_name, stance="for", tasks=(), note="", metric_backed=False):
    """Queue a lesson learned from a real map. Nothing is applied until the owner approves it."""
    slug = _slug(slug)
    init_genre(slug)
    if stance not in ("for", "against"):
        return {"ok": False, "error": "stance must be 'for' or 'against'"}
    if not (map_name or "").strip():
        return {"ok": False, "error": "map_name is required (it stays on this computer)"}
    if not VARIANT_RE.fullmatch(variant or ""):
        return {"ok": False, "error": "variant must be a lowercase slug or '*'"}
    pid = pattern_id(variant, condition, action)
    deny = _deny_terms(slug) + [map_name.strip()]
    cand = {"id": pid, "variant": variant, "statement": statement.strip(), "condition": condition.strip(),
            "action": action.strip(), "tier": "hypothesis", "status": "active", "origin": "local"}
    findings = validate_pattern(cand, deny)
    if findings:
        return {"ok": False, "error": "pattern failed the safety/format check", "findings": findings,
                "hint": "Generalize it: no map names, codes, task/bug IDs, links or commands in the statement."}
    ov = _overlay(slug)
    mk = _map_key(map_name)
    if pid in ov.get("rejected", []) and stance == "for":
        return {"ok": True, "skipped": "you rejected this pattern before"}
    if "%s:%s" % (pid, mk) in ov.get("rejected_support", []):
        return {"ok": True, "skipped": "you rejected this evidence before"}
    pack, sup = load_pack(slug), _support(slug)
    existing = _find(pack, pid)
    s = sup.get(pid, {"for": [], "against": []})
    if existing is None:
        if stance == "against":
            return {"ok": False, "error": "cannot contradict a pattern that does not exist yet"}
        kind = "new_pattern"
        say = _say_new(slug, variant, statement.strip())
    elif stance == "for":
        if mk in s.get("for", []):
            return {"ok": True, "skipped": "this map already supports the pattern"}
        kind = "support_added"
        old = tier_for(len(s.get("for", [])), bool(s.get("metric_backed")))
        new = tier_for(len(s.get("for", [])) + 1, bool(s.get("metric_backed") or metric_backed))
        say = ("The pattern “%s” showed up again on %s. If you approve, it goes from %s to %s."
               % (existing["statement"], map_name.strip(), old.capitalize(), new.capitalize())
               if old != new else
               "The pattern “%s” showed up again on %s. If you approve, its support grows to %d maps."
               % (existing["statement"], map_name.strip(), len(s.get("for", [])) + 1))
    else:
        if mk in s.get("against", []):
            return {"ok": True, "skipped": "this map already contradicts the pattern"}
        kind = "contradiction"
        say = ("%s did the opposite of the pattern “%s”. I will mark it Contested instead of changing it; "
               "both stay visible until more maps decide." % (map_name.strip(), existing["statement"]))
    prop = {"id": "pr-" + hashlib.sha1(("%s|%s|%s" % (kind, pid, mk)).encode()).hexdigest()[:10],
            "kind": kind, "genre": slug, "variant": variant, "pattern_id": pid, "pattern": cand,
            "say": say, "map_name": map_name.strip(), "map_key": mk, "stance": stance,
            "tasks": [str(t) for t in tasks], "note": redact(note or ""), "metric_backed": bool(metric_backed),
            "created": _now()}
    if _isfile(os.path.join(_inbox_dir(slug), prop["id"] + ".json")):
        return {"ok": True, "skipped": "already waiting for your approval", "proposal": prop["id"]}
    _save_proposal(slug, prop)
    return {"ok": True, "proposal": prop["id"], "kind": kind}


def list_proposals(slug=None):
    slugs = [_slug(slug)] if slug else _genres()
    out = []
    for s in slugs:
        d = _inbox_dir(s)
        if _isdir(d):
            for fn in sorted(_listdir(d)):
                if fn.endswith(".json"):
                    p = _read_json(os.path.join(d, fn), None)
                    if isinstance(p, dict) and p.get("id"):
                        out.append(p)
    out.sort(key=lambda p: p.get("created", ""))
    return out


def _evidence_note(slug, variant, map_name, text):
    path = os.path.join(ldir(slug), "evidence", "%s.md" % (variant if variant != "*" else "general"))
    _append_text(path, "\n## %s — %s\n%s\n" % (map_name, _today(), text))


def _apply_support(slug, pack, sup, pid, mk, stance, metric_backed=False):
    s = sup.setdefault(pid, {"for": [], "against": []})
    lst = s.setdefault(stance, [])
    if mk not in lst:
        lst.append(mk)
    if metric_backed:
        s["metric_backed"] = True
    p = _find(pack, pid)
    if p:
        recompute(p, sup)


def _proposal_path(slug, proposal_id):
    """Path of an EXISTING proposal file. The file name comes from the inbox listing, never from the caller."""
    inbox = _inbox_dir(slug)
    if _isdir(inbox):
        for fn in _listdir(inbox):
            if fn == str(proposal_id) + ".json":
                try:
                    return _inside(inbox, os.path.join(inbox, fn))
                except ValueError:
                    return None
    return None


def _remove_proposal_file(slug, ppath):
    inbox = _inbox_dir(slug)
    target = _inside(inbox, ppath)
    if not target.endswith(".json") or not _isfile(target):
        raise ValueError("invalid proposal file")
    _remove_file(target, base=inbox)


def act(slug, proposal_id, action, statement=None, exclude=()):
    """Owner decision on one queued proposal: approve | edit | reject."""
    slug = resolve_genre(slug)
    if action not in ("approve", "edit", "reject"):
        return {"ok": False, "error": "action must be approve, edit or reject"}
    if not re.fullmatch(r"pr-[0-9a-f]{10}", str(proposal_id)):
        return {"ok": False, "error": "bad proposal id"}
    ppath = _proposal_path(slug, proposal_id)
    if not ppath:
        return {"ok": False, "error": "proposal not found (already handled?)"}
    prop = _read_json(ppath, None)
    if not prop:
        return {"ok": False, "error": "proposal not found (already handled?)"}
    pack, sup, ov = load_pack(slug), _support(slug), _overlay(slug)
    kind, pid = prop["kind"], prop.get("pattern_id")

    if action == "reject":
        if kind == "pack_update":
            m = _read_json(os.path.join(ldir(slug), "merged.json"), {})
            m.setdefault("skipped", []).append({"source": prop["source"], "version": prop.get("version")})
            _write_json(os.path.join(ldir(slug), "merged.json"), m)
        elif kind in ("new_pattern", "community_new"):
            ov.setdefault("rejected", []).append(pid)
        else:
            ov.setdefault("rejected_support", []).append("%s:%s" % (pid, prop.get("map_key")))
        _write_json(os.path.join(ldir(slug), "overlay.json"), ov)
        _ledger(slug, "reject", pid or prop["id"], "owner rejected " + kind)
        _remove_proposal_file(slug, ppath)
        return {"ok": True, "result": "rejected"}

    if action == "edit":
        if not statement or kind not in ("new_pattern",):
            return {"ok": False, "error": "only a new pattern's wording can be edited"}
        prop["pattern"]["statement"] = statement.strip()
        if validate_pattern(prop["pattern"], _deny_terms(slug) + [prop.get("map_name", "")]):
            return {"ok": False, "error": "edited wording failed the safety check",
                    "findings": validate_pattern(prop["pattern"], _deny_terms(slug) + [prop.get("map_name", "")])}

    if kind == "new_pattern":
        pat = dict(prop["pattern"])
        pat.update({"origin": "local", "created": _today(), "support": 0, "against": 0})
        pack["patterns"].append(pat)
        mk = _remember_map(slug, prop["map_name"])
        _apply_support(slug, pack, sup, pid, mk, "for", prop.get("metric_backed", False))
        _evidence_note(slug, pat["variant"], prop["map_name"],
                       "New pattern approved: %s\n%s" % (pat["statement"], prop.get("note", "")))
    elif kind in ("support_added", "contradiction"):
        mk = _remember_map(slug, prop["map_name"])
        _apply_support(slug, pack, sup, pid, mk, prop["stance"], prop.get("metric_backed", False))
        _evidence_note(slug, prop["variant"], prop["map_name"], "%s evidence for pattern %s. %s" % (
            "Supporting" if prop["stance"] == "for" else "CONTRADICTING", pid, prop.get("note", "")))
    elif kind == "pack_update":
        res = _apply_pack_update(slug, pack, sup, prop, set(exclude or ()))
        _save_support(slug, sup)
        save_pack(slug, pack)
        render_skill(slug)
        _remove_proposal_file(slug, ppath)
        return {"ok": True, "result": "merged", "applied": res}
    else:
        return {"ok": False, "error": "unknown proposal kind"}

    _save_support(slug, sup)
    save_pack(slug, pack)
    _ledger(slug, "approve", pid, kind, {"map_key": prop.get("map_key"), "tasks": prop.get("tasks", [])})
    render_skill(slug)
    _remove_proposal_file(slug, ppath)
    return {"ok": True, "result": "approved"}


# ----------------------------------------------------------------------------- community packs
def export_pack(slug, out_dir):
    """Write the SHAREABLE pack, but only if the privacy check passes."""
    chk = check(slug)
    if not chk["ok"]:
        return {"ok": False, "error": "privacy check failed — nothing exported", "findings": chk["findings"]}
    try:
        out_root = _user_dir(out_dir)
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    pack = load_pack(slug)
    items = []
    for p in pack["patterns"]:
        if p.get("status") == "superseded" or p.get("support", 0) < 1:
            continue
        item = {k: p[k] for k in ("id", "variant", "statement", "condition", "action", "tier", "status") if k in p}
        item["support"] = p.get("support", 0)
        items.append(item)
    out = {"schema": SCHEMA, "genre": slug, "pack_version": int(pack.get("revision", 0)),
           "exported_at": _now(), "patterns": items}
    path = os.path.join(out_root, slug, "patterns.json")
    _write_json(path, out, base=out_root)
    return {"ok": True, "path": path, "patterns": len(items)}


def _norm_key(variant, condition):
    return _norm(variant) + "|" + _norm(condition)


def merge_pack(slug, pack_obj, source):
    """Validate an incoming (community) pack and queue ONE proposal describing what would change.
    Nothing in your skill changes until you approve; your own evidence always wins."""
    slug = _slug(slug)
    init_genre(slug)
    if not isinstance(pack_obj, dict) or pack_obj.get("schema") != SCHEMA or pack_obj.get("genre") != slug \
            or not isinstance(pack_obj.get("patterns"), list):
        return {"ok": False, "error": "not a valid pack for genre %r (schema/genre mismatch)" % slug}
    if len(pack_obj["patterns"]) > MAX_PATTERNS_PER_PACK:
        return {"ok": False, "error": "pack too large"}
    source = re.sub(r"[^A-Za-z0-9._ -]", "", str(source))[:60] or "community"
    version = pack_obj.get("pack_version")
    m = _read_json(os.path.join(ldir(slug), "merged.json"), {})
    if any(s.get("source") == source and s.get("version") == version for s in m.get("skipped", [])):
        return {"ok": True, "skipped": "you skipped this version before"}
    pack, sup, ov = load_pack(slug), _support(slug), _overlay(slug)
    deny = _deny_terms(slug)
    new, known, conflicts, rejected = [], [], [], []
    last = m.get("sources", {}).get(source, {})
    by_key = {_norm_key(p["variant"], p["condition"]): p for p in pack["patterns"]}
    for raw in pack_obj["patterns"]:
        clean = {k: raw.get(k) for k in ("id", "variant", "statement", "condition", "action", "tier", "status", "support")
                 if isinstance(raw, dict)}
        if not isinstance(raw, dict):
            rejected.append({"id": None, "findings": [("pattern", "not_an_object")]})
            continue
        clean.setdefault("support", 0)
        clean["tier"] = clean["tier"] if clean["tier"] in TIERS else "hypothesis"
        clean["status"] = clean["status"] if clean["status"] in STATUSES else "active"
        fnd = validate_pattern(clean, deny)
        if fnd:
            rejected.append({"id": clean.get("id"), "findings": fnd})
            continue
        if clean["id"] in ov.get("rejected", []):
            continue
        loc = _find(pack, clean["id"])
        if loc:
            delta = clean["support"] - int(last.get(clean["id"], 0))
            if delta != 0:
                known.append({"id": clean["id"], "statement": loc["statement"], "delta": delta, "support": clean["support"]})
            continue
        other = by_key.get(_norm_key(clean["variant"], clean["condition"]))
        item = {k: clean[k] for k in ("id", "variant", "statement", "condition", "action", "support")}
        if other:
            item["conflicts_with"] = other["id"]
            item["local_statement"] = other["statement"]
            conflicts.append(item)
        else:
            new.append(item)
    if not (new or known or conflicts):
        return {"ok": True, "skipped": "nothing new in this pack", "rejected": rejected}
    pid = "pu-%s-%s" % (version, source)
    prop = {"id": "pr-" + hashlib.sha1(("pack|%s|%s" % (source, version)).encode()).hexdigest()[:10],
            "kind": "pack_update", "genre": slug, "source": source, "version": version,
            "new": new, "known": known, "conflicts": conflicts, "rejected": rejected, "pattern_id": pid,
            "say": "%s pack v%s is available. Nothing has changed on your computer yet." % (source, version),
            "created": _now()}
    _save_proposal(slug, prop)
    return {"ok": True, "proposal": prop["id"], "new": len(new), "known": len(known),
            "conflicts": len(conflicts), "rejected": len(rejected)}


def _apply_pack_update(slug, pack, sup, prop, exclude):
    m = _read_json(os.path.join(ldir(slug), "merged.json"), {})
    src = m.setdefault("sources", {}).setdefault(prop["source"], {})
    n_new = n_known = n_conf = 0
    for it in prop["new"]:
        if it["id"] in exclude or _find(pack, it["id"]):
            continue
        pack["patterns"].append({"id": it["id"], "variant": it["variant"], "statement": it["statement"],
                                 "condition": it["condition"], "action": it["action"], "tier": "hypothesis",
                                 "status": "active", "origin": "community", "support": 0, "against": 0,
                                 "community_support": it["support"], "created": _today()})
        src[it["id"]] = it["support"]
        n_new += 1
        _ledger(slug, "community_add", it["id"], "from %s v%s" % (prop["source"], prop["version"]))
    for it in prop["known"]:
        if it["id"] in exclude:
            continue
        p = _find(pack, it["id"])
        if p:
            p["community_support"] = max(0, int(p.get("community_support", 0)) + it["delta"])
            src[it["id"]] = it["support"]
            n_known += 1
    for it in prop["conflicts"]:
        if it["id"] in exclude or _find(pack, it["id"]):
            continue
        pack["patterns"].append({"id": it["id"], "variant": it["variant"], "statement": it["statement"],
                                 "condition": it["condition"], "action": it["action"], "tier": "hypothesis",
                                 "status": "contested", "origin": "community", "support": 0, "against": 0,
                                 "community_support": it["support"], "conflicts_with": it["conflicts_with"],
                                 "created": _today()})
        src[it["id"]] = it["support"]
        n_conf += 1
        _ledger(slug, "community_conflict", it["id"], "conflicts with %s" % it["conflicts_with"])
    src["_version"] = prop["version"]
    _write_json(os.path.join(ldir(slug), "merged.json"), m)
    return {"new": n_new, "known": n_known, "conflicts": n_conf}


# ----------------------------------------------------------------------------- privacy check
def check(slug=None):
    """Privacy/format check run before anything is exported. Writes local/export_check.json."""
    slugs = [resolve_genre(slug)] if slug else _genres()
    findings = []
    for s in slugs:
        deny = _deny_terms(s)
        pack = load_pack(s)
        for p in pack["patterns"]:
            if p.get("status") == "superseded":
                continue
            for field, reason in validate_pattern(p, deny):
                findings.append({"genre": s, "pattern": p.get("id"), "field": field, "reason": reason})
        result = {"ts": _now(), "ok": not [f for f in findings if f["genre"] == s],
                  "findings": len([f for f in findings if f["genre"] == s])}
        if _isdir(ldir(s)):
            _write_json(os.path.join(ldir(s), "export_check.json"), result)
    return {"ok": not findings, "ts": _now(), "findings": findings}


# ----------------------------------------------------------------------------- usage
def consult(slug):
    """Record that the coder read this genre skill (called by a PreToolUse Read hook)."""
    slug = _slug(slug)
    if not _isdir(ldir(slug)):
        return {"ok": False, "error": "genre not initialised"}
    p = os.path.join(ldir(slug), "usage.json")
    u = _read_json(p, {"total": 0, "days": []})
    u["total"] = int(u.get("total", 0)) + 1
    u["days"] = (u.get("days", []) + [_today()])[-3000:]
    _write_json(p, u)
    return {"ok": True}


def consult_from_path(file_path):
    """If file_path is inside genre/<slug>/, count one consultation for that genre."""
    try:
        rel = os.path.relpath(os.path.abspath(file_path), os.path.abspath(genre_root()))
    except ValueError:
        return {"ok": False}
    parts = rel.replace("\\", "/").split("/")
    if len(parts) >= 2 and parts[0] != ".." and SLUG_RE.fullmatch(parts[0]) and "local" not in parts[1:2]:
        return consult(parts[0])
    return {"ok": False}


# ----------------------------------------------------------------------------- summary (server)
def resolve_genre(value):
    """Map a requested genre onto an EXISTING genre directory. The returned name is taken from the
    filesystem listing, never from the caller's string, so request data cannot steer a file path."""
    if isinstance(value, str):
        for g in _genres():
            if g == value:
                return g
    raise ValueError("unknown genre")


def _genres():
    root = genre_root()
    if not _isdir(root):
        return []
    return sorted(d for d in _listdir(root)
                  if SLUG_RE.fullmatch(d) and _isdir(os.path.join(root, d)))


def summary():
    """Everything the Skills page shows — computed only from real local files."""
    genres, pending = [], list_proposals()
    totals = {"maps": 0, "patterns": 0, "proven": 0, "confirmed": 0, "hypothesis": 0, "contested": 0}
    days = [(datetime.date.today() - datetime.timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    week = {d: 0 for d in days}
    all_maps, check_ok, check_ts, variants_seen = set(), True, None, set()
    last_learned = None
    for s in _genres():
        pack, sup, maps = load_pack(s), _support(s), _maps(s)
        usage = _read_json(os.path.join(ldir(s), "usage.json"), {"total": 0, "days": []})
        for d in usage.get("days", []):
            if d in week:
                week[d] += 1
        c = {t: 0 for t in TIERS}
        c["contested"] = 0
        pats = []
        for p in pack["patterns"]:
            if p.get("status") == "superseded":
                continue
            recompute(p, sup) if p.get("origin") == "local" else None
            if p["status"] == "contested":
                c["contested"] += 1
            else:
                c[p["tier"]] += 1
            variants_seen.add(p["variant"])
            pats.append({k: p.get(k) for k in ("id", "variant", "statement", "condition", "action", "tier", "status",
                                               "origin", "support", "against", "community_support", "conflicts_with")})
        led = _read_jsonl(os.path.join(ldir(s), "ledger.jsonl"))
        ll = led[-1]["ts"] if led else None
        if ll and (not last_learned or ll > last_learned):
            last_learned = ll
        ec = _read_json(os.path.join(ldir(s), "export_check.json"), None)
        if ec:
            check_ts = max(check_ts or "", ec.get("ts", ""))
            if not ec.get("ok"):
                check_ok = False
        for k in maps:
            all_maps.add((s, k))
        genres.append({"slug": s, "maps": len(maps), "counts": c, "patterns": pats, "last_learned": ll,
                       "consulted": int(usage.get("total", 0)),
                       "pending": sum(1 for p in pending if p["genre"] == s),
                       "variants": sorted({p["variant"] for p in pats})})
        for k in ("proven", "confirmed", "hypothesis", "contested"):
            totals[k] += c[k]
        totals["patterns"] += len(pats)
    totals["maps"] = len(all_maps)
    community = sum(1 for p in pending if p["kind"] == "pack_update")
    oldest = min((p["created"] for p in pending), default=None)
    return {"root": genre_root(), "root_exists": _isdir(genre_root()), "genres": genres, "totals": totals,
            "pending": pending, "pending_lessons": len(pending) - community, "pending_packs": community,
            "oldest_pending": oldest, "variants": len(variants_seen), "last_learned": last_learned,
            "usage_week": [week[d] for d in days], "usage_week_total": sum(week.values()),
            "never_used": sum(1 for g in genres if g["patterns"] and g["consulted"] == 0),
            "privacy": {"checked": check_ts is not None, "ok": check_ok, "ts": check_ts}}


# ----------------------------------------------------------------------------- CLI
def _cli(argv=None):
    ap = argparse.ArgumentParser(prog="skills_lib.py", description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("summary")
    s = sub.add_parser("init"); s.add_argument("genre")
    s = sub.add_parser("render"); s.add_argument("genre")
    s = sub.add_parser("check"); s.add_argument("genre", nargs="?")
    s = sub.add_parser("export"); s.add_argument("genre"); s.add_argument("out_dir")
    s = sub.add_parser("merge"); s.add_argument("genre"); s.add_argument("pack_file"); s.add_argument("--source", default="")
    s = sub.add_parser("consult"); s.add_argument("genre")
    s = sub.add_parser("consult-path"); s.add_argument("file_path")
    sub.add_parser("consult-hook")  # reads a Claude Code hook payload (JSON) from stdin
    s = sub.add_parser("proposals"); s.add_argument("genre", nargs="?")
    s = sub.add_parser("patterns"); s.add_argument("genre")  # exact wording of existing patterns (reuse it to add support)
    s = sub.add_parser("act"); s.add_argument("genre"); s.add_argument("proposal")
    s.add_argument("action", choices=["approve", "edit", "reject"]); s.add_argument("--statement")
    s.add_argument("--exclude", action="append", default=[])
    s = sub.add_parser("propose")
    s.add_argument("genre"); s.add_argument("--variant", required=True)
    s.add_argument("--condition", required=True); s.add_argument("--action", required=True, dest="act_")
    s.add_argument("--statement", required=True); s.add_argument("--map", required=True, dest="map_name")
    s.add_argument("--stance", default="for", choices=["for", "against"])
    s.add_argument("--task", action="append", default=[]); s.add_argument("--note", default="")
    s.add_argument("--metric-backed", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "summary":
            r = summary()
        elif a.cmd == "init":
            r = init_genre(a.genre)
        elif a.cmd == "render":
            r = (render_skill(a.genre) or {"ok": True})
        elif a.cmd == "check":
            r = check(a.genre)
        elif a.cmd == "export":
            r = export_pack(a.genre, a.out_dir)
        elif a.cmd == "merge":
            obj = _read_user_json(a.pack_file)
            r = merge_pack(a.genre, obj, a.source or os.path.basename(os.path.dirname(os.path.abspath(a.pack_file))))
        elif a.cmd == "consult":
            r = consult(a.genre)
        elif a.cmd == "consult-path":
            r = consult_from_path(a.file_path)
        elif a.cmd == "consult-hook":
            try:
                payload = json.load(sys.stdin)
                r = consult_from_path((payload.get("tool_input") or {}).get("file_path") or "")
            except (ValueError, AttributeError):
                r = {"ok": False}
            return 0  # a hook must never fail
        elif a.cmd == "proposals":
            r = list_proposals(a.genre)
        elif a.cmd == "patterns":
            r = [{k: p.get(k) for k in ("id", "variant", "condition", "action", "statement", "tier", "status")}
                 for p in load_pack(_slug(a.genre))["patterns"]]
        elif a.cmd == "act":
            r = act(a.genre, a.proposal, a.action, a.statement, a.exclude)
        else:
            r = propose(a.genre, a.variant, a.condition, a.act_, a.statement, a.map_name, a.stance,
                        a.task, a.note, a.metric_backed)
    except (ValueError, OSError) as e:
        r = {"ok": False, "error": str(e)}
    # Redact secret-looking strings before anything reaches stdout/logs (clear-text logging fix).
    print(redact(json.dumps(r, indent=2, ensure_ascii=False)))
    return 0 if not (isinstance(r, dict) and r.get("ok") is False) else 1


if __name__ == "__main__":
    sys.exit(_cli())
