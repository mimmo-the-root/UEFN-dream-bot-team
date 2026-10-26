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
import shutil
import sys
import time
import urllib.parse

SCHEMA = 1
TIERS = ("hypothesis", "confirmed", "proven", "reference")
STATUSES = ("active", "contested", "superseded")
ORIGINS = ("local", "community", "official")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
VARIANT_RE = re.compile(r"^(\*|[a-z0-9][a-z0-9-]{0,40})$")
MAX_STATEMENT, MAX_CONDITION, MAX_ACTION = 200, 140, 200
MAX_PATTERNS_PER_PACK = 200
BEGIN, END = "<!-- PATTERNS:BEGIN -->", "<!-- PATTERNS:END -->"
INCOMING_TEXT = re.compile(r"^[\x20-\x7e\u2018\u2019\u201c\u201d\u2013\u2014\u2026\u00d7]*$")
SECTION_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,30}$")


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
    """Delete the file. If the system refuses (read-only, protected, no permission), park it in <profile>/_to_delete/<timestamp>/ for the owner to empty."""
    src = _inside(base or skills_root(), path)
    try:
        os.remove(src)
        return
    except PermissionError:
        pass
    except OSError:
        if not os.path.exists(src):
            raise
    park = os.path.join(os.path.dirname(os.path.realpath(skills_root())), "_to_delete", time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(park, exist_ok=True)
    dst, n = os.path.join(park, os.path.basename(src)), 1
    while os.path.exists(dst):
        n += 1
        dst = os.path.join(park, "%d-%s" % (n, os.path.basename(src)))
    shutil.move(src, dst)


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


def name_keys(name):
    """The map keys under which a project may have been named by an agent: the folder name as it is, with spaces for _ and -, without a
    leading root_ and without the word FAB. A recipe stores only the hash of the name, so these variants are how it finds its project again."""
    n = (name or "").strip()
    if not n:
        return set()
    out = {n}
    sp = re.sub(r"[_\-]+", " ", n).strip()
    out.add(sp)
    for v in list(out):
        w = re.sub(r"^root[ _\-]+", "", v, flags=re.I).strip()
        out.add(w)
        out.add(re.sub(r"(^|[ _\-])fab([ _\-]|$)", " ", w, flags=re.I).strip())
    return {_map_key(x) for x in out if x}


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
    if pat.get("origin") in ("local", "official") or s:
        pat["support"] = n_for
        pat["against"] = n_against
        if pat.get("origin") == "official":
            # Official (e.g. Epic template/doc) guidance: "reference" until one of the owner's own maps
            # backs it; the official source then counts as one map (1 owner map = confirmed, 2 = proven).
            pat["tier"] = "reference" if n_for == 0 else tier_for(n_for + 1, bool(s.get("metric_backed")))
        else:
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
    if "section" in p and not SECTION_RE.fullmatch(str(p.get("section"))):
        f.append(("section", "bad_format"))
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


def _proj_hash(project):
    """Short hash of a project folder: lets a map key be tied to its project without storing the path."""
    return hashlib.sha1(os.path.realpath(project).encode("utf-8")).hexdigest()[:10] if project else ""


def _remember_map(slug, name, ph=""):
    """ph = _proj_hash of the project the map belongs to (kept with the map so its published state can be found)."""
    m = _maps(slug)
    k = _map_key(name)
    if k not in m:
        m[k] = {"name": name.strip(), "first_seen": _today()}
        if ph:
            m[k]["project"] = ph
        _write_json(os.path.join(ldir(slug), "maps.json"), m)
    elif ph and m[k].get("project") != ph:
        m[k]["project"] = ph
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
        tag = " (community)" if p.get("origin") == "community" else (" (official reference)" if p.get("origin") == "official" else "")
        return "- [%s] When %s → %s%s — %d map(s)" % (p["variant"], p["condition"].strip(" ."), p["action"].strip(" ."), tag, p.get("support", 0))

    groups = [("Proven", "follow as a rule", [p for p in pats if p["status"] == "active" and p["tier"] == "proven"]),
              ("Confirmed", "follow by default; say why if you deviate", [p for p in pats if p["status"] == "active" and p["tier"] == "confirmed"]),
              ("Reference", "official guidance (e.g. Epic docs/templates), not yet validated in the owner's maps; use it as the documented way and verify in a playtest", [p for p in pats if p["status"] == "active" and p["tier"] == "reference"]),
              ("Hypothesis", "only a suggestion; tell the owner it is unproven", [p for p in pats if p["status"] == "active" and p["tier"] == "hypothesis"]),
              ("Contested", "evidence conflicts; show both options to the owner and ask", [p for p in pats if p["status"] == "contested"])]
    out = [BEGIN, "## Learned patterns (generated — do not edit by hand)",
           "",
           "To plan or build a map of this genre read `references/starter.md` FIRST: its \"Map anatomy\" section lists what the owner's maps are made of (layout, game loop, devices, rules, scoring, build order).",
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
            "pattern_counts": "proven=%d confirmed=%d reference=%d hypothesis=%d contested=%d" % (
                counts["proven"], counts["confirmed"], counts["reference"], counts["hypothesis"], counts["contested"])}
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
    render_starter(slug)


DEFAULT_SECTIONS = [  # the 8 sections every genre starter has, in neutral words; a genre with its own references/starter-sections.json overrides them
    {"id": "run-loop", "title": "Core loop", "questions": "What is one round/run/match; how does it start, end (win, loss, timeout) and restart? What is shared between players?"},
    {"id": "architecture", "title": "Architecture", "questions": "Which Verse files/classes own game state, transitions, player state, spawning, rewards? One owner per transition."},
    {"id": "devices", "title": "Devices in the level", "questions": "Which spawners, trackers, granters, barriers and UI devices exist; which are global and which per player; who wires them? (read them via the MCP when live)"},
    {"id": "progression", "title": "Progression", "questions": "What persists between rounds/runs and what resets; unlocks, currencies, difficulty or tier scaling. Numbers only from the owner or his maps' data."},
    {"id": "death-strategies", "title": "Strategies around death, defeat and progress", "questions": "Respawn/retry rules, paid retry or continue, rewards, boosts. Design strategies, learned as patterns with a variant."},
    {"id": "persistence", "title": "Persistence", "questions": "What is stored per player; what happens when data is not loaded yet or the player left."},
    {"id": "performance", "title": "Performance", "questions": "Item/NPC pools, listeners, per-frame work."},
    {"id": "launch-checklist", "title": "Launch checklist", "questions": "First 10 minutes of a new player, a full round, a death/defeat, a restart, two players at once, a player leaving mid-round."},
]


def starter_sections(slug):
    """Sections of the genre's starter (references/starter-sections.json): [{id, title, questions}]; the 8 default sections when the genre has none."""
    d = _read_json(os.path.join(gdir(slug), "references", "starter-sections.json"), None)
    out = []
    for x in (d or {}).get("sections", []) if isinstance(d, dict) else []:
        if isinstance(x, dict) and SECTION_RE.fullmatch(str(x.get("id", ""))) and x.get("title"):
            out.append({"id": x["id"], "title": str(x["title"]), "questions": str(x.get("questions", ""))})
    return out or [dict(x) for x in DEFAULT_SECTIONS]


PROFILE_VERSION = 1


def _pstr(x, n=300):
    return redact(str(x or "").strip())[:n]


def _plist(items, keys, nmax=40):
    out = []
    for it in (items if isinstance(items, list) else [])[:nmax]:
        if isinstance(it, str):
            it = {keys[0]: it}
        if isinstance(it, dict):
            row = {k: _pstr(it.get(k), 240) for k in keys}
            if row[keys[0]]:
                out.append(row)
    return out


def save_profile(slug, map_name, prof, project=None, map_key=None):
    """The blueprint of one map: what a map of this genre is made of (layout, game loop, devices, rules, scoring, build order) with the numbers
    observed in it. Private (local/profiles/, the map name is only hashed); the starter shows it as 'Map anatomy'. Replaces the previous
    profile of the same map. `project` (optional) gets a marker so the kit knows the blueprint was written."""
    slug = _slug(slug)
    gate = genre_gate(project)
    if gate:
        return gate
    init_genre(slug)
    if not (map_name or "").strip() or not isinstance(prof, dict):
        return {"ok": False, "error": "map_name and a JSON object are required"}
    clean = {"concept": _pstr(prof.get("concept"), 500),
             "layout": _plist(prof.get("layout"), ("element", "count", "note")),
             "loop": [_pstr(x, 240) for x in (prof.get("loop") or [])[:20] if x],
             "devices": _plist(prof.get("devices"), ("class", "count", "role", "settings", "wiring")),
             "rules": _plist(prof.get("rules"), ("when", "then", "numbers")),
             "verse": _plist(prof.get("verse"), ("component", "role", "api")),
             "scoring": [_pstr(x, 240) for x in (prof.get("scoring") or [])[:15] if x],
             "build_order": [_pstr(x, 240) for x in (prof.get("build_order") or [])[:25] if x],
             "unknown": [_pstr(x, 240) for x in (prof.get("unknown") or [])[:15] if x]}
    if not clean["concept"] or not (clean["layout"] or clean["devices"] or clean["loop"]):
        return {"ok": False, "error": "a profile needs a concept and at least one of layout, devices or loop"}
    mk = map_key or _map_key(map_name)
    if project and not map_key:  # one project = one map: the name passed on the command line must never create a second blueprint
        try:
            mark = json.load(open(os.path.join(project, "Claude", "docs", "map", "profile-learned.json"), encoding="utf-8-sig"))
            if isinstance(mark, dict) and mark.get("map_key") and _slug(mark.get("genre") or "") == slug:
                mk = str(mark["map_key"])
        except (OSError, ValueError):
            pass
    old = _read_json(os.path.join(ldir(slug), "profiles", mk + ".json"), None)
    label = (old or {}).get("label") or "Map %d" % (len(_profiles(slug)) + 1)
    var = _variant_name(prof.get("variant"))
    if not var and project:
        var = (_pread(project) or {}).get("variant", "")
    var = _canon_variant(slug, var) if var else var
    if var:
        clean["variant"] = var
    clean.update({"label": label, "map_key": mk, "updated": _today(), "v": PROFILE_VERSION})
    _write_json(os.path.join(ldir(slug), "profiles", mk + ".json"), clean)
    render_starter(slug)
    if project:
        try:
            mdir = os.path.join(project, "Claude", "docs", "map")
            os.makedirs(mdir, exist_ok=True)
            mpath = os.path.join(mdir, "profile-learned.json")
            old = {}
            try:
                old = json.load(open(mpath, encoding="utf-8-sig"))
                old = old if isinstance(old, dict) else {}
            except (OSError, ValueError):
                old = {}
            try:
                import verse_map
                fp = verse_map.profile_fingerprint(project, mdir)
            except Exception:
                fp = ""
            unk = len(clean.get("unknown") or [])
            tries = old.get("gap_tries", 0) if unk >= old.get("unknown_n", unk) else 0  # progress on the unknowns gives them new tries
            with open(mpath, "w", encoding="utf-8") as f:
                json.dump({"v": PROFILE_VERSION, "at": _today(), "genre": slug, "map_key": mk, "fp": fp, "unknown_n": unk,
                           "gap_tries": tries, "lessons": old.get("lessons", 0), "lessons_asked": old.get("lessons_asked", 0)}, f)
            try:  # refresh PROGRESS.md so it does not keep saying the blueprint is missing
                import verse_map
                verse_map.write_progress(project, mdir)
                verse_map.log_event(mdir, "BLUEPRINT", "map blueprint written (%d layout, %d devices, %d rules)" % (len(clean.get("layout", [])), len(clean.get("devices", [])), len(clean.get("rules", []))))
            except Exception:
                pass
        except OSError:
            pass
    return {"ok": True, "label": label, "profiles": len(_profiles(slug))}


def sync_profile_from_project(project):
    """The project keeps a copy of its blueprint (Claude/docs/map/profile.json). If the genre skill of this user profile does not have it yet
    (new PC, skills folder reset), put it back, so the knowledge always lives in the genre skill and not only in the project."""
    mdir = os.path.join(project, "Claude", "docs", "map")
    try:
        mark = json.load(open(os.path.join(mdir, "profile-learned.json"), encoding="utf-8-sig"))
        prof = json.load(open(os.path.join(mdir, "profile.json"), encoding="utf-8-sig"))
    except (OSError, ValueError):
        return ""
    if not (isinstance(mark, dict) and isinstance(prof, dict) and mark.get("map_key") and mark.get("genre")):
        return ""
    g = _slug(mark["genre"])
    if _isfile(os.path.join(ldir(g), "profiles", str(mark["map_key"]) + ".json")):
        return ""
    r = save_profile(g, "restored", prof, project=None, map_key=str(mark["map_key"]))
    return "map blueprint restored into the genre skill '%s'" % g if r.get("ok") else ""


def drop_profile(slug, label):
    """Remove the blueprint(s) of a genre with this label (e.g. a duplicate 'Map 1'); remaining ones are renumbered Map 1, 2, ..."""
    slug = _slug(slug)
    d = os.path.join(ldir(slug), "profiles")
    gone = 0
    left = []
    for fn in sorted(_listdir(d)) if _isdir(d) else []:
        if fn.endswith(".json"):
            p = _read_json(os.path.join(d, fn), None)
            if isinstance(p, dict) and p.get("label") == label:
                _remove_file(os.path.join(d, fn)); gone += 1
            elif isinstance(p, dict):
                left.append((p.get("updated", ""), fn, p))
    for i, (_, fn, p) in enumerate(sorted(left), 1):
        p["label"] = "Map %d" % i
        _write_json(os.path.join(d, fn), p)
    render_starter(slug)
    return {"ok": gone > 0, "removed": gone, "left": len(left)} if gone else {"ok": False, "error": "no blueprint with that label"}


def _profiles(slug):
    d = os.path.join(ldir(slug), "profiles")
    out = []
    if _isdir(d):
        for fn in sorted(_listdir(d)):
            if fn.endswith(".json"):
                p = _read_json(os.path.join(d, fn), None)
                if isinstance(p, dict) and p.get("concept"):
                    out.append(p)
    return out


def console_learning(project):
    """Everything the console's 'This map' section shows (state files only). Used by both console servers."""
    import verse_map
    d = verse_map.learning_status(project, os.path.join(project, "Claude", "docs", "map"))
    d["genre_state"] = genre_state(project)
    d["blueprints"] = blueprints_for(d["genre_state"]["genre"]) if d["genre_state"].get("genre") else []
    return d


def blueprints_for(slug):
    """Blueprints of the analysed maps of a genre, for the console (labels only, never map names)."""
    try:
        return [{k: v for k, v in p.items() if k != "map_key"} for p in _profiles(_slug(slug))]
    except Exception:
        return []


def _anatomy_lines(slug):
    """'Map anatomy' section of the starter, aggregated over the owner's analysed maps."""
    profs = _profiles(slug)
    if not profs:
        return []
    out = ["## Map anatomy: what a map of this genre is made of", "",
           "Learned from %d analysed map(s) of the owner. Numbers are what was OBSERVED in each map (labels, not names): a value seen in several maps is a safe default, one seen in a single map is an example to adapt. To build a map of this genre, start here." % len(profs), ""]

    def agg(title, getter):
        rows = {}
        for p in profs:
            for it in getter(p):
                k, text = it
                rows.setdefault(_norm(k), {"name": k, "seen": []})["seen"].append((p["label"], text))
        if rows:
            out.append("### " + title)
            for r in sorted(rows.values(), key=lambda r: -len(r["seen"])):
                out.append("- **%s** (%d of %d map(s)): %s" % (r["name"], len(r["seen"]), len(profs), "; ".join("%s: %s" % (l, t) for l, t in r["seen"] if t) or "present"))
            out.append("")

    out += ["### Concept"] + ["- %s%s: %s" % (p["label"], (" (type: %s)" % p["variant"]) if p.get("variant") else "", p["concept"]) for p in profs] + [""]
    agg("Layout (what is placed in the level)", lambda p: [(x["element"], " ".join(v for v in (str(x.get("count") or ""), x.get("note") or "") if v)) for x in p.get("layout", [])])
    out += ["### Game loop of one match"]
    for p in profs:
        if p.get("loop"):
            out.append("- %s: " % p["label"] + " -> ".join(p["loop"]))
    out.append("")
    agg("Devices to place and what each one does", lambda p: [(x["class"], "; ".join(v for v in ((("x" + str(x["count"])) if x.get("count") else ""), x.get("role"), x.get("settings") and "settings: " + x["settings"], x.get("wiring") and "wiring: " + x["wiring"]) if v)) for x in p.get("devices", [])])
    agg("Verse components to write", lambda p: [(x["component"], "; ".join(v for v in (x.get("role"), x.get("api") and "api: " + x["api"]) if v)) for x in p.get("verse", [])])
    agg("Game logic rules", lambda p: [(x["when"], "then %s%s" % (x["then"], (" [" + x["numbers"] + "]") if x.get("numbers") else "")) for x in p.get("rules", [])])
    agg("Scoring and rewards", lambda p: [(x, "") for x in p.get("scoring", [])])
    out += ["### Build order"]
    for p in profs:
        if p.get("build_order"):
            out += ["- %s:" % p["label"]] + ["  %d. %s" % (i, x) for i, x in enumerate(p["build_order"], 1)]
    out.append("")
    unk = [(p["label"], x) for p in profs for x in p.get("unknown", [])]
    if unk:
        out += ["### Not known yet (not read or not decided)"] + ["- %s: %s" % u for u in unk] + [""]
    return out


def render_starter(slug):
    """Regenerate references/starter.md from the sections + the approved patterns tagged with each section.
    Zero tokens. Called on every render, so it follows the owner's maps: new patterns, tier changes, contested ones."""
    slug = _slug(slug)
    secs = starter_sections(slug)
    if not secs:
        return
    pats = [p for p in load_pack(slug)["patterns"] if p.get("status") != "superseded"]
    order = {"proven": 0, "confirmed": 1, "reference": 2, "hypothesis": 3}

    def lines_for(items):
        items = sorted(items, key=lambda p: (p.get("status") == "contested", order.get(p.get("tier"), 9)))
        return ["- [%s%s] %s: when %s -> %s (%d map(s))" % (
            p.get("tier", "?"), ", contested" if p.get("status") == "contested" else "", p["variant"],
            p["condition"].strip(" ."), p["action"].strip(" ."), p.get("support", 0)) for p in items]

    out = ["# Starter - %s (generated from the owner's approved patterns; do not edit by hand)" % slug, "",
           "Use when the owner starts a NEW project of this genre. Each section lists what the owner's maps taught (proven = rule, confirmed = default, "
           "hypothesis = suggestion, contested = ask) and the open questions. Nothing here comes from general knowledge: an empty section "
           "means nothing was learned yet, so ask the owner and write a DESIGN-<system>.md for it. No code before the owner approves the design.", ""]
    out += _anatomy_lines(slug)
    known = {x["id"] for x in secs}
    for i, sec in enumerate(secs, 1):
        mine = [p for p in pats if p.get("section") == sec["id"]]
        out += ["## %d. %s" % (i, sec["title"]), ""]
        if sec["questions"]:
            out += ["Questions: " + sec["questions"], ""]
        out += lines_for(mine) if mine else ["_Nothing learned yet for this section._"]
        out.append("")
    rest = [p for p in pats if p.get("section") not in known]
    if rest:
        out += ["## Not classified yet", "", "Run `skills_lib.py section %s <pattern id> <section id>` for each (ids: %s)." % (slug, ", ".join(sorted(known))), ""]
        out += lines_for(rest) + [""]
    _write_text(os.path.join(gdir(slug), "references", "starter.md"), "\n".join(out))


def similar(slug, threshold=0.5):
    """Zero-token duplicate finder: pairs of active patterns whose condition+action share most of their words (Jaccard)."""
    slug = resolve_genre(slug)
    stop = set("a an the of to in on and or for with when is are be it its that this by as at from so no not per each every".split())

    def toks(p):
        return set(w for w in re.findall(r"[a-z0-9]+", (p["condition"] + " " + p["action"]).lower()) if w not in stop and len(w) > 2)

    pats = [p for p in load_pack(slug)["patterns"] if p.get("status") != "superseded"]
    ts = [toks(p) for p in pats]
    out = []
    for i in range(len(pats)):
        for j in range(i + 1, len(pats)):
            u = ts[i] | ts[j]
            sc = len(ts[i] & ts[j]) / len(u) if u else 0
            if sc >= threshold:
                out.append({"score": round(sc, 2), "a": pats[i]["id"], "b": pats[j]["id"], "a_text": pats[i]["condition"][:90], "b_text": pats[j]["condition"][:90],
                            "same_section": pats[i].get("section") == pats[j].get("section")})
    return sorted(out, key=lambda x: -x["score"])


def set_section(slug, pid, section):
    slug = resolve_genre(slug)
    ids = {x["id"] for x in starter_sections(slug)}
    if section not in ids:
        return {"ok": False, "error": "unknown section (ids: %s)" % ", ".join(sorted(ids))}
    pack = load_pack(slug)
    p = _find(pack, pid)
    if p is None:
        return {"ok": False, "error": "pattern not found"}
    p["section"] = section
    save_pack(slug, pack)
    render_skill(slug)
    return {"ok": True, "pattern": pid, "section": section}


# ----------------------------------------------------------------------------- proposals
def _inbox_dir(slug):
    return os.path.join(ldir(slug), "inbox")


def _save_proposal(slug, prop):
    _write_json(os.path.join(_inbox_dir(slug), prop["id"] + ".json"), prop)


def _say_new(slug, variant, statement):
    return "In %s / %s: %s" % (slug, variant, statement)


# ----------------------------------------------------------------------------- genre confirmation
def _gproposal_path(project):
    return os.path.join(project, "Claude", "docs", "map", "genre-proposal.json")


def _pread(project):
    path = _gproposal_path(project)
    return _read_json(path, None, base=project) if _isfile(path, base=project) else None


def _log(project, kind, text):
    try:
        import verse_map
        verse_map.log_event(os.path.join(project, "Claude", "docs", "map"), kind, text)
    except Exception:
        pass


def _pwrite(project, obj):
    _write_json(_gproposal_path(project), obj, base=project)


def _project_from_cwd():
    d = os.path.abspath(os.getcwd())
    for _ in range(6):
        if os.path.isdir(os.path.join(d, "Claude", "docs")):
            return d
        d = os.path.dirname(d)
    return ""


def genre_gate(project=None):
    """Error dict while the owner has not confirmed the genre the kit proposed for this project; None otherwise (also for projects without a proposal)."""
    project = project or _project_from_cwd()
    if not project:
        return None
    pr = _pread(project)
    if isinstance(pr, dict) and pr.get("status") == "pending":
        return {"ok": False, "error": "GENRE NOT CONFIRMED: the owner has not confirmed '%s' (type '%s') on the console yet. Nothing is written to the genre skills until then. Keep reading the project locally and try again at the next session." % (pr.get("genre"), pr.get("variant"))}
    return None


def _known_variants(slug=None):
    out = {}
    for s in _genres():
        v = set()
        for p in _profiles(s):
            if p.get("variant"):
                v.add(p["variant"])
        try:
            for p in load_pack(s)["patterns"]:
                if p.get("variant") and p["variant"] != "*" and p.get("status") != "superseded":
                    v.add(p["variant"])
        except Exception:
            pass
        out[s] = sorted(v)
    return out


def _official_genres():
    path = os.path.join(genre_root(), "fortnite-genres-official.json")
    d = _read_json(path, {}) if _isfile(path) else {}
    return [{"slug": g.get("slug"), "name": g.get("name") or g.get("slug")} for g in d.get("genres", []) if g.get("slug")]


def _official_slug(value):
    """A genre slug taken from the OFFICIAL list itself, never from the caller's string (same idea as resolve_genre):
    request data can then not steer a file path. None when the value is not on the list."""
    if isinstance(value, str):
        for g in _official_genres():
            if g["slug"] == value:
                return _slug(g["slug"])
    return None


def propose_genre(project, slug, variant, why=""):
    """The kit's own deduction of genre + map type. Written to the project only (genre-proposal.json and .genre); the genre skill is not touched until the owner confirms."""
    slug = _official_slug(slug)
    if slug is None:
        return {"ok": False, "error": "genre must be one slug of the official list (fortnite-genres-official.json)"}
    variant = _canon_variant(slug, variant)
    if not variant:
        return {"ok": False, "error": "a map type (variant) is required, e.g. pillars, red-vs-blue"}
    _write_text(os.path.join(project, "Claude", "docs", ".genre"), slug + "\n", base=project)
    _pwrite(project, {"genre": slug, "variant": variant, "why": _pstr(why, 600), "status": "pending", "at": _today()})
    _log(project, "GENRE", "%s / %s proposed (waiting for the owner)" % (slug, variant))
    return {"ok": True, "status": "pending"}


def _variant_name(v):
    v = re.sub(r"[^a-z0-9]+", "-", (v or "").strip().lower()).strip("-")[:40]
    return v


def _variant_stem(name):
    """Spelling-independent key of a map type: 'pillar', 'pillars' and 'Pillars' are the same type."""
    s = (name or "").replace("-", "")
    if len(s) > 3:
        if s.endswith("ies"):
            s = s[:-3] + "y"
        elif s.endswith(("ses", "xes", "zes", "ches", "shes")):
            s = s[:-2]
        elif s.endswith("s") and not s.endswith("ss"):
            s = s[:-1]
    return s


def _variant_counts(slug, prefer=""):
    cnt = {}

    def add(v, w=1):
        if v and v != "*":
            cnt[v] = cnt.get(v, 0) + w
    try:
        for p in load_pack(slug)["patterns"]:
            if p.get("status") != "superseded":
                add(p.get("variant"))
    except Exception:
        pass
    for p in _profiles(slug):
        add(p.get("variant"), 2)   # the blueprint carries the type the owner confirmed
    for p in list_proposals(slug):
        add(p.get("variant"))
    if prefer:
        add(prefer, 100)           # the type confirmed for the project in hand wins
    return cnt


def _canon_variant(slug, v, prefer=""):
    """A map type spelled like one that already exists in the genre (same stem) takes the existing spelling, so
    'pillar' next to 'pillars' never becomes a second type. A new type keeps its own clean name."""
    name = _variant_name(v)
    if not name:
        return name
    cnt = _variant_counts(slug, prefer)
    key = _variant_stem(name)
    same = [x for x in cnt if _variant_stem(x) == key]
    if not same:
        return name
    return sorted(same, key=lambda x: (-cnt[x], x != name, x))[0]


def merge_variants(slug=None, project=None):
    """Heal map types written two ways (pillar / pillars): the patterns, their support, the waiting lessons, the blueprints, the
    evidence notes and the project's own proposal move to one spelling (the most used one, or the type confirmed for `project`).
    Idempotent; changes nothing when every type is already unique."""
    slugs = [resolve_genre(slug)] if slug else _genres()
    done = []
    for s in slugs:
        prefer = ""
        if project:
            pr = _pread(project) or {}
            if pr.get("genre") == s and pr.get("status") == "confirmed":
                prefer = _variant_name(pr.get("variant"))
        cnt = _variant_counts(s, prefer)
        groups = {}
        for v in cnt:
            groups.setdefault(_variant_stem(v), []).append(v)
        remap = {}
        for g in groups.values():
            if len(g) > 1:
                canon = sorted(g, key=lambda x: (-cnt[x], x))[0]
                remap.update({v: canon for v in g if v != canon})
        if not remap:
            continue
        pack, sup, ov = load_pack(s), _support(s), _overlay(s)
        idmap, kept, byid = {}, [], {}
        for p in pack["patterns"]:
            if p.get("variant") in remap:
                old = p["id"]
                p["variant"] = remap[p["variant"]]
                p["id"] = pattern_id(p["variant"], p.get("condition"), p.get("action"))
                idmap[old] = p["id"]
            if p["id"] in byid:    # the same lesson was stored under both spellings: one pattern, evidence of both
                continue
            byid[p["id"]] = p
            kept.append(p)
        for old, new in idmap.items():
            if old == new:
                continue
            a = sup.pop(old, None)
            if a:
                b = sup.setdefault(new, {"for": [], "against": []})
                for k in ("for", "against"):
                    b[k] = sorted(set(b.get(k, [])) | set(a.get(k, [])))
                if a.get("metric_backed"):
                    b["metric_backed"] = True
        pack["patterns"] = kept
        for p in kept:
            if p["id"] in idmap.values():
                recompute(p, sup)
        ov["rejected"] = sorted({idmap.get(x, x) for x in ov.get("rejected", [])})
        ov["rejected_support"] = sorted({"%s:%s" % (idmap.get(x.split(":")[0], x.split(":")[0]), x.split(":", 1)[1]) if ":" in x else x
                                         for x in ov.get("rejected_support", [])})
        for prop in list_proposals(s):
            if prop.get("variant") not in remap:
                continue
            old_path = os.path.join(_inbox_dir(s), prop["id"] + ".json")
            prop["variant"] = remap[prop["variant"]]
            pat = prop.get("pattern") or {}
            if pat:
                pat["variant"] = prop["variant"]
                pat["id"] = pattern_id(pat["variant"], pat.get("condition"), pat.get("action"))
                prop["pattern_id"] = pat["id"]
            prop["id"] = "pr-" + hashlib.sha1(("%s|%s|%s" % (prop.get("kind"), prop.get("pattern_id"), prop.get("map_key"))).encode()).hexdigest()[:10]
            if not _isfile(os.path.join(_inbox_dir(s), prop["id"] + ".json")):
                _save_proposal(s, prop)
            if os.path.join(_inbox_dir(s), prop["id"] + ".json") != old_path and _isfile(old_path):
                _remove_proposal_file(s, old_path)
        pdir = os.path.join(ldir(s), "profiles")
        for fn in (sorted(_listdir(pdir)) if _isdir(pdir) else []):
            if fn.endswith(".json"):
                pf = _read_json(os.path.join(pdir, fn), None)
                if isinstance(pf, dict) and pf.get("variant") in remap:
                    pf["variant"] = remap[pf["variant"]]
                    _write_json(os.path.join(pdir, fn), pf)
        edir = os.path.join(ldir(s), "evidence")
        for v, canon in remap.items():
            src, dst = os.path.join(edir, v + ".md"), os.path.join(edir, canon + ".md")
            if _isfile(src):
                try:
                    with open(_inside(edir, src), encoding="utf-8") as f:
                        _append_text(dst, "\n" + f.read())
                    _remove_file(_inside(edir, src), base=edir)
                except (OSError, ValueError):
                    pass
        _save_support(s, sup)
        _write_json(os.path.join(ldir(s), "overlay.json"), ov)
        save_pack(s, pack)
        _ledger(s, "merge-variants", "-", ", ".join("%s -> %s" % (a, b) for a, b in sorted(remap.items())))
        if project:
            pr = _pread(project) or {}
            if pr.get("genre") == s and pr.get("variant") in remap:
                pr["variant"] = remap[pr["variant"]]
                _pwrite(project, pr)
        render_skill(s)
        done.append({"genre": s, "merged": remap})
    return {"ok": True, "merged": done}


def _marker_bump(project, key):
    """Count a lesson queued from this project (profile-learned.json), so the kit knows the map already produced lessons."""
    if not project:
        return
    try:
        mpath = os.path.join(project, "Claude", "docs", "map", "profile-learned.json")
        m = json.load(open(mpath, encoding="utf-8-sig"))
        if isinstance(m, dict):
            m[key] = int(m.get(key, 0)) + 1
            json.dump(m, open(mpath, "w", encoding="utf-8"))
    except (OSError, ValueError):
        pass


def _held_path(project):
    return os.path.join(project, "Claude", "docs", "map", "lessons-held.json")


def _hold_lesson(project, args):
    try:
        path = _held_path(project)
        items = _read_json(path, [], base=project) if _isfile(path, base=project) else []
        if not isinstance(items, list):
            items = []
        key = (args["variant"], args["condition"], args["action"])
        if not any((i.get("variant"), i.get("condition"), i.get("action")) == key for i in items):
            items.append(args)
        _write_json(path, items[-50:], base=project)
    except Exception:
        pass


def _flush_held(project, slug):
    """After the owner confirmed genre and type: save the blueprint written while waiting and queue the lessons held back."""
    out = {"blueprint": False, "lessons": 0}
    mdir = os.path.join(project, "Claude", "docs", "map")
    pj = os.path.join(mdir, "profile.json")
    if os.path.isfile(pj):
        try:
            prof = json.load(open(pj, encoding="utf-8-sig"))
            mark = {}
            try:
                mark = json.load(open(os.path.join(mdir, "profile-learned.json"), encoding="utf-8-sig"))
            except (OSError, ValueError):
                pass
            if isinstance(prof, dict) and (mark.get("v", 0) < 1 or _slug(mark.get("genre") or slug) != slug or not mark.get("map_key")):
                r = save_profile(slug, os.path.basename(os.path.abspath(project)) or "map", prof, project=project)
                out["blueprint"] = bool(r.get("ok"))
        except (OSError, ValueError):
            pass
    hp = _held_path(project)
    if _isfile(hp, base=project):
        try:
            items = _read_json(hp, [], base=project) or []
            keep = []
            for i in items:
                r = propose(slug, i["variant"], i["condition"], i["action"], i["statement"], i["map_name"], i.get("stance", "for"),
                            i.get("tasks", ()), i.get("note", ""), i.get("metric_backed", False), i.get("section", ""))
                if r.get("ok"):
                    out["lessons"] += 1
                else:
                    keep.append(i)
            _write_json(hp, keep, base=project)
        except Exception:
            pass
    return out


def confirm_genre(project, slug, variant):
    """Owner decision from the console: genre and map type are right (or corrected). Only now the genre skill is created / retargeted."""
    slug = _official_slug(slug)
    if slug is None:
        return {"ok": False, "error": "genre must be one of the official genres"}
    variant = _canon_variant(slug, variant)
    if not variant:
        return {"ok": False, "error": "a map type is required"}
    gfile = os.path.join(project, "Claude", "docs", ".genre")
    old = open(gfile, encoding="utf-8").read().strip().lower() if os.path.isfile(gfile) else ""
    if old and old != slug and old != "epic-template" and _isdir(gdir(old)):
        try:
            retarget(old, slug)
        except Exception:
            pass
    _write_text(gfile, slug + "\n", base=project)
    init_genre(slug)
    pr = _pread(project) or {}
    pr.update({"genre": slug, "variant": variant, "status": "confirmed", "confirmed_at": _today()})
    _pwrite(project, pr)
    _log(project, "GENRE", "%s / %s confirmed by the owner" % (slug, variant))
    saved = _flush_held(project, slug)
    return {"ok": True, "genre": slug, "variant": variant, "saved": saved}


def genre_state(project):
    """What the console shows for this project's genre: proposal (pending/confirmed), lists to choose from."""
    gfile = os.path.join(project, "Claude", "docs", ".genre")
    genre = open(gfile, encoding="utf-8").read().strip().lower() if os.path.isfile(gfile) else ""
    pr = _pread(project)
    variant = (pr or {}).get("variant") or ""
    if not variant and genre and genre != "epic-template":
        for p in _profiles(genre):
            if p.get("variant"):
                variant = p["variant"]
    return {"genre": genre, "variant": variant, "status": (pr or {}).get("status") or ("confirmed" if genre else "none"),
            "why": (pr or {}).get("why", ""), "genres": _official_genres(), "known_variants": _known_variants()}


def propose(slug, variant, condition, action, statement, map_name, stance="for", tasks=(), note="", metric_backed=False, section=""):
    """Queue a lesson learned from a real map. Nothing is applied until the owner approves it."""
    slug = _slug(slug)
    gate = genre_gate()
    if gate:
        proj = _project_from_cwd()
        if proj:  # the lesson is kept in the project and queued by itself when the owner confirms the genre
            _hold_lesson(proj, {"slug": slug, "variant": variant, "condition": condition, "action": action, "statement": statement,
                                "map_name": map_name, "stance": stance, "tasks": list(tasks), "note": note,
                                "metric_backed": metric_backed, "section": section})
            gate = dict(gate, held=True)
        return gate
    init_genre(slug)
    if stance not in ("for", "against"):
        return {"ok": False, "error": "stance must be 'for' or 'against'"}
    if not (map_name or "").strip():
        return {"ok": False, "error": "map_name is required (it stays on this computer)"}
    if not VARIANT_RE.fullmatch(variant or ""):
        return {"ok": False, "error": "variant must be a lowercase slug or '*'"}
    if variant != "*":
        variant = _canon_variant(slug, variant) or variant   # 'pillar' next to an existing 'pillars' is the same type
    pid = pattern_id(variant, condition, action)
    deny = _deny_terms(slug) + [map_name.strip()]
    cand = {"id": pid, "variant": variant, "statement": statement.strip(), "condition": condition.strip(),
            "action": action.strip(), "tier": "hypothesis", "status": "active", "origin": "local"}
    if section:
        cand["section"] = section.strip()
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
            "project": _proj_hash(_project_from_cwd()), "created": _now()}
    if _isfile(os.path.join(_inbox_dir(slug), prop["id"] + ".json")):
        return {"ok": True, "skipped": "already waiting for your approval", "proposal": prop["id"]}
    _save_proposal(slug, prop)
    _marker_bump(_project_from_cwd(), "lessons")
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
        mk = _remember_map(slug, prop["map_name"], prop.get("project", ""))
        _apply_support(slug, pack, sup, pid, mk, "for", prop.get("metric_backed", False))
        _evidence_note(slug, pat["variant"], prop["map_name"],
                       "New pattern approved: %s\n%s" % (pat["statement"], prop.get("note", "")))
    elif kind in ("support_added", "contradiction"):
        mk = _remember_map(slug, prop["map_name"], prop.get("project", ""))
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
def export_pack(slug, out_dir, skip=()):
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
        if p.get("status") == "superseded" or p.get("support", 0) < 1 or p.get("id") in skip:
            continue
        item = {k: p[k] for k in ("id", "variant", "statement", "condition", "action", "tier", "status", "section") if k in p}
        item["support"] = p.get("support", 0)
        items.append(item)
    out = {"schema": SCHEMA, "genre": slug, "pack_version": int(pack.get("revision", 0)),
           "exported_at": _now(), "patterns": items}
    path = os.path.join(out_root, slug, "patterns.json")
    _write_json(path, out, base=out_root)
    return {"ok": True, "path": path, "patterns": len(items)}


