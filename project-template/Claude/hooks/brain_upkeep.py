#!/usr/bin/env python3
"""brain_upkeep.py - second brain upkeep automation (free checks daily, real pass weekly via /pieces).

This is the automation brain for the second brain vault:

1. Free checks (no tokens), at most once per day, from the session-start hook:
   - vault_check links / dups / stats / status
   - Count of Clippings/ files not yet compiled (Clippings counts as raw material)
   - Result in <vault>/output/upkeep/YYYY-MM-DD.md
   - One line in the session context only when something needs work ("vault: 163 to compile, 4 broken links")

2. Real pass (tokens): due when the last one is older than 7 days OR a release just closed
   (learn_gate.py closed releases), and only when the vault path is set.
   - Runs as /pieces with --mode free (never the plan)
   - One piece per batch of about 10 files to compile
   - Then audit (broken links, stale pages over 30 days, contradictions)
   - Then hot.md and the indexes
   - State in <vault>/output/upkeep/state.json (last run, files done) so an interrupted pass continues
   - Log one line per pass in wiki/log.md ("upkeep | compile N, fixed M links")

3. The mailbox worker starts the due pass by itself when the inbox is empty
   (one command written by brain_upkeep.py into Claude/relay/inbox/ with parallel: yes)
   - A session never runs it in the foreground

4. daily-vault-compile.ps1: write a log line to <vault>/output/upkeep/scheduler.log each run,
   and document in second-brain-template/README.md how to register it with schtasks
   (or say it is no longer needed with point 3)
"""

import json
import os
import re
import sys
import subprocess
import datetime
from pathlib import Path


def get_vault_path():
    """Get the vault path from environment or ~/.claude/CLAUDE.md"""
    if os.environ.get("SECOND_BRAIN"):
        return os.path.abspath(os.environ["SECOND_BRAIN"])

    home = os.environ.get("UEFN_HOME") or os.path.join(os.path.expanduser("~"), ".claude")
    claude_md = os.path.join(home, "CLAUDE.md")

    if not os.path.isfile(claude_md):
        return None

    m = re.search(r"\*\*Second brain path\*\*:\s*`([^`]*)`", open(claude_md, encoding="utf-8").read())
    if not m or m.group(1) == "<SECOND_BRAIN_PATH>":
        return None

    vault = m.group(1)
    if not os.path.isdir(vault):
        return None

    return os.path.abspath(vault)


def get_check_script():
    """Get the path to vault_check.py"""
    home = os.environ.get("UEFN_HOME") or os.path.join(os.path.expanduser("~"), ".claude")
    return os.path.join(home, "skills", "second-brain-query", "scripts", "vault_check.py")


def run_vault_check(vault, *args):
    """Run vault_check.py with the given arguments"""
    check_script = get_check_script()
    if not os.path.isfile(check_script):
        return 1, "vault_check.py not found"

    try:
        result = subprocess.run(
            [sys.executable, check_script, *args, "--vault", vault],
            capture_output=True,
            text=True,
            timeout=60,
            errors="replace"
        )
        return result.returncode, (result.stdout or "").strip()
    except subprocess.TimeoutExpired:
        return 1, "timeout"
    except Exception as e:
        return 1, str(e)


def count_clippings(vault):
    """Count files in Clippings/ that are not yet compiled"""
    clippings_dir = os.path.join(vault, "Clippings")
    if not os.path.isdir(clippings_dir):
        return 0

    count = 0
    for root, dirs, files in os.walk(clippings_dir):
        for f in files:
            if f.endswith(".md") and not f.endswith("_COMPILED.md"):
                count += 1
    return count


def free_checks(vault):
    """Run daily free checks (no tokens)"""
    today = datetime.date.today().isoformat()
    output_dir = os.path.join(vault, "output", "upkeep")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{today}.md")

    results = []

    # Run links check - vault_check.py always returns 0, check output for "broken link"
    rc, out = run_vault_check(vault, "links")
    if "broken link" in out.lower():
        results.append(("links", out))

    # Run dups check - vault_check.py always returns 0, check output for "duplicate"
    rc, out = run_vault_check(vault, "dups")
    if "duplicate" in out.lower():
        results.append(("dups", out))

    # Run stats
    rc, out = run_vault_check(vault, "stats")
    if rc != 0:
        results.append(("stats", out))

    # Run status
    rc, out = run_vault_check(vault, "status")
    if rc != 0:
        results.append(("status", out))

    # Count Clippings
    clippings_count = count_clippings(vault)

    # Write output file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# Upkeep Free Check - {today}\n\n")
        if results:
            for cmd, out in results:
                f.write(f"## {cmd}\n```\n{out}\n```\n\n")
        else:
            f.write("All free checks passed.\n\n")
        f.write(f"Clippings to compile: {clippings_count}\n")

    # Determine if work is needed
    needs_work = bool(results) or clippings_count > 0

    if needs_work:
        msg_parts = []
        if clippings_count > 0:
            msg_parts.append(f"{clippings_count} to compile")
        if results:
            for cmd, out in results:
                if "broken" in out.lower():
                    msg_parts.append(f"{cmd}: issues")
                elif "duplicate" in out.lower():
                    msg_parts.append(f"{cmd}: duplicates")
                else:
                    msg_parts.append(f"{cmd}: warnings")
        return f"vault: {', '.join(msg_parts)}"

    return None


