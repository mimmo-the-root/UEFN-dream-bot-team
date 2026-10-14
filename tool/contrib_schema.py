#!/usr/bin/env python3
"""contrib_schema.py - structure check of one community lesson file (contributions/<genre>/<pattern_id>/<handle>.json).

validate(doc, handle, rel_path) -> list of error strings (empty = valid). Identity is the PR author (`handle`), never a field of the file.
The pattern id must be the content hash the kit already uses, so a file cannot claim another lesson's id."""
import json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "project-template", "Claude", "hooks"))
import skills_lib as L  # noqa: E402

SCHEMA_VERSION = 1
FIELDS = ("schema_version", "pattern_id", "genre", "variant", "section", "direction", "statement", "condition", "action", "kit_version")
DEFAULT_SECTIONS = ("run-loop", "architecture", "devices", "progression", "death-strategies", "persistence", "performance", "launch-checklist")
HANDLE_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
VERSION_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}$")
ALLOWED_TEXT = re.compile(r"^[\x20-\x7e\u2018\u2019\u201c\u201d\u2013\u2014\u2026\u00d7]*$")
LIMITS = {"statement": L.MAX_STATEMENT, "condition": L.MAX_CONDITION, "action": L.MAX_ACTION}


def genres():
    try:
        with open(os.path.join(ROOT, "user-level-skills", "genre", "fortnite-genres-official.json"), encoding="utf-8") as f:
            return {g["slug"] for g in json.load(f)["genres"]}
    except (OSError, ValueError, KeyError):
        return set()


def sections():
    out = set(DEFAULT_SECTIONS)
    base = os.path.join(ROOT, "user-level-skills", "genre")
    for g in (os.listdir(base) if os.path.isdir(base) else []):
        p = os.path.join(base, g, "references", "starter-sections.json")
        try:
            with open(p, encoding="utf-8") as f:
                out |= {s["id"] for s in json.load(f)["sections"]}
        except (OSError, ValueError, KeyError, TypeError):
            pass
    return out


def validate(doc, handle, rel_path):
    if not isinstance(doc, dict):
        return ["file: not a JSON object"]
    err = []
    for k in doc:
        if k not in FIELDS:
            err.append("%s: unknown field" % k)
    for k in FIELDS:
        if k not in doc:
            err.append("%s: missing" % k)
    if err:
        return err
    if doc["schema_version"] != SCHEMA_VERSION or isinstance(doc["schema_version"], bool):
        err.append("schema_version: must be %d" % SCHEMA_VERSION)
    for k in FIELDS[1:]:
        if not isinstance(doc[k], str):
            err.append("%s: must be a string" % k)
    if err:
        return err
    if not HANDLE_RE.fullmatch(handle or ""):
        err.append("handle: not a GitHub handle")
    if not re.fullmatch(r"p-[0-9a-f]{12}", doc["pattern_id"]):
        err.append("pattern_id: bad format")
    if doc["genre"] not in genres():
        err.append("genre: not in fortnite-genres-official.json")
    if not L.VARIANT_RE.fullmatch(doc["variant"]):
        err.append("variant: must be a lowercase slug or '*'")
    if doc["section"] not in sections():
        err.append("section: unknown section")
    if doc["direction"] not in ("for", "against"):
        err.append("direction: must be 'for' or 'against'")
    if not VERSION_RE.fullmatch(doc["kit_version"]):
        err.append("kit_version: must look like 1.99.0")
    for k, lim in LIMITS.items():
        v = doc[k]
        if not v.strip():
            err.append("%s: empty" % k)
        elif len(v) > lim:
            err.append("%s: longer than %d characters" % (k, lim))
        elif not ALLOWED_TEXT.match(v):
            err.append("%s: unusual characters (only plain English text is accepted)" % k)
    if not err and doc["pattern_id"] != L.pattern_id(doc["variant"], doc["condition"], doc["action"]):
        err.append("pattern_id: does not match variant + condition + action")
    want = "contributions/%s/%s/%s.json" % (doc["genre"], doc["pattern_id"], (handle or "").lower())
    if (rel_path or "").replace("\\", "/").lower() != want.lower():
        err.append("path: must be %s" % want)
    return err


if __name__ == "__main__":
    bad = 0
    for p in sys.argv[1:]:
        rel = os.path.relpath(p, os.getcwd()).replace("\\", "/")
        handle = os.path.splitext(os.path.basename(p))[0]
        try:
            with open(p, encoding="utf-8") as f:
                e = validate(json.load(f), handle, rel)
        except (OSError, ValueError) as ex:
            e = ["file: %s" % ex]
        for m in e:
            print("%s: %s" % (rel, m))
        bad += bool(e)
    sys.exit(1 if bad else 0)