# ----------------------------------------------------------------------------- a map is shareable only when it is published
ISLAND_API = "https://api.fortnite.com/ecosystem/v1/islands/"
PUBLISHED_TTL_YES, PUBLISHED_TTL_NO = 24 * 3600, 3600


def _fetch_island_public(code):
    """True when Epic has public data for this island code (the map is published), False when it has none (401/403/404), None when unknown."""
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(ISLAND_API + urllib.parse.quote(code, safe="-"), headers={"Accept": "application/json", "User-Agent": "UEFN-Claude-Kit/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status == 200
    except urllib.error.HTTPError as e:
        return False if e.code in (401, 403, 404) else None
    except Exception:
        return None


def island_published(project, fetch=None, force=False, now=None):
    """{"published": True|False|None, "reason": ...} for the island code saved in the project (Claude/docs/.island-code).
    The code itself is never stored or printed: only a short hash and the answer, cached in Claude/logs/island-published.json."""
    now = time.time() if now is None else now
    try:
        with open(os.path.join(project, "Claude", "docs", ".island-code"), encoding="utf-8") as f:
            code = f.read().strip()
    except OSError:
        code = ""
    if not re.fullmatch(r"\d{4}-\d{4}-\d{4}", code):
        return {"published": False, "reason": "no island code saved for this project"}
    ch = hashlib.sha1(code.encode()).hexdigest()[:8]
    cache = os.path.join(project, "Claude", "logs", "island-published.json")
    try:
        with open(cache, encoding="utf-8") as f:
            c = json.load(f)
    except (OSError, ValueError):
        c = {}
    if not force and c.get("code") == ch and c.get("published") in (True, False) and now - float(c.get("at", 0)) < (PUBLISHED_TTL_YES if c["published"] else PUBLISHED_TTL_NO):
        return {"published": c["published"], "reason": "checked earlier"}
    ans = (fetch or _fetch_island_public)(code)
    if ans is None:
        return {"published": c.get("published") if c.get("code") == ch else None, "reason": "could not reach Epic to check"}
    try:
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        with open(cache, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"code": ch, "published": bool(ans), "at": now}, f)
    except OSError:
        pass
    return {"published": bool(ans), "reason": "Epic has public data for this island" if ans else "Epic has no public data for this island (not published yet)"}


def sync_published(project, fetch=None, force=False, now=None):
    """Mark the maps of this project (in every genre skill) as published or not, from island_published. Unknown answers change nothing."""
    st = island_published(project, fetch, force, now)
    if st["published"] is None:
        return dict(st, marked=0)
    ph, pl, marked = _proj_hash(project), "", 0
    try:
        with open(os.path.join(project, "Claude", "docs", "map", "profile-learned.json"), encoding="utf-8-sig") as f:
            pl = str((json.load(f) or {}).get("map_key") or "")
    except (OSError, ValueError, AttributeError):
        pass
    for g in _genres():
        m, changed = _maps(g), False
        for k, v in m.items():
            if isinstance(v, dict) and ((ph and v.get("project") == ph) or (pl and k == pl)) and v.get("published") is not st["published"]:
                v["published"] = st["published"]
                changed = True
                marked += 1
        if changed:
            _write_json(os.path.join(ldir(g), "maps.json"), m)
    return dict(st, marked=marked)


def lesson_published(slug, pattern_id):
    """True when at least one map that supports this lesson is published. Lessons of unpublished maps stay on this computer."""
    maps = _maps(slug)
    keys = (_support(slug).get(pattern_id) or {}).get("for", [])
    return any(isinstance(maps.get(k), dict) and maps[k].get("published") is True for k in keys)


# ----------------------------------------------------------------------------- share lessons with the community (opt-in)
COMMUNITY_REPO = "mimmo-the-root/UEFN-dream-bot-team"
MAX_CONTRIB_URL = 3000
CONTRIB_SECTIONS = ("run-loop", "architecture", "devices", "progression", "death-strategies", "persistence", "performance", "launch-checklist")


def _community_file():
    return os.path.join(skills_root(), "community-share.json")


def community_state():
    """The switch "Contribute to the community" (ON by default; you can switch it off) and which lessons were already shared. Lives next to the skills."""
    d = _read_json(_community_file(), {})
    shared = [x for x in (d.get("shared") or []) if isinstance(x, str) and re.fullmatch(r"[pr]-[0-9a-f]{12}", x)]
    h = d.get("handle") if isinstance(d.get("handle"), str) and re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", d.get("handle")) else ""
    return {"share": d.get("share") is not False, "shared": shared[-2000:], "handle": h}


def set_handle(handle):
    """Your GitHub name, asked once: it goes into the file name of a proposal (the community check wants it there), so you do not have to rename the file."""
    h = (handle or "").strip().lstrip("@")
    if h and not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", h):
        return {"ok": False, "error": "that is not a GitHub name (letters, digits and dashes)"}
    st = community_state()
    st["handle"] = h
    _write_json(_community_file(), st)
    return {"ok": True, "handle": h}


_GH_BODY = "Sent from the UEFN Dream Bot Team console. The file holds only the JSON shown there before sending: no paths, no map names."


def _gh_url(name, value, title):
    """GitHub 'new file' page with the file name, the content, the commit title and the description already filled in.
    Returns (url, prefilled, name). Too long to carry the content: the url keeps the name and the title, the user pastes the JSON."""
    h = community_state().get("handle")
    if h:
        name = name.replace("<your-github-handle>", h.lower())
    base = "https://github.com/%s/new/main?filename=%s" % (COMMUNITY_REPO, urllib.parse.quote(name, safe="/"))
    tail = "&message=%s&description=%s" % (urllib.parse.quote(title, safe=""), urllib.parse.quote(_GH_BODY, safe=""))
    full = base + "&value=" + urllib.parse.quote(value, safe="") + tail
    if len(full) <= MAX_CONTRIB_URL:
        return full, True, name
    return base + tail, False, name


def _gh_note(prefilled):
    h = community_state().get("handle")
    ren = "" if h else " Rename the file to your GitHub name (set it once in the Community tab and this step disappears)."
    return ("On GitHub press Propose new file, then Create pull request." if prefilled else "Too long to prefill: press Copy, paste the JSON in the GitHub editor, then press Propose new file.") + ren


def set_community(share):
    st = community_state()
    st["share"] = bool(share)
    _write_json(_community_file(), st)
    return {"ok": True, "share": st["share"]}


def _kit_version():
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "KIT-VERSION"), encoding="utf-8") as f:
            v = f.read().strip()
        return v if re.fullmatch(r"\d{1,3}\.\d{1,3}\.\d{1,3}", v) else "0.0.0"
    except OSError:
        return "0.0.0"


