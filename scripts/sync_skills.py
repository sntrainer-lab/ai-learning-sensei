#!/usr/bin/env python3
"""Mirror canonical Codex skills into Claude Code's project skill path."""

from __future__ import annotations

import argparse
import filecmp
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / ".agents" / "skills"
TARGET_ROOT = ROOT / ".claude" / "skills"


def trees_match(source: Path, target: Path) -> bool:
    if not target.is_dir():
        return False
    comparison = filecmp.dircmp(source, target, ignore=["__pycache__"])
    if comparison.left_only or comparison.right_only or comparison.diff_files or comparison.funny_files:
        return False
    return all(trees_match(source / name, target / name) for name in comparison.common_dirs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if the copies differ")
    args = parser.parse_args()
    sources = sorted(path for path in SOURCE_ROOT.iterdir() if path.is_dir())
    if not sources:
        print("No canonical skills found.")
        return 1
    if args.check:
        mismatched = [source.name for source in sources if not trees_match(source, TARGET_ROOT / source.name)]
        if not mismatched:
            print(f"{len(sources)} skill copies are synchronized.")
            return 0
        print(f"Skill copies differ: {', '.join(mismatched)}. Run: python scripts/sync_skills.py")
        return 1
    TARGET_ROOT.mkdir(parents=True, exist_ok=True)
    for source in sources:
        target = TARGET_ROOT / source.name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        print(f"Synchronized {source.relative_to(ROOT)} -> {target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
