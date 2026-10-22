# GitHub requests preview

Telegram commands /github_request and /github_request_status store a file-manifest proposal in SQLite and request an expiring content-bound approval. Currently the file is a fixed illustrative docs/review.md; there is no actual patch and no GitHub write after approval. Only an independently reviewed, credential-isolated executor can apply the approved files. Never merge or deploy automatically. AI API stays disabled.
