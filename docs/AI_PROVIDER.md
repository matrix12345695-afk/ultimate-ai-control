# AI Provider (opt-in, disabled by default)

No provider is active in v0.7. Existing ChatGPT subscriptions do not automatically fund API requests.

Configuration keys (only in the runtime secret environment, never in GitHub):
AI_ENABLED=false
AI_PROVIDER=none
AI_MODEL=
AI_API_KEY=
AI_ENDPOINT=
AI_ALLOWED_HOSTS=
AI_MONTHLY_BUDGET_USD=0

`/ai_status` reports configuration status without revealing secrets. `/ai_plan nova <request>` attempts an advisory proposal only when explicitly enabled and configured.

**Limitations:** The monthly budget setting is a configuration gate, NOT a real spend tracker. Before using a paid provider, implement token/cost accounting, durable quotas, provider billing limits and error handling. Never enable until all limits and explicit owner approval are established. Do not feed sensitive project data or Kinder Spa client information to any external model.

The AI response is untrusted advisory text, not code to execute. No automatic writes or production deployments.

## UAC4 operations update

The separate `budget_gate.py` ledger now provides atomic conservative monthly reservations
with a hard $30 ceiling, per-project/agent attribution and usage receipts. It does not make the
legacy provider safe to enable: the old unmetered transport is blocked. A reviewed priced
transport, private key configuration and real provider usage reconciliation remain required.
No paid provider is enabled by the offline code recipes or rootless test executor.
