#!/usr/bin/env python3
"""
Tier Inventory Script
Lists every skill and every agent of the kit (name and kind) into a JSON file data/inventory.json.
"""
import json
import os
import sys
from pathlib import Path


def get_skill_name(skill_path: Path) -> str:
    """Extract skill name from path: user-level-skills/<name>/SKILL.md"""
    parts = skill_path.parts
    # Find user-level-skills in path
    for i, part in enumerate(parts):
        if part == "user-level-skills" and i + 1 < len(parts):
            return parts[i + 1]
    return skill_path.stem


def get_agent_name(agent_path: Path) -> str:
    """Extract agent name from filename"""
    return agent_path.stem


def main():
    repo_root = Path(__file__).parent.parent
    skills_dir = repo_root / "user-level-skills"
    agents_dir = repo_root / "user-level-agents"
    output_file = repo_root / "data" / "inventory.json"

    skills = []
    agents = []

    # Find all skills (SKILL.md files under user-level-skills)
    if skills_dir.exists():
        for skill_file in skills_dir.rglob("SKILL.md"):
            name = get_skill_name(skill_file)
            skills.append({
                "name": name,
                "kind": "skill",
                "path": str(skill_file.relative_to(repo_root))
            })

    # Find all agents (.md files under user-level-agents)
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            name = get_agent_name(agent_file)
            agents.append({
                "name": name,
                "kind": "agent",
                "path": str(agent_file.relative_to(repo_root))
            })

    # Sort by name for consistent output
    skills.sort(key=lambda x: x["name"])
    agents.sort(key=lambda x: x["name"])

    inventory = {
        "skills": skills,
        "agents": agents,
        "total_skills": len(skills),
        "total_agents": len(agents)
    }

    # Write JSON output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)

    print(f"Skills found: {len(skills)}")
    print(f"Agents found: {len(agents)}")
    print(f"Output written to: {output_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())