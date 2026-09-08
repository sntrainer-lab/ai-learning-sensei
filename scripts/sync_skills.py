#!/usr/bin/env python3
"""Mirror the canonical Codex skill into Claude Code's project skill path."""

from __future__ import annotations

import argparse
import filecmp
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".agents" / "skills" / "ai-learning-sensei"
TARGET = ROOT / ".claude" / "skills" / "ai-learning-sensei"


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
    if args.check:
        if trees_match(SOURCE, TARGET):
            print("Skill copies are synchronized.")
            return 0
        print("Skill copies differ. Run: python scripts/sync_skills.py")
        return 1
    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(SOURCE, TARGET, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print(f"Synchronized {SOURCE.relative_to(ROOT)} -> {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