def community_info(project):
    """State for the Skills / What's new pages: the switch, what was shared, and whether the map of this project is published."""
    st = community_state()
    try:
        pub = sync_published(project)
    except Exception:
        pub = {"published": None, "reason": "could not check"}
    st["published"] = pub.get("published")
    st["published_reason"] = pub.get("reason", "")
    return st


def community_act(data, project=None):
    """One entry point for the console servers (POST /community-act): {action: on|off|export|shared, genre, id}. Genre and id are looked up, never used as paths."""
    act_ = (data or {}).get("action")
    if act_ in ("on", "off"):
        return set_community(act_ == "on")
    if act_ == "handle":
        return set_handle(data.get("handle"))
    if act_ == "mode":
        return set_maintainer_mode(data.get("mode"))
    if act_ == "export":
        return contribution_export(data.get("genre"), data.get("id"))
    if act_ == "shared":
        return mark_shared(data.get("genre"), data.get("id"))
    if act_ == "export-recipes":
        return recipes_export(project)
    if act_ == "recipe-shared":
        return mark_recipe_shared(data.get("genre"), data.get("name"))
    if act_ == "export-recipe":
        return recipe_export(data.get("genre"), data.get("name"))
    if act_ == "section":
        if data.get("section") not in CONTRIB_SECTIONS:
            return {"ok": False, "error": "section must be one of: %s" % ", ".join(CONTRIB_SECTIONS)}
        return set_section(resolve_genre(data.get("genre")), data.get("id"), data.get("section"))
    return {"ok": False, "error": "unknown action"}


