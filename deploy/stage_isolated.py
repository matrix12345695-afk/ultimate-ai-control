#!/usr/bin/env python3
"""Install ULTIMATE into a new, isolated destination. Never touches Inventory Bot.

Stage-only: does NOT start services, send Telegram messages, install dependencies,
read secrets, or replace an existing ULTIMATE installation.
"""
import argparse
import os
import shutil
import stat
import sys
from pathlib import Path

INVENTORY = Path("/home/maksim/inventory-bot").resolve()
DEFAULT_TARGET = Path("/home/maksim/ultimate-ai-control")
SKIP = {".git", ".github", ".env", "data", "__pycache__", ".venv", "logs", ".server-control"}
def isolated(path, inventory=INVENTORY):
    raw = Path(path).absolute()
    inv = Path(inventory).resolve()
    if raw.is_symlink():
        raise ValueError("Symlink destination forbidden")
    dest = raw.resolve()
    if dest == inv or dest in inv.parents or inv in dest.parents:
        raise ValueError("Destination overlaps Inventory Bot")
    if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
        raise ValueError("Destination must be nonexistent or empty")
    return dest

def stage(source, target=DEFAULT_TARGET, inventory=INVENTORY):
    source = Path(source).resolve(strict=True)
    target = isolated(target, inventory)
    inv = Path(inventory).resolve()
    if source == inv or source in inv.parents or inv in source.parents:
        raise ValueError("Cannot use Inventory Bot as a source")
    if target == source or target in source.parents or source in target.parents:
        raise ValueError("Source/destination nesting forbidden")
    if not source.is_dir():
        raise ValueError("Source must be directory")
    files = []
    for root, dirs, filenames in os.walk(source, followlinks=False):
        parent = Path(root)
        dirs[:] = [d for d in dirs if d not in SKIP and not (parent / d).is_symlink()]
        for name in filenames:
            p = parent / name
            if name in SKIP or p.is_symlink() or not p.is_file():
                continue
            rel = p.relative_to(source)
            if any(part in SKIP for part in rel.parts):
                continue
            files.append((p, rel))
    # Copy into an empty isolated directory. No changes to running processes.
    target.mkdir(parents=True, mode=0o700, exist_ok=True)
    try:
        for p, rel in files:
            dst = target / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, dst, follow_symlinks=False)
            dst.chmod(0o600)
    except Exception:
        # No automatic destructive cleanup if a partial copy exists.
        raise
    return {"target": str(target), "staged_files": len(files),
            "services_started": False, "inventory_changed": False}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", default=str(DEFAULT_TARGET))
    args = parser.parse_args()
    try:
        print(stage(args.source, args.target))
    except (OSError, ValueError) as exc:
        print("BLOCKED:", exc, file=sys.stderr)
        sys.exit(2)
