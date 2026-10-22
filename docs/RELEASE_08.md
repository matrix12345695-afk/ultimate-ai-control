# ULTIMATE AI CONTROL v0.8

The new `control_v08.py` stores local **draft** project proposals with SHA-256 fingerprints and reserves notional per-request cents in a SQLite ledger. It never creates branches, commits, pull requests, deploys or calls a model.

**Crucial:** reservations do not measure actual provider costs, are not suitable for enabling a paid API, and do not enforce a hard external billing cap. Keep `AI_ENABLED=false` and do not add paid credentials yet. Production billing safety additionally needs provider-side caps, price calculations, usage reconciliation, failure handling and single shared database.

GitHub draft changes will be developed on isolated branches after the target repository and scope have been explicitly approved. Current proposals are local records only.

Never put Telegram bot tokens, credentials, sensitive business data or client information in GitHub.
