"""Scoped GitHub App installation token for an isolated review runner.

No token or key ever reaches standard output, git or Telegram. Credential
loading is opt-in, from a local mode-0600 regular file owned by the runner.
"""
import base64
import json
import os
import pathlib
import stat
import subprocess
import time
import urllib.request

APP_ID = 5424384
INSTALLATION_ID = 174076314
BASE = "https://api.github.com"


def _encode(value):
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _trusted_key(path):
    key = pathlib.Path(path)
    info = key.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
        raise PermissionError("GitHub App private key must be a regular user-owned file")
    if stat.S_IMODE(info.st_mode) != 0o600 or info.st_size < 300:
        raise PermissionError("GitHub App private key must be nonempty and chmod 600")
    return key


def make_jwt(path, now=None, signer=None):
    path = _trusted_key(path)
    timestamp = int(time.time() if now is None else now)
    header = _encode(json.dumps({"alg": "RS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _encode(json.dumps({
        "iat": timestamp - 30,
        "exp": timestamp + 480,
        "iss": APP_ID,
    }, separators=(",", ":")).encode())
    signing_input = (header + "." + payload).encode("ascii")
    if signer is None:
        signed = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", str(path)],
            input=signing_input, capture_output=True, check=True, timeout=10,
        ).stdout
    else:
        signed = signer(path, signing_input)
    if not isinstance(signed, bytes) or not signed:
        raise RuntimeError("GitHub App signing failed")
    return header + "." + payload + "." + _encode(signed)


def installation_token(key_path, opener=None):
    jwt = make_jwt(key_path)
    body = json.dumps({
        "repositories": ["ultimate-ai-control"],
        "permissions": {"contents": "write", "pull_requests": "write", "actions": "read"},
    }).encode()
    request = urllib.request.Request(
        BASE + "/app/installations/" + str(INSTALLATION_ID) + "/access_tokens",
        method="POST", data=body,
        headers={
            "Authorization": "Bearer " + jwt,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "ultimate-control-isolated-review",
        },
    )
    with (opener or urllib.request.urlopen)(request, timeout=15) as response:
        result = json.load(response)
    token = result.get("token")
    if not isinstance(token, str) or len(token) < 30:
        raise PermissionError("GitHub did not issue an installation token")
    return token
