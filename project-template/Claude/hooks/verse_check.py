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

Usage: verse_check.py [--port 1962] [--host 127.0.0.1] [--timeout 120]
"""
import argparse, json, socket, sys, time

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

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=1962)
    ap.add_argument("--timeout", type=float, default=120.0)
    a = ap.parse_args(argv)
    res = check(a.host, a.port, a.timeout)
    sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
    return {"clean": 0, "errors": 1}.get(res["state"], 2)

if __name__ == "__main__":
    sys.exit(main())
