"""SQLite hot backup with integrity check and test restore.

No external upload; encrypted off-host backups are a separate milestone.
"""
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

def backup_database(source, backup_dir):
    source=Path(source).resolve()
    folder=Path(backup_dir).resolve()
    if not source.is_file():
        raise FileNotFoundError("Source database does not exist")
    if folder == source.parent:
        raise ValueError("Backups must use a separate directory")
    folder.mkdir(parents=True,exist_ok=True)
    name="control-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+".sqlite3"
    target=folder/name
    try:
        with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as src:
            with sqlite3.connect(target) as dst:
                src.backup(dst)
        with sqlite3.connect(f"file:{target}?mode=ro",uri=True) as verify:
            if verify.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
                raise RuntimeError("Backup integrity check failed")
        return target
    except Exception:
        target.unlink(missing_ok=True)
        raise

def verify_restore_copy(backup_file):
    """Restore into memory, then integrity check: does not touch live DB."""
    with sqlite3.connect(f"file:{Path(backup_file).resolve()}?mode=ro",uri=True) as src:
        with sqlite3.connect(":memory:") as restored:
            src.backup(restored)
            return restored.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