def recipes_export(project):
    """What would leave this computer for the UEFN MCP recipes you proved by real work: one count per recipe (worked, failed, a short
    error with no paths), never arguments, paths or names. Refused while the switch is off."""
    if not community_state()["share"]:
        return {"ok": False, "error": "sharing with the community is switched off"}
    try:
        import recipes_status as RS
        ledger = os.path.join(project or os.getcwd(), "Claude", "logs", "explore-ledger.jsonl")
        ex = RS.export(RS.merge(RS.load_recipes(), RS.evidence_from_ledger(ledger)))
    except Exception as e:
        return {"ok": False, "error": "could not read the recipes evidence (%s)" % e.__class__.__name__}
    rec = {}
    for k, v in ex["recipes"].items():
        why = redact(str(v.get("last_failure") or ""))[:80]
        if "/" in why or "\\" in why or ":" in why:
            why = ""
        rec[k] = {"ok": int(v["ok"]), "failed": int(v["failed"]), "last_failure": why}
    if not any(v["ok"] for v in rec.values()):
        return {"ok": False, "error": "nothing proven yet: work through the lab module (calls that worked count) and come back"}
    doc = {"schema_version": 1, "kind": "mcp-recipes-evidence", "kit_version": _kit_version(), "recipes": rec}
    name = "contributions/mcp-recipes/<your-github-handle>.json"
    value = json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=1)
    url, pre, name = _gh_url(name, value, "Community: which UEFN MCP tools worked")
    return {"ok": True, "doc": doc, "json": value, "filename": name, "url": url, "note": _gh_note(pre), "recipes_kind": True}


