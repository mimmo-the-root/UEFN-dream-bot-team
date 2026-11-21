#!/usr/bin/env python3
"""Golden set nightly runner: run the 20 golden packages on free models through the router.

Usage:
  python3 tools/golden_nightly.py --model NAME[=COMMAND] [--model ...] [--url URL]
                                  --out RESULTS.json [--previous PREVIOUS.json] [--timeout SEC]

The router URL defaults to http://127.0.0.1:8787/v1/messages. A NAME without =COMMAND uses
the built-in Anthropic-compatible HTTP call for that free model. A COMMAND receives the prompt
on stdin and prints the answer on stdout; {url} and {model} are expanded in it and
GOLDEN_ROUTER_URL / GOLDEN_MODEL are set in its environment. When --previous is omitted the
previous run is read from --out, before it is overwritten. A model dropping more than
2 packages versus the previous run is flagged in the JSON and printed as DEGRADED.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import golden_set  # noqa: E402

DEFAULT_URL = "http://127.0.0.1:8787/v1/messages"
MAX_DROP = 2
PAID_PREFIXES = ("anthropic", "claude", "claude-plan", "openai")


def answer_from_response(body):
    """Extract the reply text from a /v1/messages response (or a plain completion)."""
    if not isinstance(body, dict):
        return ""
    content = body.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(str(b.get("text", "")) for b in content
                       if isinstance(b, dict) and b.get("type") == "text")
    if isinstance(body.get("completion"), str):
        return body["completion"]
    return ""


def router_call(url, name, timeout=120):
    """Build callable(prompt)->str that asks the router for one answer over HTTP."""
    def fn(prompt):
        payload = json.dumps({"model": name, "max_tokens": 512,
                              "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
        req = urllib.request.Request(url, data=payload,
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return answer_from_response(json.loads(r.read().decode("utf-8", "replace")))
    return fn


def command_call(cmd, env, timeout=120):
    """Build callable(prompt)->str from a per-model shell command with a dedicated env."""
    def fn(prompt):
        r = subprocess.run(cmd, shell=True, input=prompt, capture_output=True, text=True,
                           timeout=timeout, encoding="utf-8", errors="replace", env=env)
        if r.returncode != 0:
            raise RuntimeError("exit %d" % r.returncode)
        return r.stdout
    return fn


def parse_models(items, url, timeout):
    """Build {name: callable} from --model items, rejecting paid prefixes."""
    models, errors = {}, []
    for item in items:
        name, sep, cmd = item.partition("=")
        name = name.strip()
        if not name or (sep and not cmd.strip()):
            errors.append("bad --model %r, expected NAME[=COMMAND]" % item)
            continue
        if name.split("/")[0].lower() in PAID_PREFIXES:
            errors.append("paid model rejected: %s (free models only)" % name)
            continue
        if sep:
            env = dict(os.environ, GOLDEN_ROUTER_URL=url, GOLDEN_MODEL=name)
            expanded = cmd.replace("{url}", url).replace("{model}", name)
            models[name] = command_call(expanded, env, timeout)
        else:
            models[name] = router_call(url, name, timeout)
    return models, errors


def load_previous(path):
    """Read the models section of an earlier result file, tolerating missing/broken files."""
    if not path:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    models = data.get("models") if isinstance(data, dict) else None
    return models if isinstance(models, dict) else {}


def compare(current, previous):
    """Flag models whose passed count fell by more than MAX_DROP packages."""
    deltas, degradation = {}, []
    for name, res in current.items():
        old = previous.get(name)
        passed = res.get("passed") if isinstance(res, dict) else None
        if not isinstance(old, dict) or not isinstance(old.get("passed"), int) or not isinstance(passed, int):
            continue
        delta = old["passed"] - passed
        deltas[name] = delta
        if delta > MAX_DROP:
            degradation.append({"model": name, "previous": old["passed"],
                                "current": passed, "drop": delta})
    return {"deltas": deltas, "degradation": degradation,
            "degraded_models": [a["model"] for a in degradation]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--url", default=DEFAULT_URL, help="router /v1/messages URL")
    ap.add_argument("--model", action="append", default=[], help="free NAME[=COMMAND]")
    ap.add_argument("--out", required=True, help="write result JSON to this path")
    ap.add_argument("--previous", help="previous result JSON (default: --out before overwrite)")
    ap.add_argument("--timeout", type=int, default=120, help="seconds per package")
    a = ap.parse_args(argv)
    if not a.model:
        ap.error("at least one --model NAME[=COMMAND] is required")
    models, errors = parse_models(a.model, a.url, a.timeout)
    if errors:
        ap.error("; ".join(errors))
    previous_path = a.previous or (a.out if os.path.exists(a.out) else None)
    previous = load_previous(previous_path)
    res = golden_set.run_golden(models)
    res["generated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    res["url"] = a.url
    res["previous"] = previous_path or ""
    res["comparison"] = compare(res["models"], previous)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=1)
        f.write("\n")
    for name, r in res["models"].items():
        print("%s: %d/%d" % (name, r["passed"], r["total"]))
    for alert in res["comparison"]["degradation"]:
        print("DEGRADED %s: %d -> %d (drop %d)" % (alert["model"], alert["previous"],
                                                    alert["current"], alert["drop"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
