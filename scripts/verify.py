#!/usr/bin/env python3
"""Guard test suite for agentic-work-infra.

Checks:
1. Every directory under `skills/` has a `SKILL.md` with valid YAML frontmatter,
   non-empty `name` matching the directory name, non-empty `description` (supporting
   folded `>` / literal `|` scalars), and no duplicate keys.
2. Every tracked non-template `.md` file has valid inline and reference-style
   relative Markdown links (handling backtick/tilde fences, link titles, and
   heading `#anchor` fragments).
3. Template files (`*.template.md`) exist only under `skills/*/assets/`, and none
   are named `AGENTS.md` (which could be accidentally auto-loaded by agent hosts).
4. Tracked files (`git ls-files -z`) contain no `.DS_Store`, `*_backup*`, or `*_old*`
   artifacts, and untracked unignored files (`--others --exclude-standard`) are clean.
"""

from __future__ import annotations

import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$")
INLINE_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
REF_DEF_RE = re.compile(r"^ {0,3}\[([^\]]+)\]:\s*(\S+)")


def strip_fenced_blocks(text: str) -> str:
    out: list[str] = []
    fence_char = ""
    fence_len = 0
    for line in text.splitlines():
        m = FENCE_OPEN_RE.match(line)
        if m:
            marker = m.group(1)
            if not fence_char:
                fence_char = marker[0]
                fence_len = len(marker)
                continue
            if marker[0] == fence_char and len(marker) >= fence_len and line.strip() == marker:
                fence_char = ""
                fence_len = 0
                continue
        if not fence_char:
            out.append(line)
    return "\n".join(out)


def github_slug(heading: str) -> str:
    # Strip inline markdown formatting
    cleaned = re.sub(r"[`*_~]", "", heading)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", cleaned)
    cleaned = cleaned.strip().lower()
    out: list[str] = []
    for ch in cleaned:
        if ch in (" ", "\t"):
            out.append("-")
        elif ch == "-":
            out.append("-")
        else:
            cat = unicodedata.category(ch)
            if cat.startswith(("L", "N")) or ch == "_":
                out.append(ch)
    return "".join(out)


def collect_headings(md_path: Path, cache: dict[Path, set[str]]) -> set[str]:
    if md_path in cache:
        return cache[md_path]
    slugs: set[str] = set()
    counts: dict[str, int] = {}
    body = strip_fenced_blocks(md_path.read_text(encoding="utf-8"))
    for line in body.splitlines():
        m = HEADING_RE.match(line)
        if not m:
            continue
        base = github_slug(m.group(1))
        if not base:
            continue
        idx = counts.get(base, 0)
        counts[base] = idx + 1
        slugs.add(base if idx == 0 else f"{base}-{idx}")
    cache[md_path] = slugs
    return slugs


def parse_simple_frontmatter(fm_text: str, rel: Path, errors: list[str]) -> dict[str, str]:
    lines = fm_text.splitlines()
    data: dict[str, str] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not m:
            errors.append(f"{rel}: invalid YAML frontmatter line '{line}'")
            i += 1
            continue
        key, rest = m.group(1), m.group(2).strip()
        if key in data:
            errors.append(f"{rel}: duplicate YAML frontmatter key '{key}'")
        # Strip inline comment unless quoted
        if rest and not rest.startswith(("'", '"')) and " #" in rest:
            rest = rest.split(" #", 1)[0].strip()
        if rest.startswith("#"):
            rest = ""
        if rest in (">", "|", ">-", "|-"):
            block_lines: list[str] = []
            i += 1
            while i < len(lines):
                bline = lines[i]
                if not bline.strip():
                    block_lines.append("")
                    i += 1
                    continue
                if bline.startswith((" ", "\t")):
                    block_lines.append(bline.strip())
                    i += 1
                else:
                    break
            data[key] = " ".join(x for x in block_lines if x).strip()
            continue
        if (rest.startswith('"') and not rest.endswith('"')) or (
            rest.startswith("'") and not rest.endswith("'")
        ) or (rest.startswith("[") and not rest.endswith("]")):
            errors.append(f"{rel}: unterminated YAML value for '{key}'")
            data[key] = ""
            i += 1
            continue
        if (rest.startswith('"') and rest.endswith('"')) or (
            rest.startswith("'") and rest.endswith("'")
        ):
            rest = rest[1:-1].strip()
        data[key] = rest
        i += 1
    return data


