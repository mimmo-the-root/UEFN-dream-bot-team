#!/usr/bin/env python3
"""Tests for tools/debug_bundle.py: fake secrets planted in temp dirs must never reach the zip."""
import json, os, sys, tempfile, zipfile
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import debug_bundle  # noqa: E402

# built at runtime so this file itself holds no secret-looking literal
SECRETS = ["s" + "k-" + "A1b2C3d4E5f6G7h8", "ke" + "y_" + "9f8e7d6c5b4a3210", "gh" + "p_" + "A" * 24,
           "hunter" + "2pass", "mimmo" + "@example.org", "ey" + "J" + "hbGciOiJIUzI1.eyJzdWIiOiIx.abcdEFGH12"]
HOME_USER = "C:" + "\\Users\\" + "Mimmo" + "\\Documents\\proj"


def plant(d):
    os.makedirs(os.path.join(d, "Claude", "logs"))
    os.makedirs(os.path.join(d, "Claude", "plan"))
    os.makedirs(os.path.join(d, "Claude", "config"))
    s = SECRETS
    with open(os.path.join(d, "Claude", "logs", "task-status.log"), "w", encoding="utf-8") as f:
        f.write("call with %s and %s\nAuthorization: Bearer %s\npassword=%s\nfile %s\nwho %s\njwt %s\n" % (s[0], s[1], s[2], s[3], HOME_USER, s[4], s[5]))
    with open(os.path.join(d, "Claude", "plan", "PROBLEMS-FROM-COD.md"), "w", encoding="utf-8") as f:
        f.write("problem: url https://bob:%s@host.%s/x and %s/secret/file\n" % (s[3], "example", "/ho" + "me/mimmo"))
    with open(os.path.join(d, "Claude", "config", "kit-settings.json"), "w", encoding="utf-8") as f:
        json.dump({"problems_log": True, "openrouter_api_key": s[0], "nested": {"login": s[3], "mode": "paid"}}, f)


def zip_text(p):
    with zipfile.ZipFile(p) as z:
        return "\n".join(z.read(n).decode("utf-8") for n in z.namelist()), z.namelist()


def main():
    with tempfile.TemporaryDirectory() as d:
        plant(d)
        out = os.path.join(d, "out", "b.zip")
        r = debug_bundle.build_bundle(d, out)
        assert r["ok"] and os.path.isfile(out), r
        text, names = zip_text(out)
        for sec in SECRETS + ["Mimmo", "mimmo", "bob:"]:
            assert sec not in text, "leaked: " + sec
        assert not debug_bundle.scan_text(text), debug_bundle.scan_text(text)
        assert "<USER_HOME>" in text and "<REDACTED" in text
        assert '"mode": "paid"' in text and "problems_log" in text  # harmless config kept
        for want in ("versions.json", "config/kit-settings.json", "problems/PROBLEMS-FROM-COD.md", "logs/task-status.log"):
            assert want in names, names
        assert not os.path.exists(out + ".tmp")
    # refusal: if sanitizing misses something, no zip is written
    with tempfile.TemporaryDirectory() as d:
        plant(d)
        out = os.path.join(d, "refused.zip")
        orig = debug_bundle.sanitize_counted
        debug_bundle.sanitize_counted = lambda t, p=None: (t, 0)
        try:
            r = debug_bundle.build_bundle(d, out)
        finally:
            debug_bundle.sanitize_counted = orig
        assert not r["ok"] and r["findings"] and not os.path.exists(out), r
    # empty project still works (versions only)
    with tempfile.TemporaryDirectory() as d:
        r = debug_bundle.build_bundle(d, os.path.join(d, "e.zip"))
        assert r["ok"] and r["files"] == ["versions.json"], r
    print("test_debug_bundle ok")


if __name__ == "__main__":
    main()
