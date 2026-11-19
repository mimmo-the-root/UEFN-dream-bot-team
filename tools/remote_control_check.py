#!/usr/bin/env python3
"""Reports whether a router mode keeps the plan login Remote Control needs.

Usage:
    python tools/remote_control_check.py <mode>            # free | paid | auto | safe | plan
    python tools/remote_control_check.py --env <json>      # session settings/env dict
    echo '{"mode":"free"}' | python tools/remote_control_check.py --env -

Prints ONE line: "OK keeps login" or "NO uses the placeholder token", with the fix.
"""
import json
import sys
from pathlib import Path

# Source: user-level-hooks/dream_router.py FREE_TOKEN and router_env/session_settings.
FREE_TOKEN = "dream-router-local"
MODES_WITH_LOGIN = frozenset({"auto", "safe", "paid", "plan"})


def check(mode):
    """Return (works, fix) for a mode name."""
    m = (mode or "").strip().lower()
    if m in MODES_WITH_LOGIN:
        return True, ""
    if m == "free":
        return False, "Fix: switch to auto, safe, or paid (keeps the plan login)."
    return False, "Fix: use a known mode (free, auto, safe, paid, plan); unknown mode is treated as free."


def check_env(env):
    """Check session settings or an environment dict for the placeholder token."""
    if not isinstance(env, dict):
        return False, "Fix: pass a settings dict (e.g. {\"mode\":\"auto\"})."

    # Explicit mode from session settings (session_settings() output).
    if "mode" in env:
        return check(env["mode"])

    # Env-style input: auth token or the derived session flags.
    token = env.get("ANTHROPIC_AUTH_TOKEN")
    if token is not None and str(token).strip() in (FREE_TOKEN, ""):
        return False, "Fix: remove ANTHROPIC_AUTH_TOKEN (placeholder) so the saved plan login is used."
    if env.get("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC") == "1":
        # Free mode sets this alongside the placeholder token.
        return False, "Fix: switch to auto, safe, or paid (keeps the plan login)."
    return True, ""


def main(argv):
    if len(argv) < 2:
        print("NO uses the placeholder token. Fix: pass a mode (free, auto, safe, paid, plan) or --env <json>.")
        return 2

    if argv[1] == "--env":
        if len(argv) < 3:
            print("NO uses the placeholder token. Fix: --env expects JSON text or '-' for stdin.")
            return 2
        try:
            raw = sys.stdin.read() if argv[2] == "-" else argv[2]
            env = json.loads(raw)
        except (ValueError, OSError):
            print("NO uses the placeholder token. Fix: --env expects valid JSON.")
            return 2
        works, fix = check_env(env)
    else:
        works, fix = check(argv[1])

    label = "OK keeps login" if works else "NO uses the placeholder token"
    print(label + (" " + fix if fix else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