_SECTION_WORDS = (
    ("death-strategies", ("death", "die", "dies", "elimination", "respawn", "knocked", "revive")),
    ("persistence", ("save", "saved", "persist", "persistent", "stored", "load ", "leaves", "returning")),
    ("performance", ("performance", "lag", "oscillat", "budget", "too many", "spawn limit", "cost", "frame")),
    ("progression", ("tier", "level", "score", "xp", "unlock", "reward", "upgrade", "progress", "counter")),
    ("devices", ("device", "spawner", "trigger", "button", "volume", "barrier", "vending")),
    ("launch-checklist", ("publish", "launch", "release", "checklist", "submission")),
    ("run-loop", ("round", "match", "timer", "loop", "wave", "restart", "reset")),
)


def guess_section(p):
    """The section of a lesson, chosen by the kit from its words, so nobody has to choose one (architecture when nothing fits)."""
    if p.get("section") in CONTRIB_SECTIONS:
        return p["section"]
    t = " ".join(str(p.get(k) or "") for k in ("statement", "condition", "action")).lower()
    for sec, words in _SECTION_WORDS:
        if any(w in t for w in words):
            return sec
    return "architecture"


def contribution_export(slug, pattern_id):
    """The exact JSON that would leave this computer for ONE approved lesson of the owner, plus the GitHub page that proposes it.
    Refused while the switch is off, for a lesson that is not the owner's own and approved, or one that fails the privacy check."""
    if not community_state()["share"]:
        return {"ok": False, "error": "sharing with the community is switched off"}
    slug = resolve_genre(slug)
    if not isinstance(pattern_id, str) or not re.fullmatch(r"p-[0-9a-f]{12}", pattern_id):
        return {"ok": False, "error": "unknown lesson"}
    p = _find(load_pack(slug), pattern_id)
    if not p or p.get("origin") != "local" or p.get("status") == "superseded" or int(p.get("support", 0)) < 1:
        return {"ok": False, "error": "only a lesson of yours that you approved can be shared"}
    if pattern_id in load_hold()["lessons"]:
        return {"ok": False, "error": "you kept this lesson private"}
    if not lesson_published(slug, pattern_id):
        return {"ok": False, "published": False, "error": "this lesson comes from a map that is not published: it stays on this computer until the map is published"}
    if validate_pattern(p, _deny_terms(slug)):
        return {"ok": False, "error": "the lesson does not pass the privacy check"}
    sec = guess_section(p)
    doc = {"schema_version": 1, "pattern_id": p["id"], "genre": slug, "variant": p["variant"], "section": sec,
           "direction": "for" if int(p.get("support", 0)) >= int(p.get("against", 0)) else "against",
           "statement": p["statement"], "condition": p["condition"], "action": p["action"], "kit_version": _kit_version()}
    name = "contributions/%s/%s/<your-github-handle>.json" % (slug, p["id"])
    value = json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=1)
    url, pre, name = _gh_url(name, value, "Community lesson: %s (%s)" % (p["id"], slug))
    return {"ok": True, "doc": doc, "json": value, "filename": name, "url": url, "note": _gh_note(pre)}


def mark_shared(slug, pattern_id):
    slug = resolve_genre(slug)
    if not re.fullmatch(r"p-[0-9a-f]{12}", str(pattern_id)) or not _find(load_pack(slug), pattern_id):
        return {"ok": False, "error": "unknown lesson"}
    st = community_state()
    if pattern_id not in st["shared"]:
        st["shared"].append(pattern_id)
        _write_json(_community_file(), st)
    return {"ok": True, "shared": len(st["shared"])}


def mark_recipe_shared(slug, name):
    """The owner sent this recipe to GitHub: it leaves the "to send" list."""
    rid = recipe_id(name)
    slug = resolve_genre(slug)
    data = _read_json(os.path.join(ldir(slug), "recipes.json"), {"recipes": []})
    if not any(_norm(x.get("name", "")) == _norm(name or "") for x in data["recipes"]):
        return {"ok": False, "error": "unknown recipe"}
    st = community_state()
    if rid not in st["shared"]:
        st["shared"].append(rid)
        _write_json(_community_file(), st)
    return {"ok": True}


def _norm_key(variant, condition):
    return _norm(variant) + "|" + _norm(condition)


def merge_pack(slug, pack_obj, source, official=False):
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
        if clean["tier"] == "reference" and not official:
            clean["tier"] = "hypothesis"   # only an explicitly official pack may carry the reference tier
        if official:
            clean["tier"] = "reference"
        clean["status"] = clean["status"] if clean["status"] in STATUSES else "active"
        fnd = validate_pattern(clean, deny)
        for _f in ("statement", "condition", "action"):   # an incoming (community) pack is plain English: no newline, look-alike, combining, zero-width or bidi characters
            if isinstance(clean.get(_f), str) and not INCOMING_TEXT.match(clean[_f]):
                fnd.append((_f, "unusual_characters"))
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
            "kind": "pack_update", "genre": slug, "source": source, "version": version, "official": bool(official),
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
    off = bool(prop.get("official"))
    for it in prop["new"]:
        if it["id"] in exclude or _find(pack, it["id"]):
            continue
        pack["patterns"].append({"id": it["id"], "variant": it["variant"], "statement": it["statement"],
                                 "condition": it["condition"], "action": it["action"],
                                 "tier": "reference" if off else "hypothesis",
                                 "status": "active", "origin": "official" if off else "community", "support": 0, "against": 0,
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


def apply_revoked(ids):
    """Remove community lessons the maintainer revoked (community-revoked.json): from the pack (only origin "community", never your own lessons),
    from waiting proposals and from waiting community packs. Returns {"removed": n}. Idempotent."""
    ids = {i for i in (ids or []) if isinstance(i, str) and re.fullmatch(r"p-[0-9a-f]{12}", i)}
    if not ids:
        return {"removed": 0}
    removed = 0
    for g in _genres():
        changed = False
        pack = load_pack(g)
        keep = [p for p in pack["patterns"] if not (p.get("id") in ids and p.get("origin") == "community" and int(p.get("support", 0)) < 1)]   # backed by your own map: stays
        if len(keep) != len(pack["patterns"]):
            gone = [p["id"] for p in pack["patterns"] if p not in keep]
            pack["patterns"] = keep
            save_pack(g, pack)
            for pid in gone:
                _ledger(g, "community_revoked", pid, "revoked by the maintainer")
            removed += len(gone)
            changed = True
        d = _inbox_dir(g)
        for fn in (sorted(_listdir(d)) if _isdir(d) else []):
            if not fn.endswith(".json"):
                continue
            prop = _read_json(os.path.join(d, fn), None)
            if not isinstance(prop, dict):
                continue
            if prop.get("kind") == "pack_update":
                n0 = sum(len(prop.get(k, [])) for k in ("new", "known", "conflicts"))
                for k in ("new", "known", "conflicts"):
                    prop[k] = [x for x in prop.get(k, []) if x.get("id") not in ids]
                if sum(len(prop.get(k, [])) for k in ("new", "known", "conflicts")) != n0:
                    removed += n0 - sum(len(prop.get(k, [])) for k in ("new", "known", "conflicts"))
                    _save_proposal(g, prop)
        if changed:
            try:
                render_skill(g)
            except Exception:
                pass
    return {"removed": removed}


def import_community_dir(genre_dir_root=None, revoked_ids=()):
    """Offer the community packs shipped with the kit (<genre>/community/*.json) as ONE proposal per genre; nothing changes until you approve.
    The pack passes the same validation as any incoming pack (merge_pack); idempotent."""
    root = genre_dir_root or genre_root()
    out = {"queued": 0, "rejected": 0}
    for g in (sorted(os.listdir(root)) if os.path.isdir(root) else []):
        cd = os.path.join(root, g, "community")
        for n in (sorted(os.listdir(cd)) if os.path.isdir(cd) else []):
            if not (n.endswith(".json") and os.path.isfile(os.path.join(cd, n))):
                continue
            try:
                with open(os.path.join(cd, n), encoding="utf-8") as f:
                    obj = json.load(f)
                if isinstance(obj, dict) and isinstance(obj.get("patterns"), list):
                    obj["patterns"] = [x for x in obj["patterns"] if not (isinstance(x, dict) and x.get("id") in set(revoked_ids))]   # a revoked lesson is never offered again
                r = merge_pack(_slug(g), obj, "community")
            except Exception as e:
                r = {"ok": False, "error": str(e)}
            if r.get("ok") and r.get("proposal"):
                out["queued"] += 1
            elif not r.get("ok"):
                out["rejected"] += 1
    return out


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
def detect_techniques(project_dir):
    """Which technique skills apply to this project? Looks for each technique skill's `markers:` words
    (frontmatter of its SKILL.md) inside the project's Verse files. Read-only, returns slugs + hits."""
    root = genre_root()
    techs, fmarks = {}, {}
    for g in (os.listdir(root) if os.path.isdir(root) else []):
        sk = os.path.join(root, g, "SKILL.md")
        if not os.path.isfile(sk):
            continue
        with open(sk, encoding="utf-8", errors="replace") as f:
            head = f.read(2000)
        m = re.search(r"^markers:\s*(.+)$", head, re.M)
        istech = re.search(r"^kind:\s*technique", head, re.M)
        if m and istech:
            words = [w.strip() for w in m.group(1).split(",") if w.strip()]
            if words:
                techs[g] = words
        fm = re.search(r"^file_markers:\s*(.+)$", head, re.M)
        if fm and istech:
            fmarks[g] = [w.strip() for w in fm.group(1).split(",") if w.strip()]
    for g in fmarks:
        techs.setdefault(g, [])
    hits = {g: [] for g in techs}
    scanned = 0
    for base, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in (".git", "Claude", "node_modules", "__pycache__")]
        for n in files:
            if not n.endswith(".verse") or scanned > 3000:
                continue
            scanned += 1
            try:
                with open(os.path.join(base, n), encoding="utf-8", errors="replace") as f:
                    txt = f.read(400000)
            except OSError:
                continue
            for g, words in techs.items():
                for w in words:
                    if w in txt and w not in hits[g]:
                        hits[g].append(w)
    for g, marks in fmarks.items():  # asset names: prefixes (M_, MI_) or a folder name
        for base, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d not in (".git", "Claude", "node_modules", "__pycache__")]
            for w in marks:
                if "file:" + w in hits[g]:
                    continue
                if w.endswith("_") and any(n.startswith(w) and n.endswith(".uasset") for n in files):
                    hits[g].append("file:" + w)
                elif not w.endswith("_") and w in dirs:
                    hits[g].append("file:" + w)
    return {"ok": True, "techniques": [{"slug": g, "markers_found": h} for g, h in hits.items() if h]}


