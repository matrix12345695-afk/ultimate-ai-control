"""Daily local snapshots and failure notifications, with bounded retention."""
import os
import time
from pathlib import Path
from backup import backup_database, verify_restore_copy

DAY=86400
MAX_COPIES=7

def snapshot_once(db_path, backup_path, now=None):
    now=time.time() if now is None else now
    folder=Path(backup_path)
    folder.mkdir(parents=True,exist_ok=True)
    stamp=folder/"last_success.txt"
    if stamp.exists():
        try:
            if now-float(stamp.read_text()) < DAY:
                return None
        except ValueError:
            pass
    out=backup_database(db_path,folder)
    if not verify_restore_copy(out):
        out.unlink(missing_ok=True)
        raise RuntimeError("Restore test failed")
    stamp.write_text(str(now))
    copies=sorted(folder.glob("control-*.sqlite3"),key=lambda p:p.stat().st_mtime,reverse=True)
    for old in copies[MAX_COPIES:]:
        old.unlink()
    return out

def backup_status(backup_path):
    folder=Path(backup_path)
    copies=list(folder.glob("control-*.sqlite3")) if folder.exists() else []
    return f"Local backup files: {len(copies)}. Offsite backups: NOT configured."

class AlertLimiter:
    def __init__(self, cooldown=3600):
        self.cooldown=cooldown
        self.last={}
    def should_send(self, category, now=None):
        now=time.monotonic() if now is None else now
        previous=self.last.get(category)
        if previous is not None and now-previous<self.cooldown:
            return False
        self.last[category]=now
        return True
