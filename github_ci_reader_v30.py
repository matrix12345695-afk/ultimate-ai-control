"""Read-only GitHub Actions transport for the isolated review workflow.

Uses an externally supplied token. Never treats a workflow run as verified
unless GitHub returns the exact requested head SHA.
"""
import json
import re
import urllib.request
from urllib.parse import quote

REPO="matrix12345695-afk/ultimate-ai-control"
SHA=re.compile(r"^[a-f0-9]{40}$")

class GithubCIReader:
    def __init__(self,token,enabled=False,opener=None):
        if enabled is not True: raise PermissionError("CI transport disabled")
        if not isinstance(token,str) or len(token)<20 or any(c.isspace() for c in token):
            raise ValueError("Invalid credential")
        self.token=token
        self.opener=opener or urllib.request.urlopen

    def __call__(self,head_sha):
        if not isinstance(head_sha,str) or not SHA.fullmatch(head_sha):
            raise ValueError("Invalid commit SHA")
        url=("https://api.github.com/repos/"+REPO+
             "/actions/runs?head_sha="+quote(head_sha)+"&per_page=50")
        req=urllib.request.Request(url,headers={
            "Authorization":"Bearer "+self.token,
            "Accept":"application/vnd.github+json",
            "X-GitHub-Api-Version":"2022-11-28",
            "User-Agent":"ultimate-control-ci"})
        with self.opener(req,timeout=15) as response:
            data=json.load(response)
        if not isinstance(data,dict) or not isinstance(data.get("workflow_runs"),list):
            raise ValueError("Invalid GitHub Actions response")
        rows=[]
        for run in data["workflow_runs"]:
            if not isinstance(run,dict) or run.get("head_sha")!=head_sha:
                continue
            if run.get("name")!="Safe unit tests":
                continue
            if run.get("event")!="pull_request":
                continue
            rows.append({"head_sha":head_sha,"name":run["name"],
                         "status":run.get("status"),"conclusion":run.get("conclusion")})
        return rows