def materials_inventory(project_dir):
    """Read-only inventory of material assets by folder and prefix (names only, binaries are not parsed)."""
    kinds = {"M_": "parent", "MI_": "instance", "MF_": "function", "MPC_": "collection", "T_": "texture"}
    folders, total = {}, {k: 0 for k in kinds.values()}
    for base, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in (".git", "Claude", "node_modules", "__pycache__")]
        for n in files:
            if not n.endswith(".uasset"):
                continue
            for pre in ("MPC_", "MI_", "MF_", "M_", "T_"):
                if n.startswith(pre):
                    k = kinds[pre]
                    rel = os.path.relpath(base, project_dir).replace(os.sep, "/")
                    e = folders.setdefault(rel, {"parent": [], "instance": [], "function": [], "collection": [], "texture": []})
                    e[k].append(n[:-7])
                    total[k] += 1
                    break
    return {"ok": True, "totals": total, "folders": {f: {k: v for k, v in e.items() if v} for f, e in sorted(folders.items())}}


# ----------------------------------------------------------------------------- recipes (v1.87.2)
# A recipe = "start from this known asset, change these parameters". Official ones ship in
# <skill>/official/recipes-official.json; learned ones live in <skill>/local/recipes.json (never overwritten by
# profile updates). A learned recipe starts as hypothesis, confirmed when reused in a 2nd map (maps are counted once);
# one learned in a Fab product is confirmed at once.
def _fab_lab_base():
    return os.environ.get("UEFN_FAB_LAB_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "fab-lab")


def _fab_products():
    names = []
    try:
        names = [d for d in os.listdir(_fab_lab_base()) if os.path.isdir(os.path.join(_fab_lab_base(), d))]
    except OSError:
        pass
    try:   # products registered as Fab (kit_install.py --kind): the name an agent gives may be the project folder or the registered name
        with open(os.path.join(os.path.expanduser("~"), ".claude", "kit-projects.json"), encoding="utf-8") as f:
            for path, v in json.load(f).items():
                if isinstance(v, dict) and v.get("kind") == "fab":
                    names += [os.path.basename(path.rstrip("/\\")), v.get("name", "")]
    except (OSError, ValueError, AttributeError):
        pass
    return [n for n in names if n]


def _fab_map_keys():
    """Map keys of the Fab products (a recipe learned in a Fab product is confirmed at once: the owner checks it in the editor)."""
    out = set()
    for d in _fab_products():
        out |= name_keys(d) | {_map_key(d)}
    return out


def recipes_list(slug, query=""):
    try:
        slug = resolve_genre(slug)
    except ValueError:   # a skill that does not exist yet has no recipes
        return {"ok": True, "recipes": []}
    out = []
    op = os.path.join(gdir(slug), "official", "recipes-official.json")
    for r in (_read_json(op, {"recipes": []}).get("recipes", []) if os.path.isfile(op) else []):
        out.append(r)
    lp = os.path.join(ldir(slug), "recipes.json")
    for r in (_read_json(lp, {"recipes": []}).get("recipes", []) if os.path.isfile(lp) else []):
        fab = r.get("fab") or any(k in _fab_map_keys() for k in r.get("maps", []))
        r["tier"] = "confirmed" if (fab or len(r.get("maps", [])) >= 2) else "hypothesis"
        out.append(r)
    q = (query or "").lower().strip()
    if q:
        out = [r for r in out if q in (r.get("name", "") + " " + r.get("use", "") + " " + r.get("parent", "")).lower()]
    return {"ok": True, "recipes": out}


# A mechanic recipe (skill "mechanics": a stand-alone device, a Verse mechanic, a whole map template) says how to REBUILD it:
# kind, devices (what to place), settings (what to set on each), wiring (what is connected to what), files ([{name, code}] Verse),
# assets it needs, verify (how to see that it works), plus the steps. Materials keep using parent + params.
RECIPE_FIELDS = ("parent", "use", "steps", "params", "kind", "devices", "settings", "wiring", "files", "assets", "verify")


def recipe_add(slug, recipe, map_name):
    """Add or update a learned recipe; the map counts once. recipe: name, parent, use, steps[], params[]."""
    slug = _slug(slug)
    name = _norm(recipe.get("name", ""))
    if not name or not recipe.get("steps") or (slug == "materials" and not recipe.get("parent")):
        return {"ok": False, "error": "recipe needs name and steps (materials also a parent)"}
    for k in ("files",):   # code of a mechanic: kept whole, but only reasonable sizes and plain {name, code} items
        fl = recipe.get(k)
        if fl is not None and (not isinstance(fl, list) or any(not isinstance(x, dict) or not x.get("name") or len(str(x.get("code", ""))) > 40000 for x in fl)):
            return {"ok": False, "error": "files must be a list of {name, code} (code up to 40000 characters each)"}
    mk = _map_key(map_name)
    lp = os.path.join(ldir(slug), "recipes.json")
    os.makedirs(ldir(slug), exist_ok=True)
    data = _read_json(lp, {"recipes": []})
    for r in data["recipes"]:
        if _norm(r.get("name", "")) == name:
            if mk not in r.get("maps", []):
                r.setdefault("maps", []).append(mk)
            for k in RECIPE_FIELDS:
                if recipe.get(k):
                    r[k] = recipe[k]
            _write_json(lp, data)
            return {"ok": True, "updated": True, "maps": len(r["maps"])}
    data["recipes"].append({"name": name, "origin": "owner", "parent": recipe.get("parent", ""), "use": recipe.get("use", ""),
                            "steps": recipe["steps"], "params": recipe.get("params", []), "maps": [mk], "added": _today(),
                            **{k: recipe[k] for k in RECIPE_FIELDS if k not in ("parent", "use", "steps", "params") and recipe.get(k)},
                            **({"fab": True} if mk in _fab_map_keys() else {})})
    _write_json(lp, data)
    return {"ok": True, "updated": False, "maps": 1}


def recipe_share(slug, name, decision):
    """The owner decides whether a learned recipe goes into the kit for everyone: 'approved', 'declined' or 'pending' (back to undecided).
    Only approved ones are collected at release time (tool/collect_recipes.py)."""
    slug = resolve_genre(slug)
    if decision not in ("approved", "declined", "pending"):
        return {"ok": False, "error": "decision must be approved, declined or pending"}
    lp = os.path.join(ldir(slug), "recipes.json")
    data = _read_json(lp, {"recipes": []})
    for r in data["recipes"]:
        if _norm(r.get("name", "")) == _norm(name):
            r["share"] = decision
            r["share_at"] = _today()
            _write_json(lp, data)
            return {"ok": True}
    return {"ok": False, "error": "no such recipe"}


# ----------------------------------------------------------------------------- recipes: to the community and from it (same logic as lessons)
# You approve a recipe ("Share in the kit"), then send it as a GitHub proposal (nothing is sent by the kit). What the community shares comes back
# with a kit update as <skill>/community/recipes-community.json: it waits in the inbox until YOU approve it. Every recipe is screened
# (recipe_screen.py) on the way out and again on the way in.
def recipe_id(name):
    return "r-" + hashlib.sha1(_norm(name).encode("utf-8")).hexdigest()[:12]


def recipe_export(slug, name):
    """The exact JSON that would leave this computer for ONE recipe you approved, plus the GitHub page to propose it. Refused while the switch is off."""
    if not community_state()["share"]:
        return {"ok": False, "error": "sharing with the community is switched off"}
    slug = resolve_genre(slug)
    data = _read_json(os.path.join(ldir(slug), "recipes.json"), {"recipes": []})
    r = next((x for x in data["recipes"] if _norm(x.get("name", "")) == _norm(name or "")), None)
    if not r or r.get("origin") != "owner":
        return {"ok": False, "error": "only a recipe of yours can be sent"}
    if r.get("share") == "declined":
        return {"ok": False, "error": "you kept this recipe private"}
    import recipe_screen as RS
    rec = {k: r[k] for k in RS.FIELDS if r.get(k) not in (None, "", [])}
    rec.setdefault("kind", "material" if slug == "materials" else "mechanic")
    chk = RS.check(rec)
    if not chk["ok"]:
        return {"ok": False, "error": "the recipe does not pass the check: " + "; ".join(chk["reasons"][:3])}
    doc = {"schema_version": 1, "skill": slug, "recipe": rec, "kit_version": _kit_version()}
    value = json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=1)
    path = "contributions/recipes/%s/%s/<your-github-handle>.json" % (slug, recipe_id(name))
    url, pre, path = _gh_url(path, value, "Community recipe: %s (%s)" % (rec.get("name", "recipe"), slug))
    return {"ok": True, "doc": doc, "json": value, "filename": path, "url": url, "note": _gh_note(pre), "recipe_kind": True}


def _inbox_path():
    return os.path.join(skills_root(), "recipes-inbox.json")


def _inbox():
    d = _read_json(_inbox_path(), {})
    return {"pending": [x for x in d.get("pending", []) if isinstance(x, dict)], "decided": d.get("decided", {}) if isinstance(d.get("decided"), dict) else {}}


