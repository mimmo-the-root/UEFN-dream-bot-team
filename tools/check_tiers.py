#!/usr/bin/env python3
"""
Check tiers coverage: every skill and agent from inventory.json must have a tier in tiers.json.
Usage: python tools/check_tiers.py
"""
import json
import sys
from pathlib import Path

def main():
    repo_root = Path(__file__).parent.parent
    inventory_path = repo_root / "data" / "inventory.json"
    tiers_path = repo_root / "data" / "tiers.json"

    if not inventory_path.exists():
        print(f"FAIL: inventory.json not found at {inventory_path}")
        return 1
    if not tiers_path.exists():
        print(f"FAIL: tiers.json not found at {tiers_path}")
        return 1

    with open(inventory_path) as f:
        inventory = json.load(f)
    with open(tiers_path) as f:
        tiers = json.load(f)

    skill_tiers = tiers["tiers"]["skills"]
    agent_tiers = tiers["tiers"]["agents"]

    # Collect unique skill names from inventory (genre appears multiple times with different paths)
    inventory_skills = {}
    for s in inventory["skills"]:
        name = s["name"]
        if name not in inventory_skills:
            inventory_skills[name] = []
        inventory_skills[name].append(s["path"])

    inventory_agents = {a["name"]: a["path"] for a in inventory["agents"]}

    errors = []
    warnings = []

    # Check skills
    for name, paths in inventory_skills.items():
        if name not in skill_tiers:
            errors.append(f"Skill '{name}' missing from tiers.json")
        else:
            tier = skill_tiers[name]
            if tier not in ("T1", "T2", "T3"):
                errors.append(f"Skill '{name}' has invalid tier '{tier}'")

    # Check agents
    for name in inventory_agents:
        if name not in agent_tiers:
            errors.append(f"Agent '{name}' missing from tiers.json")
        else:
            tier = agent_tiers[name]
            if tier not in ("T1", "T2", "T3"):
                errors.append(f"Agent '{name}' has invalid tier '{tier}'")

    # Check for extra entries in tiers.json not in inventory
    for name in skill_tiers:
        if name not in inventory_skills:
            warnings.append(f"Skill '{name}' in tiers.json but not in inventory.json")

    for name in agent_tiers:
        if name not in inventory_agents:
            warnings.append(f"Agent '{name}' in tiers.json but not in inventory.json")

    # Report
    skills_covered = sum(1 for n in inventory_skills if n in skill_tiers)
    agents_covered = sum(1 for n in inventory_agents if n in agent_tiers)
    total_inventory = len(inventory_skills) + len(inventory_agents)
    total_covered = skills_covered + agents_covered

    print(f"Skills in inventory (unique names): {len(inventory_skills)}")
    print(f"  - Covered in tiers.json: {skills_covered}")
    print(f"Agents in inventory: {len(inventory_agents)}")
    print(f"  - Covered in tiers.json: {agents_covered}")
    print(f"Total items: {total_inventory}")
    print(f"Total covered: {total_covered}")
    print(f"Coverage: {total_covered}/{total_inventory} = {100 * total_covered / total_inventory:.1f}%")

    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print("\nERRORS:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("\nPASS: 100% coverage, all tiers valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())