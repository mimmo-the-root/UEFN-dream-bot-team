#!/usr/bin/env python3
"""contrib_recipe.py - check of one community RECIPE file (contributions/recipes/<skill>/<recipe_id>/<handle>.json).

validate(doc, handle, rel_path) -> list of errors (empty = valid): the structure, then recipe_screen.check (instruction phrases, links, commands,
paths, secrets, hidden characters, Verse code). Identity is the PR author, never a field of the file."""
import json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "project-template", "Claude", "hooks"))
import recipe_screen as RS  # noqa: E402
import skills_lib as L  # noqa: E402

SKILLS = ("materials", "mechanics")


def validate(doc, handle, rel_path):
    if not isinstance(doc, dict):
        return ["file: not a JSON object"]
    if set(doc) != {"schema_version", "skill", "recipe", "kit_version"}:
        return ["file: fields must be exactly schema_version, skill, recipe, kit_version"]
    err = []
    if doc["schema_version"] != 1 or isinstance(doc["schema_version"], bool):
        err.append("schema_version: must be 1")
    if doc["skill"] not in SKILLS:
        err.append("skill: one of %s" % ", ".join(SKILLS))
    if not isinstance(doc["kit_version"], str) or not re.fullmatch(r"\d{1,3}\.\d{1,3}\.\d{1,3}", doc["kit_version"]):
        err.append("kit_version: must look like 1.99.0")
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", handle or ""):
        err.append("handle: not a GitHub handle")
    if err:
        return err
    c = RS.check(doc["recipe"])
    err += ["recipe: " + r for r in c["reasons"]]
    if not err:
        want = "contributions/recipes/%s/%s/%s.json" % (doc["skill"], L.recipe_id(doc["recipe"]["name"]), handle.lower())
        if (rel_path or "").replace("\\", "/").lower() != want.lower():
            err.append("path: must be %s" % want)
    return err


if __name__ == "__main__":
    bad = 0
    for p in sys.argv[1:]:
        rel = os.path.relpath(p, os.getcwd()).replace("\\", "/")
        try:
            with open(p, encoding="utf-8") as f:
                e = validate(json.load(f), os.path.splitext(os.path.basename(p))[0], rel)
        except (OSError, ValueError) as ex:
            e = ["file: %s" % ex]
        for m in e:
            print("%s: %s" % (rel, m))
        bad += bool(e)
    sys.exit(1 if bad else 0)