def import_community_recipes(genre_dir_root=None):
    """Recipes the community shared (shipped with the kit in <skill>/community/recipes-community.json) go into the inbox: checked again here,
    nothing is saved as a recipe until you approve. Idempotent."""
    import recipe_screen as RS
    root = genre_dir_root or genre_root()
    ib = _inbox()
    known = {x["id"] for x in ib["pending"]} | set(ib["decided"])
    out = {"queued": 0, "rejected": 0}
    for g in (sorted(os.listdir(root)) if os.path.isdir(root) else []):
        fp = os.path.join(root, g, "community", "recipes-community.json")
        if not os.path.isfile(fp):
            continue
        try:
            arr = _read_json(fp, {}, base=root).get("recipes", [])
        except Exception:
            arr = []
        for r in arr if isinstance(arr, list) else []:
            if not isinstance(r, dict) or not isinstance(r.get("name"), str):
                out["rejected"] += 1; continue
            rid = recipe_id(g + "/" + r["name"])
            if rid in known:
                continue
            body = {k: v for k, v in r.items() if k in RS.FIELDS}
            if not RS.check(body)["ok"]:
                out["rejected"] += 1
                continue
            ib["pending"].append({"id": rid, "skill": g, "recipe": body, "contributors": int(r.get("contributors", 1)) if str(r.get("contributors", 1)).isdigit() else 1})
            known.add(rid); out["queued"] += 1
    if out["queued"]:
        _write_json(_inbox_path(), ib)
    return out


def recipe_inbox():
    ib = _inbox()
    return {"pending": [{"id": x["id"], "skill": x["skill"], "name": x["recipe"].get("name"), "kind": x["recipe"].get("kind"), "use": x["recipe"].get("use", ""),
                         "steps": len(x["recipe"].get("steps", [])), "files": [f["name"] for f in x["recipe"].get("files", [])],
                         "settings": len(x["recipe"].get("settings", [])), "contributors": x.get("contributors", 1)} for x in ib["pending"]],
            "decided": len(ib["decided"])}


def recipe_inbox_act(rid, decision):
    """approve: the recipe joins your recipes (origin community, a hypothesis until a second project uses it, never offered again for sharing).
    reject: it is kept as rejected and never shown again. Nothing is deleted."""
    if decision not in ("approve", "reject"):
        return {"ok": False, "error": "decision must be approve or reject"}
    ib = _inbox()
    it = next((x for x in ib["pending"] if x["id"] == rid), None)
    if not it:
        return {"ok": False, "error": "not in the inbox"}
    if decision == "approve":
        import recipe_screen as RS
        if not RS.check(it["recipe"])["ok"]:
            return {"ok": False, "error": "the recipe does not pass the check"}
        slug = resolve_genre(it["skill"])
        lp = os.path.join(ldir(slug), "recipes.json")
        os.makedirs(ldir(slug), exist_ok=True)
        data = _read_json(lp, {"recipes": []})
        if not any(_norm(x.get("name", "")) == _norm(it["recipe"]["name"]) for x in data["recipes"]):
            data["recipes"].append(dict(it["recipe"], origin="community", maps=[], share="declined", added=_today()))
            _write_json(lp, data)
    ib["pending"] = [x for x in ib["pending"] if x["id"] != rid]
    ib["decided"][rid] = "approved" if decision == "approve" else "rejected"
    _write_json(_inbox_path(), ib)
    return {"ok": True}


def needs_feeding(slug, threshold=3):
    """True when the skill has few patterns backed by the owner's own maps (reference/official ones do not
    count). Used after an audit to decide whether skill-reflector should be asked for lessons."""
    slug = _slug(slug)
    if not os.path.isdir(gdir(slug)):
        return {"ok": True, "genre": slug, "exists": False, "owner_backed": 0, "needs": True}
    pats = load_pack(slug)["patterns"]
    own = [x for x in pats if x.get("tier") != "reference" and x.get("origin") != "official" and x.get("status") != "archived"]
    return {"ok": True, "genre": slug, "exists": True, "patterns": len(pats), "owner_backed": len(own), "needs": len(own) < threshold}


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
def retarget(old, new):
    """The owner says the genre was guessed wrong: move the lessons still waiting for approval from the old genre skill to the right one.
    Approved patterns are left where they are (reported). Nothing is deleted except the moved proposals."""
    old, new = _slug(old), _slug(new)
    if old == new:
        return {"ok": False, "error": "same genre"}
    init_genre(new)
    moved, failed = 0, []
    for p in list_proposals(old):
        if p.get("kind") != "new_pattern":
            failed.append(p.get("id"))
            continue
        c = p.get("pattern") or {}
        r = propose(new, c.get("variant", "*"), c.get("condition", ""), c.get("action", ""), c.get("statement", ""), p.get("map_name", ""),
                    stance=p.get("stance", "for"), tasks=p.get("tasks", ()), note=p.get("note", ""), metric_backed=bool(p.get("metric_backed")), section=c.get("section", ""))
        if r.get("ok"):
            try:
                _remove_proposal_file(old, _proposal_path(old, p["id"]))
            except Exception:
                pass
            moved += 1
        else:
            failed.append(p.get("id"))
    kept = len([x for x in load_pack(old)["patterns"] if x.get("status") != "superseded"])
    return {"ok": True, "moved": moved, "not_moved": failed, "approved_patterns_left_in_old_genre": kept}


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


def recipes_overview():
    """Recipes of every skill (official + learned) for the Skills page: name, what for, parent, tier, maps that used it. Never raises."""
    out = []
    try:
        for s in _genres():
            has = os.path.isfile(os.path.join(gdir(s), "official", "recipes-official.json")) or os.path.isfile(os.path.join(ldir(s), "recipes.json"))
            if not has:
                continue
            for r in recipes_list(s).get("recipes", []):
                owner = r.get("origin") == "owner"
                out.append({"skill": s, "name": r.get("name", ""), "use": (r.get("use") or "")[:200], "parent": r.get("parent", ""),
                            "source": "yours" if owner else ("community" if r.get("origin") == "community" else "official"), "tier": r.get("tier", "official"), "maps": len(r.get("maps", [])),
                            "steps": len(r.get("steps", [])), "added": r.get("added", ""), "kind": r.get("kind", ""), "share": ("declined" if r.get("share") == "declined" else "approved") if owner else "", "rid": recipe_id(r.get("name", ""))})
    except Exception:
        pass
    return out


def project_name(project):
    """Name the kit uses for a project: its folder, or the folder above it when the kit lives in .../<Project>/Content."""
    p = os.path.abspath(project)
    b = os.path.basename(p)
    return (os.path.basename(os.path.dirname(p)) or b) if b.lower() == "content" else b


def recipes_of(name):
    """Recipes (name, skill, kind) that came from the project called `name`."""
    keys = name_keys(name) | {_map_key(name)}
    out = []
    try:
        for s in _genres():
            for r in recipes_list(s).get("recipes", []):
                if keys & set(r.get("maps", [])):
                    out.append({"name": r.get("name", ""), "skill": s, "kind": r.get("kind", "")})
    except Exception:
        pass
    return out


def _learn_flag_path(project):
    return os.path.join(project, "Claude", "logs", "learn-request.json")


def map_learn_flag(project):
    """State of the Learn button of a map project: None, or {"state": "waiting"|"sent", "at", "sent_at"}."""
    try:
        with open(_learn_flag_path(project), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def map_learn_request(project):
    """The owner pressed Learn on the console: prepare the recipes of the map now (no AI) and ask the agent, once, at the end of
    its next answer (learn_nudge.py reads the flag). Returns {"recipes": [names saved now]}."""
    saved = []
    try:
        import mechanic_recipes as _mr
        saved = _mr.ensure_map(project, project_name(project), recipe_add)
    except Exception:
        saved = []
    p = _learn_flag_path(project)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"state": "waiting", "at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}, f)
    return {"recipes": saved}


def projects_overview():
    """Every project the kit learns from, for the Skills page (Maps & products): analysed maps (maps.json of each genre) and Fab products
    (lab folders + registry). Per row: name, kind, genre, how many lessons and recipes it supports, and a 0/50/100 learning percentage. Never raises."""
    rows = {}
    try:
        fabk = _fab_map_keys()
        rec_keys = {}   # key -> the recipes (skill + name) that came from it
        for s in _genres():
            for r in recipes_list(s).get("recipes", []):
                for k in r.get("maps", []):
                    rec_keys.setdefault(k, set()).add((s, recipe_id(r.get("name", ""))))
        for s in _genres():
            sup = _support(s)
            les = {}
            for pid, v in sup.items():
                for k in (v.get("for") or []):
                    les[k] = les.get(k, 0) + 1
            for k, m in _maps(s).items():
                name = (m.get("name") if isinstance(m, dict) else "") or k
                r = rows.setdefault(k, {"name": name, "kind": "fab" if k in fabk else "map", "genre": s, "lessons": 0, "recipes": 0,
                                        "first_seen": (m.get("first_seen") if isinstance(m, dict) else "") or ""})
                r["lessons"] += les.get(k, 0)
        for n in _fab_products():
            k = _map_key(n)
            rows.setdefault(k, {"name": n, "kind": "fab", "genre": "", "lessons": 0, "recipes": 0, "first_seen": ""})["kind"] = "fab"
        try:   # every project registered with the kit (kit_install.py --kind), maps included: a map that only has recipes is still listed
            with open(os.path.join(os.path.expanduser("~"), ".claude", "kit-projects.json"), encoding="utf-8") as f:
                for path, v in json.load(f).items():
                    if isinstance(v, dict) and v.get("kind") in ("map", "fab"):
                        n = v.get("name") or os.path.basename(path.rstrip("/\\"))
                        rows.setdefault(_map_key(n), {"name": n, "kind": v["kind"], "genre": "", "lessons": 0, "recipes": 0, "first_seen": ""})
        except (OSError, ValueError, AttributeError):
            pass
        for k, r in rows.items():
            found = set()
            for kk in name_keys(r["name"]) | {k}:
                found |= rec_keys.get(kk, set())
            r["recipes"] = len(found)
            r["skills"] = sorted({x[0] for x in found} | ({r["genre"]} if r.get("genre") else set()))   # the skills this project feeds
            if r["kind"] == "fab":
                r["pct"] = 100 if r["recipes"] else 50
            else:
                r["pct"] = 50 * (r["lessons"] > 0) + 50 * (r["recipes"] > 0)
    except Exception:
        pass
    return sorted(rows.values(), key=lambda r: (r["kind"], r["name"].lower()))


def is_maintainer():
    """True on the computer of the kit maintainer (update-my-profile.cmd / publish.ps1 leave skills/maintainer.json there). The maintainer releases from the console at publish time, so nothing is sent through GitHub."""
    if os.environ.get("UEFN_MAINTAINER") == "1":
        return True
    return maintainer_available() and _read_json(os.path.join(skills_root(), "maintainer.json"), {}).get("active") is not False


def maintainer_available():
    """This computer belongs to the maintainer (it may still be switched to the contributor view to test what users see)."""
    return _isfile(os.path.join(skills_root(), "maintainer.json"))


def set_maintainer_mode(mode):
    if not maintainer_available():
        return {"ok": False, "error": "this computer is not marked as the maintainer's"}
    if mode not in ("maintainer", "contributor"):
        return {"ok": False, "error": "mode must be maintainer or contributor"}
    _write_json(os.path.join(skills_root(), "maintainer.json"), {"maintainer": True, "active": mode == "maintainer"})
    return {"ok": True, "mode": mode}


def hold_path():
    return os.path.join(skills_root(), "release-hold.json")


def load_hold():
    """What the maintainer keeps out of the next release: {"skills": [slug], "lessons": [id]}. Everything else goes out."""
    d = _read_json(hold_path(), {})
    d = d if isinstance(d, dict) else {}
    return {k: [x for x in d.get(k, []) if isinstance(x, str)] for k in ("skills", "lessons", "mcp")}


def hold_set(kind, key, held):
    """Tick or untick 'release' on a skill or a lesson of the Skills page. Only names that exist on this computer are accepted."""
    d = load_hold()
    if kind == "skill":
        key = resolve_genre(key)
        lst = d["skills"]
    elif kind == "mcp":
        if not re.fullmatch(r"[\w.]{1,120}/\w{1,80}", key or ""):
            return {"ok": False, "error": "unknown tool"}
        lst = d["mcp"]
    elif kind == "lesson":
        if not any(p.get("id") == key for s in _genres() for p in load_pack(s)["patterns"]):
            return {"ok": False, "error": "unknown lesson"}
        lst = d["lessons"]
    else:
        return {"ok": False, "error": "kind must be skill or lesson"}
    if held and key not in lst:
        lst.append(key)
    if not held and key in lst:
        lst.remove(key)
    _write_json(hold_path(), d)
    return {"ok": True, "hold": d}


def hold_set_many(kind, keys, held):
    """The same as hold_set for a whole list at once (the Promote all / Keep all private buttons)."""
    if kind not in ("skill", "lesson", "mcp") or not isinstance(keys, list) or len(keys) > 2000:
        return {"ok": False, "error": "kind must be skill, lesson or mcp and keys a list"}
    d = load_hold()
    lst = d["skills"] if kind == "skill" else (d["mcp"] if kind == "mcp" else d["lessons"])
    known = set(_genres()) if kind == "skill" else ({p.get("id") for s in _genres() for p in load_pack(s)["patterns"]} if kind == "lesson" else None)
    n = 0
    for k in keys:
        if not isinstance(k, str) or (known is not None and k not in known) or (known is None and not re.fullmatch(r"[\w.]{1,120}/\w{1,80}", k)):
            continue
        if held and k not in lst:
            lst.append(k); n += 1
        if not held and k in lst:
            lst.remove(k); n += 1
    _write_json(hold_path(), d)
    return {"ok": True, "changed": n, "hold": d}


def kit_skills():
    """Slugs of the genre skills that ship with the kit (Claude/community/kit-skills.json, written by tool/promote-genre-skills.py at each release)."""
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "community", "kit-skills.json"), encoding="utf-8") as f:
            return {x for x in (json.load(f).get("skills") or []) if isinstance(x, str)}
    except (OSError, ValueError, AttributeError):
        return set()


