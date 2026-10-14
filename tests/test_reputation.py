"""Reputation: outcomes, not volume."""
import os, sys
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(root, "tool"))
from reputation import compute
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
E = lambda state, hs, genre="survival", blocked=(): {"state": state, "handles": list(hs), "genre": genre, "blocked_handles": list(blocked)}
r = compute({"lessons": {"p-000000000001": E("confirmed", ["ada"])}})["handles"]["ada"]
ok(r["score"] == 3 and r["confirmed"] == 1 and r["genres"] == ["survival"], "one confirmed lesson: +3")
r = compute({"lessons": {"p-000000000001": E("confirmed", ["ada", "bob"])}})["handles"]
ok(r["ada"]["score"] == 4 and r["bob"]["score"] == 4, "a second independent handle: +3 +1 for each")
r = compute({"lessons": {"p-000000000001": E("hypothesis", ["ada"])}})["handles"]["ada"]
ok(r["score"] == 0 and r["strict"] is True, "a hypothesis scores 0 and the handle stays strict")
r = compute({"lessons": {"p-000000000001": E("archived", [], blocked=["eve"])}})["handles"]["eve"]
ok(r["score"] == 0 and r["lessons"] == 1, "a blocked contribution scores 0 and is counted as a lesson")
r = compute({"lessons": {"p-000000000001": E("confirmed", ["ada"])}}, {"ids": ["p-000000000001"], "handles": []})["handles"]["ada"]
ok(r["score"] == -5, "a revoked lesson: -5, and the +3 is not given")
r = compute({"lessons": {"p-000000000001": E("confirmed", ["ada"])}}, {"ids": [], "handles": ["ADA"]})["handles"]["ada"]
ok(r["score"] < 0 and r["strict"], "a revoked handle goes negative")
i = {"lessons": {"p-000000000001": E("confirmed", ["ada", "bob"]), "p-000000000002": E("hypothesis", ["bob"])}}
ok(compute(i) == compute(i), "deterministic")
ok(compute({})["handles"] == {}, "empty intake gives empty reputation")