def check_skills_frontmatter(errors: list[str]) -> int:
    skills_dir = ROOT / "skills"
    checked = 0
    for subdir in sorted(p for p in skills_dir.iterdir() if p.is_dir() and not p.name.startswith(".")):
        skill_md = subdir / "SKILL.md"
        if not skill_md.is_file():
            errors.append(f"skills/{subdir.name}: missing required SKILL.md")
            continue
        checked += 1
        rel = skill_md.relative_to(ROOT)
        content = skill_md.read_text(encoding="utf-8")
        if not content.startswith("---\n"):
            errors.append(f"{rel}: missing opening YAML frontmatter '---'")
            continue
        parts = content[4:].split("\n---\n", 1)
        if len(parts) < 2:
            errors.append(f"{rel}: missing closing YAML frontmatter '---'")
            continue
        data = parse_simple_frontmatter(parts[0], rel, errors)
        name_val = data.get("name", "")
        desc_val = data.get("description", "")
        if not name_val:
            errors.append(f"{rel}: frontmatter 'name' must be non-empty")
        elif name_val != subdir.name:
            errors.append(f"{rel}: frontmatter name '{name_val}' does not match directory '{subdir.name}'")
        if not desc_val:
            errors.append(f"{rel}: frontmatter 'description' must be non-empty")
    return checked


def clean_link_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")].strip()
    # Strip optional title: path "title" or path 'title'
    m = re.match(r'^(\S+)\s+(?:"[^"]*"|\'[^\']*\')\s*$', target)
    if m:
        return m.group(1)
    return target


def validate_target(md_file: Path, rel: Path, raw_target: str, heading_cache: dict[Path, set[str]], errors: list[str]) -> None:
    target = clean_link_target(raw_target)
    if (
        not target
        or target.startswith(("http://", "https://", "mailto:"))
        or "<" in target
        or ">" in target
    ):
        return
    if target.startswith("#"):
        frag = target[1:].strip().lower()
        if frag and frag not in collect_headings(md_file, heading_cache):
            errors.append(f"{rel}: broken heading anchor '{target}'")
        return
    path_part, sep, frag = target.partition("#")
    resolved = (md_file.parent / path_part).resolve()
    if not resolved.exists():
        errors.append(f"{rel}: broken relative link '{raw_target}'")
        return
    if sep and frag and resolved.is_file() and resolved.suffix.lower() == ".md":
        if frag.lower() not in collect_headings(resolved, heading_cache):
            errors.append(f"{rel}: broken target anchor '{raw_target}'")


def git_tracked_files() -> list[Path]:
    res = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        capture_output=True,
        check=True,
    )
    return [ROOT / p.decode("utf-8") for p in res.stdout.split(b"\x00") if p]


def check_markdown_and_templates(tracked: list[Path], errors: list[str]) -> int:
    checked = 0
    heading_cache: dict[Path, set[str]] = {}
    for md_file in tracked:
        if not md_file.is_file() or md_file.suffix.lower() != ".md":
            continue
        rel = md_file.relative_to(ROOT)
        if md_file.name.endswith(".template.md"):
            if len(rel.parts) < 4 or rel.parts[0] != "skills" or rel.parts[2] != "assets":
                errors.append(f"{rel}: template file must reside under skills/<skill>/assets/")
            continue
        if len(rel.parts) >= 3 and rel.parts[0] == "skills" and rel.parts[2] == "assets" and md_file.name == "AGENTS.md":
            errors.append(f"{rel}: forbidden filename AGENTS.md inside skill assets (use agents.template.md)")
        checked += 1
        body = strip_fenced_blocks(md_file.read_text(encoding="utf-8"))
        body_no_code = re.sub(r"`[^`]*`", "", body)
        for m in INLINE_LINK_RE.finditer(body_no_code):
            validate_target(md_file, rel, m.group(1), heading_cache, errors)
        for line in body_no_code.splitlines():
            rm = REF_DEF_RE.match(line)
            if rm:
                validate_target(md_file, rel, rm.group(2), heading_cache, errors)
    return checked


def check_hygiene(tracked: list[Path], errors: list[str]) -> None:
    for path in tracked:
        rel = path.relative_to(ROOT)
        if path.name == ".DS_Store" or "_backup" in path.name or "_old" in path.name:
            errors.append(f"{rel}: forbidden hygiene artifact tracked by git")
    untracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "--others", "--exclude-standard", "-z"],
        capture_output=True,
        check=True,
    )
    for raw in untracked.stdout.split(b"\x00"):
        if not raw:
            continue
        rel_str = raw.decode("utf-8")
        name = Path(rel_str).name
        if name == ".DS_Store" or "_backup" in name or "_old" in name:
            errors.append(f"{rel_str}: forbidden untracked hygiene artifact in working tree")


def main() -> int:
    errors: list[str] = []
    tracked = git_tracked_files()
    skill_count = check_skills_frontmatter(errors)
    md_count = check_markdown_and_templates(tracked, errors)
    check_hygiene(tracked, errors)

    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1

    print(f"OK: {skill_count} skills and {md_count} tracked markdown files passed guard checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
