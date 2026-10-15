#!/usr/bin/env python3
"""Ask the running UEFN to build the Verse project and report the result.

Talks to the Verse Workflow Server that UEFN opens on 127.0.0.1:1962 (the same
channel the Epic VS Code extension uses for "Build Verse Code"). Read-only: it
sends one `compileProject` request and prints one JSON line.

Three states, never a guess:
  clean         exit 0   build finished with 0 errors
  errors        exit 1   build finished with errors (message holds the build log)
  not_analyzed  exit 2   UEFN not reachable, no answer in time, or an odd reply
Warnings do not change the state; they are counted.

Every build that ends in `errors` is also noted in Claude/logs/verse-errors.jsonl (time, error
signatures, a short excerpt; no paths, nothing sent anywhere). `--recurring` lists the signatures
seen in two or more different builds: those are the candidates for a lesson (the coder proposes it,
the owner approves; nothing is written to a skill by this script).

Usage: verse_check.py [--port 1962] [--host 127.0.0.1] [--timeout 120] [--no-log]
       verse_check.py --recurring
"""
import argparse, hashlib, json, os, re, socket, sys, time

def frame(obj):
    b = json.dumps(obj).encode("utf-8")
    return b"Content-Length: %d\r\n\r\n" % len(b) + b

def read_messages(sock, deadline):
    """Yield decoded JSON messages (Content-Length framing) until the deadline."""
    buf = b""
    while True:
        while True:
            i = buf.find(b"\r\n\r\n")
            if i < 0:
                break
            n = None
            for line in buf[:i].decode("utf-8", "replace").split("\r\n"):
                k, _, v = line.partition(":")
                if k.strip().lower() == "content-length":
                    n = int(v.strip())
            if n is None or len(buf) < i + 4 + n:
                break
            body, buf = buf[i + 4:i + 4 + n], buf[i + 4 + n:]
            try:
                yield json.loads(body.decode("utf-8"))
            except ValueError:
                continue
        left = deadline - time.time()
        if left <= 0:
            return
        sock.settimeout(left)
        try:
            d = sock.recv(65536)
        except socket.timeout:
            return
        if not d:
            return
        buf += d

def check(host="127.0.0.1", port=1962, timeout=120.0):
    try:
        sock = socket.create_connection((host, port), timeout=3)
    except OSError as e:
        return {"state": "not_analyzed", "reason": "UEFN not reachable on %s:%d (%s)" % (host, port, e.__class__.__name__)}
    with sock:
        sock.sendall(frame({"seq": 1, "type": 1, "command": "compileProject", "params": {}}))
        for m in read_messages(sock, time.time() + timeout):
            if m.get("type") == 2 and m.get("seq") == 1:
                if "error" in m:
                    return {"state": "not_analyzed", "reason": "build request refused: %s" % str(m["error"])[:300]}
                r = m.get("result")
                if not isinstance(r, dict) or not isinstance(r.get("numErrors"), int):
                    return {"state": "not_analyzed", "reason": "unexpected reply from UEFN"}
                return {"state": "errors" if r["numErrors"] else "clean", "errors": r["numErrors"],
                        "warnings": int(r.get("numWarnings") or 0), "message": str(r.get("message", ""))}
    return {"state": "not_analyzed", "reason": "no answer from UEFN within %ds" % int(timeout)}

CODE_RE = re.compile(r"\b(?:error|warning)\s+(\d{4})\b", re.I)

def signatures(message):
    """One signature per error line: the Verse error code when there is one, else a short hash of the
    line with paths, positions and numbers removed. Warning lines are skipped."""
    sigs = []
    for line in str(message).splitlines():
        if not re.search(r"\berror\b", line, re.I):
            continue
        m = CODE_RE.search(line)
        if m and "warning" not in m.group(0).lower():
            sigs.append("E" + m.group(1))
            continue
        flat = re.sub(r"[A-Za-z]:[\\/][^\s:]*|[\w./\\-]+\.verse|\(\d+(?:,\d+)?\)|\d+", "#", line.lower()).strip()
        sigs.append("H" + hashlib.sha1(flat.encode("utf-8")).hexdigest()[:8])
    return sorted(set(sigs))

def excerpt(message, n=400):
    t = re.sub(r"[A-Za-z]:[\\/][^\s:]*", "<path>", str(message))
    return t[:n]

def log_path():
    base = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return os.path.join(base, "Claude", "logs", "verse-errors.jsonl")

def record(res, path=None):
    """Append one line for a build with errors. Never raises: logging must not break the check."""
    try:
        path = path or log_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "errors": res["errors"],
               "sigs": signatures(res.get("message", "")), "excerpt": excerpt(res.get("message", ""))}
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass

def recurring(path=None, minimum=2):
    """Signatures present in at least `minimum` different logged builds, most frequent first."""
    path = path or log_path()
    count, last = {}, {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                for sg in set(row.get("sigs") or []):
                    count[sg] = count.get(sg, 0) + 1
                    last[sg] = row.get("excerpt", "")
    except OSError:
        return []
    return [{"sig": k, "builds": v, "example": last[k]} for k, v in sorted(count.items(), key=lambda x: -x[1]) if v >= minimum]

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=1962)
    ap.add_argument("--timeout", type=float, default=120.0)
    ap.add_argument("--no-log", action="store_true")
    ap.add_argument("--recurring", action="store_true")
    a = ap.parse_args(argv)
    if a.recurring:
        sys.stdout.write(json.dumps({"recurring": recurring()}, ensure_ascii=False) + "\n")
        return 0
    res = check(a.host, a.port, a.timeout)
    if res["state"] == "errors" and not a.no_log:
        record(res)
    sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
    return {"clean": 0, "errors": 1}.get(res["state"], 2)

if __name__ == "__main__":
    sys.exit(main())
