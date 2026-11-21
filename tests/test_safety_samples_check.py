#!/usr/bin/env python3
"""T-081/T-082/T-083: safety_samples_check against fake samples in temp dirs only."""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOL = os.path.join(ROOT, "tools", "safety_samples_check.py")


def run(path, home):
    return subprocess.run([sys.executable, TOOL, path], cwd=ROOT, capture_output=True,
                          text=True, timeout=30, env=dict(os.environ, DREAM_ROUTER_HOME=home))


def write(path, samples):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for item in samples:
            fh.write(json.dumps(item) + "\n")


def sample(action, paid=None, **extra):
    item = {"at": "2026-11-21 12:00:00", "chars": len(action), "mode": "safe", "tail": action}
    if paid is not None:
        item["verdict"] = paid
    item.update(extra)
    return item


def temp_file(samples, home):
    path = os.path.join(home, "samples.jsonl")
    write(path, samples)
    return path


def test_agreement():
    with tempfile.TemporaryDirectory() as home:
        path = temp_file([sample("Bash: git status", "allow"),
                          sample("Bash: git push origin main", "block"),
                          sample("Read: docs/a.md", "allow")], home)
        result = run(path, home)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "agreement 3/3" in result.stdout and "DISAGREE" not in result.stdout, result.stdout
        assert "PASS all 3 sample(s) agree" in result.stdout, result.stdout
        assert os.listdir(home) == ["samples.jsonl"], os.listdir(home)


def test_disagreements_are_all_listed():
    with tempfile.TemporaryDirectory() as home:
        path = temp_file([sample("Bash: git status", "block"),
                          sample("Bash: git push", "allow"),
                          sample("Bash: cat keys.env", "allow")], home)
        result = run(path, home)
        assert result.returncode == 1, result.stdout + result.stderr
        assert "line 1: DISAGREE local=allow paid=block" in result.stdout, result.stdout
        assert "line 2: DISAGREE local=block paid=allow" in result.stdout, result.stdout
        assert "DISAGREEMENT line 1: local allow vs paid block" in result.stdout, result.stdout
        assert "DISAGREEMENT line 2: local block vs paid allow" in result.stdout, result.stdout
        assert "agreement 0/3" in result.stdout, result.stdout


def test_secret_refuses_whole_file():
    fake = "sk-" + "ant-" + "a" * 30
    with tempfile.TemporaryDirectory() as home:
        path = temp_file([sample("Bash: git status", "allow"),
                          sample("Bash: echo " + fake, "allow")], home)
        result = run(path, home)
        assert result.returncode == 1, result.stdout + result.stderr
        assert "REFUSED line 2: secret pattern found" in result.stdout, result.stdout
        assert fake not in result.stdout and fake not in result.stderr, result.stdout


def test_secret_in_nested_field():
    fake = "Bearer " + "z" * 36
    with tempfile.TemporaryDirectory() as home:
        path = temp_file([{"tail": "Bash: git status", "verdict": "allow",
                           "messages": [{"role": "assistant", "content": fake}]}], home)
        result = run(path, home)
        assert result.returncode == 1 and "REFUSED line 1" in result.stdout, result.stdout
        assert fake not in result.stdout, result.stdout


def test_line_limit_and_bad_input():
    with tempfile.TemporaryDirectory() as home:
        path = temp_file([sample("Bash: git status", "allow")] * 6, home)
        result = run(path, home)
        assert result.returncode == 1 and "too many lines: 6 (at most 5)" in result.stdout, result.stdout
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("{not json\n")
        result = run(path, home)
        assert result.returncode == 1 and "line 1: invalid JSON" in result.stdout, result.stdout
        result = run(os.path.join(home, "missing.jsonl"), home)
        assert result.returncode == 1 and "missing file" in result.stdout, result.stdout


def test_transcript_tail_and_markup_verdict():
    with tempfile.TemporaryDirectory() as home:
        allow = {"at": "now", "chars": 40, "mode": "safe",
                 "tail": "User: go\nBash: git status\n<block>no</block>"}
        block = {"at": "now", "chars": 40, "mode": "safe",
                 "tail": "User: go\nBash: git push origin main\n<block>yes</block>"}
        path = temp_file([allow, block], home)
        result = run(path, home)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "line 1: OK local=allow paid=allow" in result.stdout, result.stdout
        assert "line 2: OK local=block paid=block" in result.stdout, result.stdout


def test_missing_paid_verdict():
    with tempfile.TemporaryDirectory() as home:
        path = temp_file([sample("Bash: git status")], home)
        result = run(path, home)
        assert result.returncode == 1, result.stdout + result.stderr
        assert "line 1: no paid verdict (allow/block) in sample" in result.stdout, result.stdout


def main():
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        print("ok", name)
    print("%d safety_samples_check tests passed" % len(tests))


if __name__ == "__main__":
    main()
