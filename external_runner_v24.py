"""External review runner, disabled by default.

Never runs inside Telegram polling. Explicit content is supplied by a trusted
operator, rehashed, and must match the approved manifest. Credentials are not
stored here. No merge or deploy methods exist.
"""
from controller_v20 import verify_request
from dispatch_v17 import reserve_once, record_result
from github_client_v22 import RestrictedGithub
from github_executor_v18 import draft_pr
from handoff_v16 import verify_material

REPO="matrix12345695-afk/ultimate-ai-control"

def submit_review(conn,request_id,base_sha,files,transport,enabled=False):
    if enabled is not True:
        raise PermissionError("External executor not enabled")
    manifest=verify_request(conn,request_id,base_sha)
    if manifest.get("project")!="control":
        raise PermissionError("Only control pilot allowed")
    if not verify_material(manifest,files,base_sha):
        raise ValueError("File content does not match approved hashes")
    # Persist replay barrier before any remote side effects. A partial failure
    # remains reserved and requires an operator to reconcile manually.
    package=reserve_once(conn,request_id,base_sha)
    client=RestrictedGithub(transport)
    result=draft_pr(client,REPO,package,files,base_sha,approved=True)
    record_result(conn,request_id,package["handoff_sha256"],result["url"],True)
    return result
