"""Community lesson file: structure check (handle = PR author, id = content hash)."""
import os, sys, copy
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(root, "tool"))
import contrib_schema as C
L = C.L
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))

cond, act = "a round starts", "teleport everyone from one manager"
GOOD = {"schema_version": 1, "pattern_id": L.pattern_id("pillars", cond, act), "genre": "survival", "variant": "pillars", "section": "run-loop",
        "direction": "for", "statement": "Start rounds from one manager.", "condition": cond, "action": act, "kit_version": "1.99.0"}
PATH = "contributions/survival/%s/ada.json" % GOOD["pattern_id"]
ok(C.validate(GOOD, "ada", PATH) == [], "valid lesson passes")
ok(C.validate(GOOD, "Ada", PATH) == [], "handle case does not matter")


def bad(msg, field, handle="ada", path=PATH, **chg):
    d = copy.deepcopy(GOOD); d.update(chg)
    r = C.validate(d, handle, path)
    ok(any(field in e for e in r), "%s -> error naming %s" % (msg, field))


bad("wrong schema_version", "schema_version", schema_version=2)
bad("genre not official", "genre", genre="not-a-genre")
bad("bad variant", "variant", variant="Pillars!")
bad("unknown section", "section", section="secret-section")
bad("direction other", "direction", direction="maybe")
bad("statement too long", "statement", statement="x" * 201)
bad("condition empty", "condition", condition="  ")
bad("bad kit version", "kit_version", kit_version="latest")
bad("id not the content hash", "pattern_id", pattern_id="p-000000000000")
bad("id bad format", "pattern_id", pattern_id="123")
bad("path with another handle", "path", handle="eve")
bad("path outside the lesson folder", "path", path="contributions/survival/x/ada.json")
d = copy.deepcopy(GOOD); d["extra"] = "x"
ok(any("extra" in e for e in C.validate(d, "ada", PATH)), "unknown extra key is refused")
d = copy.deepcopy(GOOD); del d["action"]
ok(any("action" in e for e in C.validate(d, "ada", PATH)), "missing field is refused")
ok(C.validate([], "ada", PATH) != [], "non-object refused")
ok(any("handle" in e for e in C.validate(GOOD, "bad handle!", PATH)), "handle must look like a GitHub handle")
