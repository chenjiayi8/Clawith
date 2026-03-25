#!/usr/bin/env python3
"""Scan agency-agents .md files and generate reference.json.

Usage:
    python -m app.scripts.build_role_reference [--dir /path/to/agency-agents]
"""
import argparse
import json
import re
import sys
from pathlib import Path


def slugify(name: str) -> str:
    """Convert 'Frontend Developer' -> 'frontend-developer'."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter fields from markdown content."""
    stripped = content.strip()
    if not stripped.startswith("---"):
        return {}
    end = stripped.find("---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in stripped[3:end].strip().split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip().lower()] = val.strip().strip('"').strip("'")
    return fm


def build_reference(agency_dir: Path) -> dict:
    """Scan agency_dir for .md files, return reference dict."""
    reference = {}
    collisions = []

    for md_file in sorted(agency_dir.rglob("*.md")):
        # Skip non-agent files
        if md_file.name in ("SKILL.md", "skill.md", "README.md", "CONTRIBUTING.md", "LICENSE.md"):
            continue
        # Skip hidden dirs, docs, examples, scripts folders
        rel = md_file.relative_to(agency_dir)
        parts = rel.parts
        if any(p.startswith(".") or p in ("docs", "examples", "scripts", ".github") for p in parts):
            continue

        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        fm = parse_frontmatter(content)
        name = fm.get("name")
        if not name:
            continue  # Skip files without a name in frontmatter

        slug = slugify(name)
        if slug in reference:
            collisions.append((slug, str(rel), reference[slug]["path"]))
            continue

        reference[slug] = {
            "name": name,
            "description": fm.get("description", "")[:300],
            "emoji": fm.get("emoji", ""),
            "path": str(rel),
        }

    if collisions:
        for slug, new_path, existing_path in collisions:
            print(f"WARNING: slug collision '{slug}': keeping '{existing_path}', skipping '{new_path}'", file=sys.stderr)

    return reference


def main():
    parser = argparse.ArgumentParser(description="Build reference.json from agency-agents .md files")
    parser.add_argument("--dir", type=str, help="Path to agency-agents directory")
    args = parser.parse_args()

    # Resolve directory
    if args.dir:
        agency_dir = Path(args.dir)
    else:
        try:
            from app.config import settings
            agency_dir = Path(settings.AGENCY_AGENTS_DIR)
        except ImportError:
            agency_dir = Path("/data/shared/agency-agents")

    if not agency_dir.exists():
        print(f"ERROR: Directory not found: {agency_dir}", file=sys.stderr)
        sys.exit(1)

    reference = build_reference(agency_dir)
    out_path = agency_dir / "reference.json"
    out_path.write_text(json.dumps(reference, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Generated {out_path} with {len(reference)} entries")


if __name__ == "__main__":
    main()
