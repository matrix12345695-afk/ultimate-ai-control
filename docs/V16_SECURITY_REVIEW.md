# v1.6 security review

One-time claim checks approved exact file manifest, approval expiry and fixed Git commit SHA; then marks a request handed_off. It cannot create PRs, change code or deploy. A separate authenticated, least-privilege executor and validated artifact storage are still required for actual PR creation. No AI API calls. Production requires separate approval.
