"""External v1.9 orchestration gate. Not invoked by the production bot.

The controller must be given independently verified approval and a restricted
client by a trusted operator. No secrets, model, merge or deploy access.
"""
from github_executor_v18 import draft_pr

ALLOWED_TEST_REPO="matrix12345695-afk/ultimate-ai-control"

def run_review(client, package, files, base_sha, verified_approval=False):
    if verified_approval is not True:
        raise PermissionError("Owner approval must be independently verified")
    if package.get("project")!="control":
        raise PermissionError("Pilot restricted to ULTIMATE AI CONTROL")
    if package.get("execution_performed") is not False:
        raise PermissionError("Unexpected execution flag")
    result=draft_pr(client,ALLOWED_TEST_REPO,package,files,base_sha,approved=True)
    return {"draft_pr":result["url"],"head_sha":result["head_sha"],
            "ci":"pending_external_check","telegram":"pending_external_delivery",
            "merge_performed":False,"deployment_performed":False}
