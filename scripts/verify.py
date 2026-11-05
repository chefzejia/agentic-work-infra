#!/usr/bin/env python3
"""Guard test suite for agentic-work-infra.

Checks:
1. Every skills/*/SKILL.md has valid YAML frontmatter with non-empty `name` and `description`.
2. Every relative Markdown link in tracked non-template .md files resolves to an existing path.
3. No `.DS_Store` or backup (`*_backup*`, `*_old*`) files are tracked by Git.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
FENCE_RE = re.compile(r"^```")


def strip_fenced_blocks(text: str) -> str:
    out = []
    in_fence = False
    for line in text.splitlines():
        if FENCE_RE.match(line.strip()):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def check_skills_frontmatter(errors: list[str]) -> int:
    skills_dir = ROOT / "skills"
    checked = 0
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        checked += 1
        content = skill_md.read_text(encoding="utf-8")
        if not content.startswith("---\n"):
            errors.append(f"{skill_md.relative_to(ROOT)}: missing opening YAML frontmatter '---'")
            continue
        parts = content.split("\n---\n", 1)
        if len(parts) < 2:
            errors.append(f"{skill_md.relative_to(ROOT)}: missing closing YAML frontmatter '---'")
            continue
        fm = parts[0]
        name_match = re.search(r"^name:\s*(\S+)\s*$", fm, re.MULTILINE)
        desc_match = re.search(r"^description:\s*(.+)$", fm, re.MULTILINE)
        if not name_match:
            errors.append(f"{skill_md.relative_to(ROOT)}: frontmatter missing 'name'")
        elif name_match.group(1) != skill_md.parent.name:
            errors.append(
                f"{skill_md.relative_to(ROOT)}: frontmatter name '{name_match.group(1)}' "
                f"does not match directory '{skill_md.parent.name}'"
            )
        if not desc_match:
            errors.append(f"{skill_md.relative_to(ROOT)}: frontmatter missing 'description'")
    return checked


def check_markdown_links(errors: list[str]) -> int:
    checked = 0
    for md_file in sorted(ROOT.rglob("*.md")):
        rel = md_file.relative_to(ROOT)
        if rel.parts[0] in ("thirdparty", ".git") or md_file.name.endswith(".template.md"):
            continue
        checked += 1
        body = strip_fenced_blocks(md_file.read_text(encoding="utf-8"))
        # Remove inline code spans so example links inside backticks are ignored
        body_no_code = re.sub(r"`[^`]*`", "", body)
        for match in LINK_RE.finditer(body_no_code):
            raw_target = match.group(1).strip()
            if raw_target.startswith("<") and raw_target.endswith(">"):
                raw_target = raw_target[1:-1].strip()
            if (
                not raw_target
                or raw_target.startswith(("#", "http://", "https://", "mailto:"))
                or "<" in raw_target
            ):
                continue
            target_path = raw_target.split("#", 1)[0]
            if not target_path:
                continue
            resolved = (md_file.parent / target_path).resolve()
            if not resolved.exists():
                errors.append(f"{rel}: broken relative link '{raw_target}'")
    return checked


def check_tracked_hygiene(errors: list[str]) -> None:
    res = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    )
    for line in res.stdout.splitlines():
        path = Path(line)
        if path.name == ".DS_Store" or "_backup" in path.name or "_old" in path.name:
            errors.append(f"{line}: forbidden hygiene artifact tracked by git")


def main() -> int:
    errors: list[str] = []
    skill_count = check_skills_frontmatter(errors)
    md_count = check_markdown_links(errors)
    check_tracked_hygiene(errors)

    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1

    print(f"OK: {skill_count} skills and {md_count} markdown files passed guard checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