def is_real_pass_due(vault):
    """Check if the real pass (with tokens) is due"""
    state_file = os.path.join(vault, "output", "upkeep", "state.json")

    # Check if 7 days have passed since last run
    if os.path.isfile(state_file):
        try:
            with open(state_file, encoding="utf-8") as f:
                state = json.load(f)
            last_run = state.get("last_run")
            if last_run:
                last_date = datetime.date.fromisoformat(last_run)
                if (datetime.date.today() - last_date).days < 7:
                    return False, "last run < 7 days ago"
        except Exception:
            pass

    # Check if a release was just closed (via learn_gate)
    # This is checked by looking at the learn_gate state
    learn_gate_state = os.path.join(vault, ".brain", "learn_gate_state.json")
    if os.path.isfile(learn_gate_state):
        try:
            with open(learn_gate_state, encoding="utf-8") as f:
                lg_state = json.load(f)
            if lg_state.get("just_closed_release"):
                return True, "release just closed"
        except Exception:
            pass

    # If no previous run, it's due
    if not os.path.isfile(state_file):
        return True, "never run"

    return True, "due"


def write_inbox_command(vault):
    """Write a command to the mailbox inbox to start the real pass"""
    # Find the project root (where Claude/relay/inbox is)
    # This assumes we're running from a project that has the kit installed
    project_root = os.environ.get("UEFN_HOME") or os.path.join(os.path.expanduser("~"), ".claude")
    # Go up to find the project that contains Content/Claude/relay
    # Actually, the relay is in the project's Content/Claude/relay
    # We need to find the project that has the current vault path set

    # For now, use the UEFN_HOME as the project root
    inbox_dir = os.path.join(project_root, "Claude", "relay", "inbox")
    if not os.path.isdir(inbox_dir):
        # Try to find it from the vault path
        # The vault is usually outside the project, so we look for a project that has this vault configured
        pass

    os.makedirs(inbox_dir, exist_ok=True)

    # Create a unique command file
    import uuid
    cmd_file = os.path.join(inbox_dir, f"brain-upkeep-{uuid.uuid4().hex[:8]}.json")

    command = {
        "command": "second_brain_upkeep",
        "mode": "free",
        "parallel": True,
        "vault": vault,
        "description": "Second brain real pass: compile, audit, update indexes"
    }

    with open(cmd_file, "w", encoding="utf-8") as f:
        json.dump(command, f, indent=2)

    return cmd_file


def update_state(vault, files_done=0, links_fixed=0):
    """Update the upkeep state file"""
    state_file = os.path.join(vault, "output", "upkeep", "state.json")
    os.makedirs(os.path.dirname(state_file), exist_ok=True)

    state = {}
    if os.path.isfile(state_file):
        try:
            with open(state_file, encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            pass

    state["last_run"] = datetime.date.today().isoformat()
    state["files_compiled"] = state.get("files_compiled", 0) + files_done
    state["links_fixed"] = state.get("links_fixed", 0) + links_fixed

    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def log_upkeep(vault, message):
    """Log a line to wiki/log.md"""
    log_file = os.path.join(vault, "wiki", "log.md")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    line = f"- {timestamp} | {message}\n"

    # Append to log
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line)


def maybe_start_real_pass(vault, project_root=None):
    """Check if real pass is due and if so, write inbox command"""
    due, reason = is_real_pass_due(vault)
    if not due:
        return False, reason

    # Check if inbox exists and is empty (mailbox worker will pick it up)
    if project_root is None:
        project_root = os.environ.get("UEFN_HOME") or os.path.join(os.path.expanduser("~"), ".claude")
    inbox_dir = os.path.join(project_root, "Claude", "relay", "inbox")

    # If inbox doesn't exist, relay system isn't set up - don't start
    if not os.path.isdir(inbox_dir):
        return False, "inbox missing"

    inbox_files = [f for f in os.listdir(inbox_dir) if f.endswith(".json")]
    if inbox_files:
        return False, "inbox not empty"

    # Write the command
    cmd_file = write_inbox_command(vault)
    return True, f"command written to {cmd_file}"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Second brain upkeep automation")
    parser.add_argument("mode", choices=["free", "real", "check-due", "maybe-start"], help="Mode to run in")
    parser.add_argument("--vault", help="Vault path (overrides auto-detection)")
    args = parser.parse_args()

    vault = args.vault or get_vault_path()
    if not vault:
        # Vault not configured - silent exit
        return 0

    if args.mode == "free":
        # Daily free checks (called from session start)
        msg = free_checks(vault)
        if msg:
            print(msg)
        return 0

    elif args.mode == "check-due":
        due, reason = is_real_pass_due(vault)
        print(f"due={due} reason={reason}")
        return 0

    elif args.mode == "maybe-start":
        # Allow test to inject project_root via UEFN_HOME
        project_root = os.environ.get("UEFN_HOME")
        started, reason = maybe_start_real_pass(vault, project_root)
        if started:
            print(f"started: {reason}")
        else:
            print(f"not started: {reason}")
        return 0

    elif args.mode == "real":
        # This is the actual real pass - run via /pieces
        # The piece orchestrator will call this with specific pieces
        print("Real pass should be run via /pieces with --mode free")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())