#!/usr/bin/env python3
"""Tests for mcp_lessons.py with a synthetic ledger in a temp folder. Exit 1 on any FAIL."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "project-template", "Claude", "hooks"))
import mcp_lessons as ml  # noqa: E402

FAILS = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        FAILS.append(name)


def row(tool, r, peek, args="{}", t="10:00:00", toolset="TS.Tools"):
    d = {"t": t, "toolset": toolset, "tool": tool, "args": args, "r": r}
    d["peek" if r == "ok" else "why"] = peek
    return d


def main():
    g1 = "12345678-1234-1234-1234-123456789abc"
    g2 = "abcdef01-2345-6789-abcd-ef0123456789"
    rows = [
        row("a", "ok", "fine"),
        # same error, different guid/asset: one signature, 3 distinct calls
        row("make", "rejected", "FolderPath \"/%s/UI_T001\" is outside roots (/Game/Foo/Bar)" % g1, '{"n":1}', "10:00:01"),
        row("make", "rejected", "FolderPath \"/%s/UI_T002\" is outside roots (/Game/Baz)" % g2, '{"n":2}', "10:00:02"),
        row("make", "rejected", "FolderPath \"/Game/X/UI_T777\" is outside roots (/Game/Q)", '{"n":3}', "10:00:03"),
        # one looping call repeated: same args and same time -> not a candidate
        row("loop", "rejected", "boom 42", '{"x":1}', "10:01:00"),
        row("loop", "rejected", "boom 42", '{"x":1}', "10:01:00"),
        # single occurrence -> below --min
        row("once", "rejected", "only once", '{"o":1}', "10:02:00"),
        # guardian noise
        row("w", "refused", "refused even in the laboratory, path outside /root_ai_lab: /Game/A", '{"p":1}', "10:03:00"),
        row("w", "refused", "refused even in the laboratory, path outside /root_ai_lab: /Game/B", '{"p":2}', "10:03:01"),
        # covered by docs
        row("known", "rejected", "Collection not found: 'Cover_157' (Local)", '{"c":1}', "10:04:00"),
        row("known", "rejected", "Collection not found: 'Cover_158' (Local)", '{"c":2}', "10:04:01"),
        # no_answer, message falls back to r
        {"t": "10:05:00", "toolset": "TS.Tools", "tool": "slow", "args": "{\"s\":1}", "r": "no_answer"},
        {"t": "10:05:01", "toolset": "TS.Tools", "tool": "slow", "args": "{\"s\":2}", "r": "no_answer"},
    ]
    with tempfile.TemporaryDirectory() as tmp:
        led = os.path.join(tmp, "ledger.jsonl")
        with open(led, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
            f.write("this line is not json\n\n")
            f.write(json.dumps({"action": "recover", "result": "refused", "tool": "uefn_session"}) + "\n")
        docs = os.path.join(tmp, "docs")
        os.makedirs(docs)
        with open(os.path.join(docs, "t.md"), "w", encoding="utf-8") as f:
            f.write("Known trap: Collection not found: 'Cover_9' (Local)\n")
        known = os.path.join(tmp, "known.json")
        with open(known, "w", encoding="utf-8") as f:
            json.dump({"tools": ["make"]}, f)
        out_j = os.path.join(tmp, "o.json")
        out_m = os.path.join(tmp, "o.md")
        rc = ml.main(["--ledger", led, "--known", known, "--docs", docs, "--json", out_j, "--md", out_m])
        check("exit code 0", rc == 0)
        items = json.load(open(out_j, encoding="utf-8"))
        keys = [i["key"] for i in items]
        check("3 candidates (make, known, slow)", len(items) == 3)
        make = [i for i in items if i["key"].startswith("TS.Tools/make")]
        check("guid/asset variants merged into one signature", len(make) == 1 and make[0]["count"] == 3)
        check("no guid or Game path left in signature", make and g1 not in make[0]["signature"] and "/Game" not in make[0]["signature"])
        check("asset name normalized", [i["signature"] for i in items if "/known" in i["key"]] == ["Collection not found: 'Cover_N' (Local)"])
        check("single repeated call is not a candidate", not any("/loop" in k for k in keys))
        check("below --min is dropped", not any("/once" in k for k in keys))
        check("guardian refusals are skipped", not any("/w " in k or "/w|" in k or k.startswith("TS.Tools/w ") for k in keys))
        check("covered detected", [i["covered"] for i in items if "/known" in i["key"]] == [True])
        check("uncovered first", [i["covered"] for i in items] == sorted(i["covered"] for i in items))
        check("sorted by count among uncovered", items[0]["key"].startswith("TS.Tools/make"))
        check("no_answer uses r as message", any(i["signature"] == "no_answer" for i in items))
        check("area from known list", make and make[0]["area"] == "Tools")
        check("area other when unknown", [i["area"] for i in items if "/slow" in i["key"]] == ["other"])
        check("example_args max 160", all(len(i["example_args"]) <= 160 for i in items))
        check("fields present", all({"key", "area", "count", "r", "signature", "first_seen", "last_seen", "example_args", "covered"} <= set(i) for i in items))
        md = open(out_m, encoding="utf-8").read()
        check("md totals line", "3 candidates, 1 already covered" in md)
        check("md max 40 lines", len(md.splitlines()) <= 40)
        check("signature max 120", all(len(i["signature"]) <= 120 for i in items))
        check("normalize guid path", ml.normalize("x /%s/a/b y" % g1) == "x <path> y")
        check("normalize spaces", ml.normalize("a   b\n c") == "a b c")
        check("missing ledger is silent", ml.main(["--ledger", os.path.join(tmp, "nope.jsonl")]) == 0)
        led = os.path.join(tmp, "bat.jsonl")
        rows = []
        for i in range(3):
            rows.append({"t": "10:0%d:00" % i, "toolset": "A.B", "tool": "Make", "args": '{"p":"x%d"}' % i, "r": "rejected", "why": "bad path"})
            rows.append({"t": "10:0%d:30" % i, "toolset": "A.B", "tool": "Probe", "args": '{"p":"/G/Cover/Cover_%d"}' % i, "r": "rejected", "why": "invented"})
            rows.append({"t": "10:0%d:40" % i, "toolset": "A.B", "tool": "Tagged", "args": '{"p":"y%d"}' % i, "r": "rejected", "why": "probe", "src": "battery"})
        open(led, "w").write("\n".join(json.dumps(r) for r in rows))
        kn = os.path.join(tmp, "known.json")
        json.dump({"tools": {"A.B/Make": {"s": "ok", "a": "materials"}}}, open(kn, "w"))
        got = ml.collect(led, *ml.load_known(kn), 2)
        check("battery rows are not lessons (tagged and old /Cover rows)", [g["key"].split(" | ")[0] for g in got] == ["A.B/Make"])
        check("area comes from mcp-known-tools.json", got and got[0]["area"] == "materials")
        ml.INCLUDE_BATTERY = True
        check("--include-battery brings them back", len(ml.collect(led, *ml.load_known(kn), 2)) == 3)
        ml.INCLUDE_BATTERY = False
    if FAILS:
        print("%d FAIL" % len(FAILS))
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
