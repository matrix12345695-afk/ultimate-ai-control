"""Restricted remote GitHub adapter protocol. Credentials supplied externally.

No tokens, networking, merge or deploy operations are defined here.
"""
ALLOWED="matrix12345695-afk/ultimate-ai-control"

class RestrictedGithub:
    def __init__(self,transport):
        self.transport=transport
    def check_repo(self,repo):
        if repo!=ALLOWED: raise PermissionError("Repository not allowlisted")
    def get_base_sha(self,repo):
        self.check_repo(repo)
        return self.transport.get_base_sha(repo)
    def branch_exists(self,repo,branch):
        self.check_repo(repo)
        return self.transport.branch_exists(repo,branch)
    def create_branch(self,repo,branch,sha):
        self.check_repo(repo)
        if not branch.startswith("ai-review/"): raise PermissionError("Protected branch")
        return self.transport.create_branch(repo,branch,sha)
    def create_file(self,repo,branch,path,content):
        self.check_repo(repo)
        if not branch.startswith("ai-review/") or not path.startswith(("docs/","proposals/","tests/")):
            raise PermissionError("Protected destination")
        return self.transport.create_file(repo,branch,path,content)
    def get_branch_sha(self,repo,branch):
        self.check_repo(repo)
        return self.transport.get_branch_sha(repo,branch)
    def create_draft_pr(self,repo,branch,base_sha,head_sha,title,body):
        self.check_repo(repo)
        if not branch.startswith("ai-review/"): raise PermissionError("Protected branch")
        return self.transport.create_draft_pr(repo,branch,base_sha,head_sha,title,body)
