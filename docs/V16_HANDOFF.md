# v1.6 verified handoff

Approved request manifests can be bound to a complete base commit SHA and independently checked against precise file content. Telegram command /github_handoff displays the package digest, without executing it. No external GitHub executor is installed; no automated branch/PR creation, merge, deploy or AI API access is enabled. A separate least-privilege executor and persisted replay protection are required before processing real requests.
