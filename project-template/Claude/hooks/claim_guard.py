#!/usr/bin/env python3
"""claim_guard.py - Stop hook: catches claims of file writes without actual writes.
If the last assistant message says a file was written/created/updated/saved (EN and IT)
but the transcript of this turn has no successful Write/Edit/NotebookEdit/Bash that touched
a file, block once with reason:
"You said a file was written but no write succeeded in this turn: check and either write it or correct the message."
Never block twice in a row (stop_hook_active).
Switch off with UEFN_KIT_GUARDS=0. Never fails loudly."""
import json, os, re, sys
from pathlib import Path

WRITE_VERBS_EN = r'\b(wrote|written|created|updated|saved|committed)\b'
WRITE_VERBS_IT = r'\b(scritto|creato|aggiornato|salvato|commit)\b'
WRITE_VERBS = f'({WRITE_VERBS_EN}|{WRITE_VERBS_IT})'

FILE_PATTERN = r'[\w\-./\\]+\.\w+'

STATE_FILE = "Claude/logs/claim-guard-state.json"

def load_state(project_root: Path) -> dict:
    path = project_root / STATE_FILE
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_state(project_root: Path, data: dict):
    path = project_root / STATE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")

def get_session_id() -> str:
    return os.environ.get("CLAUDE_SESSION_ID", "default")

def has_write_claim(message: str) -> bool:
    """Check if message claims a file was written."""
    if not message:
        return False
    # Look for write verbs near file-like patterns
    pattern = rf'{WRITE_VERBS}.*{FILE_PATTERN}|{FILE_PATTERN}.*{WRITE_VERBS}'
    return bool(re.search(pattern, message, re.IGNORECASE))

def has_actual_write(transcript: list) -> bool:
    """Check if transcript has successful write operations."""
    write_tools = {"Write", "Edit", "NotebookEdit", "Bash"}
    for entry in transcript:
        tool = entry.get("tool", "")
        if tool not in write_tools:
            continue
        result = entry.get("result", {})
        # For Bash, check if it wrote a file (redirect, tee, etc.)
        if tool == "Bash":
            cmd = entry.get("tool_input", {}).get("command", "")
            if re.search(r'>\s*[\w\-./\\]+\.\w+|tee\s+[\w\-./\\]+\.\w+', cmd):
                if result.get("exit_code", 1) == 0:
                    return True
            continue
        # For Write/Edit/NotebookEdit, check success
        if result.get("success", False) or "error" not in result:
            return True
    return False

def main():
    try:
        if os.environ.get("UEFN_KIT_GUARDS") == "0":
            return 0

        # Use CLAUDE_PROJECT_DIR if set, otherwise find project root
        project_root = Path(os.environ.get("CLAUDE_PROJECT_DIR", ""))
        if not project_root.exists() or not (project_root / "Claude").exists():
            cwd = Path.cwd()
            project_root = cwd
            while project_root != project_root.parent:
                if (project_root / "Claude").exists():
                    break
                project_root = project_root.parent

        p = json.loads(sys.stdin.read() or "{}")

        # Get last assistant message
        transcript = p.get("transcript", [])
        last_assistant_msg = ""
        for entry in reversed(transcript):
            if entry.get("role") == "assistant":
                last_assistant_msg = entry.get("content", "")
                break

        if not has_write_claim(last_assistant_msg):
            # No claim, nothing to check
            state = load_state(project_root)
            session_id = get_session_id()
            state[session_id] = {"blocked_last": False}
            save_state(project_root, state)
            return 0

        # Check for actual writes in this turn's transcript
        actual_write = has_actual_write(transcript)

        if not actual_write:
            state = load_state(project_root)
            session_id = get_session_id()
            session_state = state.get(session_id, {})

            if session_state.get("blocked_last", False):
                # Already blocked once, don't block again
                session_state["blocked_last"] = False
                state[session_id] = session_state
                save_state(project_root, state)
                return 0

            # Block this time
            session_state["blocked_last"] = True
            state[session_id] = session_state
            save_state(project_root, state)

            msg = ("You said a file was written but no write succeeded in this turn: "
                   "check and either write it or correct the message.")
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "Stop",
                "permissionDecision": "deny",
                "permissionDecisionReason": msg
            }}))
        else:
            # Write succeeded, reset block flag
            state = load_state(project_root)
            session_id = get_session_id()
            state[session_id] = {"blocked_last": False}
            save_state(project_root, state)
    except Exception:
        pass
    return 0

if __name__ == "__main__":
    sys.exit(main())