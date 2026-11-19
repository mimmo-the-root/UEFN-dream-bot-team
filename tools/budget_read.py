#!/usr/bin/env python3
"""Read budget and limit info from the relay outbox.

Claude/relay/outbox/LIMIT.json: limit hit and reset time (written by limit_resume.py).
Claude/relay/outbox/budget.json: weekly_used_pct written by the owner by hand.

Returns a small dict with the current usage status.
"""

import json
import os
from pathlib import Path


def read_limit(project_dir: str) -> dict:
    """Read LIMIT.json from relay/outbox.
    
    Returns:
        dict with keys: state, hit_at, resets_at, kind, session_id, transcript_path.
        Missing or broken file: returns empty dict.
    """
    limit_path = Path(project_dir) / "Claude" / "relay" / "outbox" / "LIMIT.json"
    try:
        with open(limit_path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "state" in data:
            return data
    except (OSError, ValueError, json.JSONDecodeError):
        pass
    return {}


def read_budget(project_dir: str) -> dict:
    """Read budget.json from relay/outbox.
    
    budget.json is written by the owner by hand. Expected keys:
        - weekly_used_pct: float, 0.0 to 100.0, or None if not set.
    
    Returns:
        dict with weekly_used_pct if present, else empty dict.
    """
    budget_path = Path(project_dir) / "Claude" / "relay" / "outbox" / "budget.json"
    try:
        with open(budget_path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {"weekly_used_pct": data.get("weekly_used_pct")}
    except (OSError, ValueError, json.JSONDecodeError):
        pass
    return {}


def read_budget_and_limit(project_dir: str) -> dict:
    """Read both budget and limit info.
    
    Args:
        project_dir: Path to the project directory.
    
    Returns:
        dict with:
            - limit: result of read_limit()
            - budget: result of read_budget()
    """
    return {
        "limit": read_limit(project_dir),
        "budget": read_budget(project_dir),
    }


if __name__ == "__main__":
    import sys
    project_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    result = read_budget_and_limit(project_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
