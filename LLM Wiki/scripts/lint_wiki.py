#!/usr/bin/env python3

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
REQUIRED_FIELDS = ("title", "type", "summary", "updated")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def parse_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    data: dict[str, str] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def wiki_files() -> list[Path]:
    return sorted(WIKI.rglob("*.md"))


def resolve_markdown_link(source: Path, target: str) -> Path | None:
    if "://" in target or target.startswith("#"):
        return None
    clean = target.split("#", 1)[0]
    return (source.parent / clean).resolve()


def main() -> int:
    files = wiki_files()
    known = {path.resolve() for path in files}
    inbound: dict[Path, int] = {path.resolve(): 0 for path in files}
    issues: list[str] = []
    warnings: list[str] = []

    for path in files:
        meta = parse_frontmatter(path)
        missing = [field for field in REQUIRED_FIELDS if not meta.get(field)]
        if missing:
            issues.append(f"missing frontmatter in {path.relative_to(ROOT)}: {', '.join(missing)}")

        content = path.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(content):
            raw_target = match.group(1).strip()
            target = resolve_markdown_link(path, raw_target)
            if target is None:
                continue
            if target not in known and not target.exists():
                issues.append(
                    f"broken link in {path.relative_to(ROOT)} -> {raw_target}"
                )
                continue
            if target in inbound:
                inbound[target] += 1

    for path in files:
        if path.name in {"home.md", "index.md", "inbox.md", "log.md"}:
            continue
        if inbound[path.resolve()] == 0:
            warnings.append(f"orphan page: {path.relative_to(ROOT)}")

    if issues:
        print("ERRORS")
        for issue in issues:
            print(f"- {issue}")
    if warnings:
        print("WARNINGS")
        for warning in warnings:
            print(f"- {warning}")
    if not issues and not warnings:
        print("OK - wiki lint passed")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
