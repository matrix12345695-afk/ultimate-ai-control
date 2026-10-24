"""Review-only path safety helper; not imported by production. """
import re

_PATH = re.compile(r"^(docs|tests|proposals)/[A-Za-z0-9_./-]{1,120}$")
_BLOCKED = (".env", "credentials", "secret", "token")

def safe_review_path(value):
    """Reject traversal, unusual separators and sensitive destinations."""
    if not isinstance(value, str) or not _PATH.fullmatch(value):
        return False
    if any(part in ("", ".", "..") for part in value.split("/")):
        return False
    return not any(part in value.lower() for part in _BLOCKED)
