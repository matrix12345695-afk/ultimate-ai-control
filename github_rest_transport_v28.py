"""Opt-in restricted GitHub REST transport for an isolated runner.

No environment access, embedded token, merge, deployment or broad repo scope.
Token must be a narrowly scoped GitHub App installation token supplied by
the external operator. No live calls occur until a method is invoked.
"""
import base64
import json
import re
import urllib.request
import urllib.error
from urllib.parse import quote

REPO="matrix12345695-afk/ultimate-ai-control"
BRANCH=re.compile(r"^ai-review/[a-z0-9-]{1,90}$")
SAFE=re.compile(r"^(docs|tests|proposals)/[A-Za-z0-9_./-]{1,160}$")
SHA=re.compile(r"^[0-9a-f]{40}$")

class GithubTransport:
    def __init__(self,token,enabled=False,opener=None):
        if enabled is not True: raise PermissionError("GitHub write transport disabled")
        if not isinstance(token,str) or len(token)<20 or any(c.isspace() for c in token):
            raise ValueError("Invalid credential")
        self._token=token
        self._open=opener or urllib.request.urlopen

    def _call(self,method,path,payload=None):
        data=None if payload is None else json.dumps(payload).encode("utf-8")
        req=urllib.request.Request("https://api.github.com/repos/"+REPO+path,
            data=data,method=method,headers={
                "Authorization":"Bearer "+self._token,
                "Accept":"application/vnd.github+json",
                "X-GitHub-Api-Version":"2022-11-28",
                "User-Agent":"ultimate-control-review"})
        with self._open(req,timeout=15) as response:
            return json.load(response)

    def _repo(self,repo):
        if repo!=REPO: raise PermissionError("Repository not allowed")
    def _branch(self,branch):
        if not isinstance(branch,str) or not BRANCH.fullmatch(branch):
            raise PermissionError("Branch not allowlisted")
    def get_base_sha(self,repo):
        self._repo(repo)
        return self._call("GET","/git/ref/heads/main")["object"]["sha"]
    def branch_exists(self,repo,branch):
        self._repo(repo);self._branch(branch)
        try:self._call("GET","/git/ref/heads/"+quote(branch,safe="/"));return True
        except urllib.error.HTTPError as exc:
            if exc.code==404:return False
            raise
    def create_branch(self,repo,branch,sha):
        self._repo(repo);self._branch(branch)
        if not SHA.fullmatch(sha):raise ValueError("Invalid base SHA")
        return self._call("POST","/git/refs",{"ref":"refs/heads/"+branch,"sha":sha})
    def create_file(self,repo,branch,path,content):
        self._repo(repo);self._branch(branch)
        if not isinstance(path,str) or not SAFE.fullmatch(path) or ".." in path.split("/"):
            raise ValueError("Invalid file path")
        if not isinstance(content,str) or len(content.encode())>24000:
            raise ValueError("Invalid file content")
        return self._call("PUT","/contents/"+quote(path,safe="/"),{
            "message":"Approved review-only proposal",
            "branch":branch,"content":base64.b64encode(content.encode()).decode()})
    def get_branch_sha(self,repo,branch):
        self._repo(repo);self._branch(branch)
        return self._call("GET","/git/ref/heads/"+quote(branch,safe="/"))["object"]["sha"]
    def create_draft_pr(self,repo,branch,base_sha,head_sha,title,body):
        self._repo(repo);self._branch(branch)
        if not SHA.fullmatch(base_sha) or not SHA.fullmatch(head_sha):
            raise ValueError("Invalid SHA")
        result=self._call("POST","/pulls",{
            "head":branch,"base":"main","title":title,"body":body,"draft":True})
        return result["html_url"]
    def fetch_pr(self,repo,url):
        self._repo(repo)
        match=re.fullmatch("https://github[.]com/matrix12345695-afk/ultimate-ai-control/pull/([1-9][0-9]*)",url)
        if not match:raise ValueError("Untrusted PR URL")
        result=self._call("GET","/pulls/"+match.group(1))
        return {"url":result["html_url"],"draft":result["draft"],"merged":result.get("merged",False),
            "head":result["head"]["ref"],"head_sha":result["head"]["sha"],
            "base":result["base"]["ref"],"base_sha":result["base"]["sha"],
            "head_repo_full_name":result["head"]["repo"]["full_name"]}
