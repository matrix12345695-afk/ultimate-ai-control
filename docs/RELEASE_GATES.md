# Level 2 deployment gates
All proposed code changes must be made on feature branches and submitted as pull requests. No auto-merge, no production access in pull-request tests, and no secrets in builds.
Before release, require: successful CI, exact commit SHA recorded, human diff review, explicit target-environment approval, documented rollback.
Repository administrators must enable branch protection/rulesets in GitHub settings: require pull requests before merge; require status checks (tests); prevent force pushes/deletion; restrict bypass where available; require fresh approval when new commits arrive.
CODEOWNERS is a reviewer routing aid, not a replacement for branch protection.
AI planning and draft modules do not perform any deployments.
Never paste bot tokens or API keys into GitHub files, issues, PRs or chat.
