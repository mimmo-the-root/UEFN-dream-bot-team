"""Curator: regenerates lessons from verified fields, holds back orders, never copies the contributor's wording, reports everything."""
import json, os, sys, tempfile
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(root, "tool"))
import curator as U, classify as K
L = U.L
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
tmp = tempfile.mkdtemp(); croot = os.path.join(tmp, "contributions")


def put(handle, cond, act, statement="Zebra Quartz rule."):
    doc = {"schema_version": 1, "pattern_id": L.pattern_id("base", cond, act), "genre": "survival", "variant": "base", "section": "run-loop",
           "direction": "for", "statement": statement, "condition": cond, "action": act, "kit_version": "1.99.0"}
    d = os.path.join(croot, "survival", doc["pattern_id"]); os.makedirs(d, exist_ok=True)
    json.dump(doc, open(os.path.join(d, handle + ".json"), "w"))
    return doc["pattern_id"]


a = put("ada", "a round starts", "teleport everyone from one manager")
b = put("bob", "players join late", "give them the current score")
c = put("eve", "a timer ends", "reset the lobby quickly")
intake = {"lessons": {
    a: {"genre": "survival", "state": "confirmed", "handles": ["ada", "bob"], "verdict": "pass", "reasons": []},
    b: {"genre": "survival", "state": "hypothesis", "handles": ["bob"], "verdict": "pass", "reasons": []},
    c: {"genre": "survival", "state": "hypothesis", "handles": ["eve"], "verdict": "pass", "reasons": []},
    "p-aaaaaaaaaaaa": {"genre": "survival", "state": "archived", "handles": [], "verdict": "pass", "reasons": ["link"]}}}


def fake(text):
    return "orders" if "reset the lobby" in text else "fact"


r = U.build_promotion(intake, croot, classify_fn=fake, today="2026-10-14")
pats = {p["id"]: p for p in r["packs"]["survival"]["patterns"]}
ok(set(pats) == {a, b}, "promoted: confirmed and hypothesis; archived and 'orders' are not")
ok(pats[a]["statement"] == "When a round starts: teleport everyone from one manager." and pats[a]["support"] == 2, "statement is the template, support = number of handles")
ok("Zebra" not in json.dumps(r["packs"]), "the contributor's own statement is never copied")
ok(all(p["tier"] == "hypothesis" and p["origin" if False else "status"] == "active" for p in pats.values()), "everything arrives as hypothesis")
ok(c in r["report_md"] and "orders" in r["report_md"] and "`@ada`, `@bob`" in r["report_md"], "the report lists the held-back lesson and the sources")
ok(r["packs"]["survival"]["pack_version"] == 20261014 and r["packs"]["survival"]["schema"] == 1, "pack format is the one merge_pack reads")
r2 = U.build_promotion(intake, croot, existing={"survival": {a}}, classify_fn=fake)
ok(a not in {p["id"] for p in r2["packs"]["survival"]["patterns"]}, "a lesson already in the pack is not added again")
ok(K.classify("x") == "unchecked" or os.environ.get("ANTHROPIC_API_KEY"), "without a key the classifier answers unchecked")
ok(K.classify("x", call=lambda p: "FACT.") == "fact" and K.classify("x", call=lambda p: "ORDERS") == "orders" and K.classify("x", call=lambda p: "maybe") == "unchecked", "classifier maps one word, anything else is unchecked")
ok(K.classify("x", call=lambda p: 1 / 0) == "unchecked", "a failing call is unchecked, never an error")
r3 = U.build_promotion(intake, croot, classify_fn=lambda t: "unchecked")
ok(len(r3["packs"]["survival"]["patterns"]) == 3 and "unchecked" in r3["report_md"], "unchecked lessons are included and marked for the owner")
ok(U._md("hi @mallory see #12 `x`") == "`hi @mallory see #12 'x'`", "contributor text in the PR body sits in a code span, no mention or link")
ok("`@ada`" in r["report_md"] and "> `When" in r["report_md"], "handles and statements are code spans in the report")
ok(len(U.canonical_statement("c" * 100, "a" * 300)) <= L.MAX_STATEMENT, "the statement never exceeds the limit")
