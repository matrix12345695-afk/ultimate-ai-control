# Private ULTIMATE model configuration

Observed 2026-10-23 UTC. The model is not active. An existing ChatGPT subscription or
replenished Codex usage allowance does not provision OpenAI API credentials or account credit.

## Owner step

Open [the private transport repository's new Actions secret page](https://github.com/matrix12345695-afk/inventory-bot/settings/secrets/actions/new).
Create the repository secret named `ULTIMATE_OPENAI_API_KEY` with a separate OpenAI API key.
Do not send its value through ChatGPT, Telegram, source files or a workflow request. Tell the
operator only that the secret was added. This step does not buy credit or enable any policy.
The Inventory application and its credentials are not used or changed.

## Reviewed transport

Transport branch: inventory-bot/server-bridge-v1. Initial helper/workflow commit:
`ede32b5232adc5c7a90bf18682a6479234eafb8d`.

- `.github/workflows/uac-private-model-key.yml` has a separate path trigger on
  `.uac-provider/key-install-request.json`, exact event-commit checkout, read-only repository
  permission and the existing shared runner concurrency group. Only the owner's pushes run it.
- The default request is `check_only`, refreshed to installed app
  `6c6df74997bcdb283e47ac664e26f9d778dd315e` after the roadmap update. This check receives no model secret, reads only
  private policy files and key metadata, and creates nothing.
- The secret is injected into only the explicit installation step, which is skipped for
  `check_only`. It is not added to the existing Inventory workflow or any worker environment.
- An operator may change the request to `install_key` only after confirming the owner added
  the secret and the runtime still matches the reviewed pin. Revalidate/update the pin through
  code review if a later runtime was deployed. Never bypass a stale-pin refusal.
- `server_bridge/install_ultimate_key.py` verifies user/path/ownership, disabled provider and
  broker policies, and a monthly application ceiling no greater than $30. It writes only
  `/home/maksim/.config/ultimate-review/openai-api.key`, mode 0600, using exclusive creation and
  fsync. It disables process dumping, rejects symlinks and never prints the value or its hash.
  Same-value retry is idempotent; a different existing key is rejected rather than overwritten.
- No model call, policy activation, application restart, key rotation or Inventory access is
  part of key installation. Subsequent enablement and an actual metered acceptance test remain
  explicit operations within the existing approved $30 ceiling.

## Verification and remaining gates

[Server dry-run](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39903189529)
passed four helper tests and private preflight. `key_present=false`,
`secret_install_requested=false`, `paid_policies_enabled=false`; the install step was skipped.
The tests use temporary artificial keys only. A real key transfer and account/billing access
have not been verified.

After the roadmap runtime update, a fresh
[check-only run](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39904885830)
also passed four helper tests and the current-runtime preflight. The install step remained
skipped, `key_present=false` and `paid_policies_enabled=false`.

The concrete owner request was delivered through the existing ULTIMATE dispatcher:
notification 36, Telegram message 203, event `developer-private-key-setup-v1`.
[Receipt-confirming run](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39903359280)
passed 15 transport tests. The relay only observes the persisted delivery receipt; it does not
send independently or mark delivery itself. Reusing this event key does not create a new request.

After private setup: verify policy/key boundary without printing credentials; run one bounded
reviewed model task through the existing reservation guard; reconcile actual model/usage receipt;
test its exact capsule in Bubblewrap; confirm the owner notification. Keep release publication
separate. Ambiguous calls retain their financial hold and block further paid calls.
