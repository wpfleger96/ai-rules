#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml"]
# ///
"""Skill Router Hook - Suggests skills based on prompt content."""

import json
import re
import sys

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Skill:
    name: str
    trigger_keywords: list[str] = field(default_factory=list)
    trigger_patterns: list[str] = field(default_factory=list)


def parse_skill(content: str) -> Skill | None:
    """Parse skill from SKILL.md frontmatter."""
    if not content.startswith("---"):
        return None

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None

    try:
        data = yaml.safe_load(parts[1])
        if not data or not data.get("name"):
            return None

        metadata = data.get("metadata", {})
        return Skill(
            name=data["name"],
            trigger_keywords=[
                kw.strip()
                for kw in metadata.get("trigger-keywords", "").split(",")
                if kw.strip()
            ],
            trigger_patterns=[
                p.strip()
                for p in metadata.get("trigger-patterns", "").split(",")
                if p.strip()
            ],
        )
    except yaml.YAMLError:
        return None


def match_skills(prompt: str, skills: list[Skill]) -> list[str]:
    """Match prompt against skill triggers."""
    matched = []
    prompt_lower = prompt.lower()

    for skill in skills:
        if any(kw.lower() in prompt_lower for kw in skill.trigger_keywords):
            matched.append(skill.name)
        elif any(
            re.search(p, prompt, re.IGNORECASE) for p in skill.trigger_patterns if p
        ):
            matched.append(skill.name)

    return matched


def main() -> None:
    try:
        prompt = json.loads(sys.stdin.read()).get("prompt", "")
        if not prompt:
            sys.exit(0)

        skills_dir = Path.home() / ".claude" / "skills"
        if not skills_dir.exists():
            sys.exit(0)

        skills = []
        for skill_md in skills_dir.glob("*/SKILL.md"):
            try:
                skill = parse_skill(skill_md.read_text())
                if skill:
                    skills.append(skill)
            except Exception:
                continue

        matched = match_skills(prompt, skills)
        if matched:
            print(f"[Skill Router] Suggested: {', '.join(matched)}")
            print("Use the Skill tool to invoke before responding.")

    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
