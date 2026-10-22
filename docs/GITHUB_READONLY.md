# Read-only GitHub integration (Level 2 preparation)

Telegram commands: `/repos` shows configured repository aliases; `/repo control` fetches metadata through GitHub's read-only REST endpoint.

To add repositories, set `GITHUB_READONLY_REPOS=control=matrix12345695-afk/ultimate-ai-control,nova=OWNER/NOVA_REPO`.
Labels must be lower-case short identifiers. Repository paths are validated and explicitly allowlisted.

For **private repositories**, add `GITHUB_READ_TOKEN` to the host's protected environment, with read-only *Metadata* access limited to selected repositories. Never commit it. Public repositories generally require no token. Do not put a token in Telegram commands.

This integration does not read code yet, create branches, open pull requests, or execute changes. GitHub Actions only runs the included unit tests and does not run an always-on bot. Approval system remains separate and no deployment can be triggered.

Before using production credentials, make this repository private, review the workflow, use minimal access, protect the main branch, and set budgets/capabilities explicitly.
