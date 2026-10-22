"""Fail-closed preflight for an isolated GitHub App review executor.

This checks configuration shape only; it cannot confirm actual GitHub App
installation permissions. No tokens are printed or persisted.
"""
import os
import re

REPO="matrix12345695-afk/ultimate-ai-control"
DECIMAL=re.compile(r"^[1-9][0-9]{0,18}$")

def preflight(settings):
    if settings.get("REVIEW_EXECUTOR_ENABLED")!="true":
        raise PermissionError("Executor disabled")
    if settings.get("REVIEW_REPO")!=REPO:
        raise PermissionError("Repository mismatch")
    if not DECIMAL.fullmatch(settings.get("GITHUB_APP_ID","")):
        raise ValueError("Missing GitHub App ID")
    if not DECIMAL.fullmatch(settings.get("GITHUB_INSTALLATION_ID","")):
        raise ValueError("Missing installation ID")
    if "-----BEGIN" not in settings.get("GITHUB_APP_PRIVATE_KEY",""):
        raise ValueError("Missing GitHub App private key")
    if not DECIMAL.fullmatch(settings.get("REVIEW_ADMIN_CHAT_ID","")):
        raise ValueError("Missing admin chat")
    token=settings.get("REVIEW_TELEGRAM_BOT_TOKEN","")
    if not isinstance(token,str) or ":" not in token or len(token)<25:
        raise ValueError("Missing Telegram token")
    if settings.get("REVIEW_ALLOW_MERGE")=="true" or settings.get("REVIEW_ALLOW_DEPLOY")=="true":
        raise PermissionError("Merge and deploy prohibited")
    return {"repo":REPO,"mode":"draft_only","configured":True}

def from_environment():
    keys=("REVIEW_EXECUTOR_ENABLED","REVIEW_REPO","GITHUB_APP_ID",
          "GITHUB_INSTALLATION_ID","GITHUB_APP_PRIVATE_KEY",
          "REVIEW_ADMIN_CHAT_ID","REVIEW_TELEGRAM_BOT_TOKEN",
          "REVIEW_ALLOW_MERGE","REVIEW_ALLOW_DEPLOY")
    return preflight({k:os.environ.get(k,"") for k in keys})
