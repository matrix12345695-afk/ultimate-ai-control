#!/usr/bin/env python3
"""Fail-closed, isolated ULTIMATE deployment preflight. Read-only and offline."""
from pathlib import Path
import os
import sys
import json

INVENTORY = Path("/home/maksim/inventory-bot")
DEFAULT_TARGET = Path("/home/maksim/ultimate-ai-control")
def check(target=DEFAULT_TARGET, inventory=INVENTORY):
    target = Path(target).absolute()
    inventory = Path(inventory).resolve()
    if target.is_symlink():
        raise ValueError("Symlink target not permitted")
    target = target.resolve()
    if target == inventory or inventory in target.parents or target in inventory.parents:
        raise ValueError("Target overlaps Inventory Bot directory")
    if target.exists() and not target.is_dir():
        raise ValueError("Target is not a directory")
    if target.exists() and any(target.iterdir()):
        raise ValueError("Target must be empty; existing ULTIMATE requires separate backup/upgrade procedure")
    if not target.is_absolute():
        raise ValueError("Target must be absolute")
    return {"status": "PREFLIGHT_ONLY", "target": str(target),
            "inventory_untouched": True, "deploy_performed": False}
if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv)>1 else DEFAULT_TARGET
    try:
        print(json.dumps(check(target),ensure_ascii=False))
    except (OSError,ValueError) as exc:
        print("BLOCKED:",exc,file=sys.stderr)
        sys.exit(2)