def kit_lesson_ids(slug):
    """Ids of the lessons that already ship with the kit for this skill (<genre>/community/*.json: what the maintainer released)."""
    ids = set()
    cd = os.path.join(gdir(slug), "community")
    if not _isdir(cd):
        return ids
    for n in _listdir(cd):
        if n.endswith(".json"):
            obj = _read_json(os.path.join(cd, n), {})
            for x in (obj.get("patterns") if isinstance(obj, dict) else None) or []:
                if isinstance(x, dict) and x.get("id"):
                    ids.add(x["id"])
    return ids


def summary():
    """Everything the Skills page shows — computed only from real local files."""
    genres, pending = [], list_proposals()
    totals = {"maps": 0, "patterns": 0, "proven": 0, "confirmed": 0, "hypothesis": 0, "contested": 0, "reference": 0}
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
        in_kit = kit_lesson_ids(s)
        shipped = kit_skills()
        hold = load_hold()
        for p in pack["patterns"]:
            if p.get("status") == "superseded":
                continue
            recompute(p, sup) if p.get("origin") in ("local", "official") else None
            if p["status"] == "contested":
                c["contested"] += 1
            else:
                c[p["tier"]] += 1
            variants_seen.add(p["variant"])
            pats.append({k: p.get(k) for k in ("id", "variant", "statement", "condition", "action", "tier", "status",
                                               "origin", "support", "against", "community_support", "conflicts_with", "section")})
            if p.get("origin") == "local" and p.get("support", 0) >= 1:
                pats[-1]["published"] = lesson_published(s, p["id"])
                pats[-1]["in_kit"] = p["id"] in in_kit
                pats[-1]["hold"] = p["id"] in hold["lessons"]
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
        has_own = any(x.get("origin") == "local" and (x.get("support") or 0) >= 1 for x in pats)
        genres.append({"slug": s, "maps": len(maps), "counts": c, "patterns": pats, "last_learned": ll,
                       "created": led[0]["ts"] if led else None,
                       "hold": s in hold["skills"],
                       "kit": "in" if s in shipped else ("new" if has_own else "none"),
                       "consulted": int(usage.get("total", 0)),
                       "pending": sum(1 for p in pending if p["genre"] == s),
                       "variants": sorted({p["variant"] for p in pats}), "blueprints": blueprints_for(s)})
        for k in ("proven", "confirmed", "hypothesis", "contested", "reference"):
            totals[k] += c[k]
        totals["patterns"] += len(pats)
    totals["maps"] = len(all_maps)
    community = sum(1 for p in pending if p["kind"] == "pack_update")
    oldest = min((p["created"] for p in pending), default=None)
    return {"maintainer": is_maintainer(), "maintainer_available": maintainer_available(), "root": genre_root(), "root_exists": _isdir(genre_root()), "genres": genres, "totals": totals,
            "pending": pending, "pending_lessons": len(pending) - community, "pending_packs": community,
            "recipes": recipes_overview(), "projects": projects_overview(), "oldest_pending": oldest, "variants": len(variants_seen), "last_learned": last_learned,
            "usage_week": [week[d] for d in days], "usage_week_total": sum(week.values()),
            "never_used": sum(1 for g in genres if g["patterns"] and g["consulted"] == 0),
            "privacy": {"checked": check_ts is not None, "ok": check_ok, "ts": check_ts}}


# ----------------------------------------------------------------------------- CLI
def _cli(argv=None):
    for _st in (sys.stdout, sys.stderr):  # Windows pipes default to cp1252; patterns/docs may contain arrows or typographic dashes
        try:
            _st.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="skills_lib.py", description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("summary")
    s = sub.add_parser("init"); s.add_argument("genre")
    s = sub.add_parser("render"); s.add_argument("genre")
    s = sub.add_parser("check"); s.add_argument("genre", nargs="?")
    s = sub.add_parser("export"); s.add_argument("genre"); s.add_argument("out_dir")
    s = sub.add_parser("merge"); s.add_argument("genre"); s.add_argument("pack_file"); s.add_argument("--source", default=""); s.add_argument("--official", action="store_true")
    s = sub.add_parser("techniques"); s.add_argument("project_dir")
    s = sub.add_parser("materials"); s.add_argument("project_dir")
    s = sub.add_parser("needs-feeding"); s.add_argument("genre")
    s = sub.add_parser("recipes"); s.add_argument("genre"); s.add_argument("query", nargs="?", default="")
    s = sub.add_parser("recipe-share"); s.add_argument("genre"); s.add_argument("name"); s.add_argument("decision")
    s = sub.add_parser("recipe-add"); s.add_argument("genre"); s.add_argument("recipe_json_file"); s.add_argument("map_name")
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
    s.add_argument("--metric-backed", action="store_true"); s.add_argument("--section", default="")
    s = sub.add_parser("section"); s.add_argument("genre"); s.add_argument("pattern"); s.add_argument("section")
    s = sub.add_parser("retarget"); s.add_argument("old"); s.add_argument("new")
    s = sub.add_parser("profile-drop"); s.add_argument("genre"); s.add_argument("label")
    s = sub.add_parser("variants-merge"); s.add_argument("genre", nargs="?", default=""); s.add_argument("--project", default="")
    s = sub.add_parser("learning"); s.add_argument("--project", default=".")
    s = sub.add_parser("propose-genre"); s.add_argument("genre"); s.add_argument("--variant", required=True); s.add_argument("--why", default=""); s.add_argument("--project", default=".")
    s = sub.add_parser("confirm-genre"); s.add_argument("genre"); s.add_argument("--variant", required=True); s.add_argument("--project", default=".")
    s = sub.add_parser("profile"); s.add_argument("genre"); s.add_argument("--map", required=True); s.add_argument("--file", required=True); s.add_argument("--project", default="")
    s = sub.add_parser("similar"); s.add_argument("genre"); s.add_argument("--threshold", type=float, default=0.5)
    s = sub.add_parser("community"); s.add_argument("what", choices=["state", "on", "off"]); s.add_argument("--project", default="")
    s = sub.add_parser("mark-shared"); s.add_argument("genre"); s.add_argument("pattern")
    s = sub.add_parser("community-import")
    s = sub.add_parser("sync-published"); s.add_argument("--project", default="."); s.add_argument("--force", action="store_true")
    s = sub.add_parser("contribute"); s.add_argument("genre"); s.add_argument("pattern")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "summary":
            r = summary()
        elif a.cmd == "community":
            r = (community_info(os.path.abspath(a.project)) if a.project else community_state()) if a.what == "state" else set_community(a.what == "on")
        elif a.cmd == "community-import":
            r = import_community_dir()
        elif a.cmd == "mark-shared":
            r = mark_shared(a.genre, a.pattern)
        elif a.cmd == "sync-published":
            r = sync_published(os.path.abspath(a.project), force=a.force)
        elif a.cmd == "contribute":
            r = contribution_export(a.genre, a.pattern)
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
            r = merge_pack(a.genre, obj, a.source or os.path.basename(os.path.dirname(os.path.abspath(a.pack_file))), official=a.official)
        elif a.cmd == "techniques":
            r = detect_techniques(a.project_dir)
        elif a.cmd == "recipes":
            r = recipes_list(a.genre, a.query)
        elif a.cmd == "recipe-share":
            r = recipe_share(a.genre, a.name, a.decision)
        elif a.cmd == "recipe-add":
            with open(a.recipe_json_file, encoding="utf-8") as _f:
                r = recipe_add(a.genre, json.load(_f), a.map_name)
        elif a.cmd == "needs-feeding":
            r = needs_feeding(a.genre)
        elif a.cmd == "materials":
            r = materials_inventory(a.project_dir)
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
            r = [{k: p.get(k) for k in ("id", "variant", "condition", "action", "statement", "tier", "status", "section")}
                 for p in load_pack(_slug(a.genre))["patterns"]]
        elif a.cmd == "retarget":
            r = retarget(a.old, a.new)
        elif a.cmd == "variants-merge":
            r = merge_variants(a.genre or None, os.path.abspath(a.project) if a.project else None)
        elif a.cmd == "profile-drop":
            r = drop_profile(a.genre, a.label)
        elif a.cmd == "learning":
            r = console_learning(os.path.abspath(a.project))
        elif a.cmd == "propose-genre":
            r = propose_genre(os.path.abspath(a.project), a.genre, a.variant, a.why)
        elif a.cmd == "confirm-genre":
            r = confirm_genre(os.path.abspath(a.project), a.genre, a.variant)
        elif a.cmd == "profile":
            r = save_profile(a.genre, a.map, json.load(open(a.file, encoding="utf-8-sig")), a.project or None)
        elif a.cmd == "similar":
            r = similar(a.genre, a.threshold)
        elif a.cmd == "section":
            r = set_section(a.genre, a.pattern, a.section)
        elif a.cmd == "act":
            r = act(a.genre, a.proposal, a.action, a.statement, a.exclude)
        else:
            r = propose(a.genre, a.variant, a.condition, a.act_, a.statement, a.map_name, a.stance,
                        a.task, a.note, a.metric_backed, a.section)
    except (ValueError, OSError) as e:
        r = {"ok": False, "error": str(e)}
    # Redact secret-looking strings before anything reaches stdout/logs (clear-text logging fix).
    print(redact(json.dumps(r, indent=2, ensure_ascii=False)))
    return 0 if not (isinstance(r, dict) and r.get("ok") is False) else 1


if __name__ == "__main__":
    sys.exit(_cli())
