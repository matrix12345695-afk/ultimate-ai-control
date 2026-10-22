# Metered OpenAI transport: disabled until private configuration

This increment implements a direct Responses API transport and conservative cost ledger. It
does not enable automatic queue/model calls, start a credential broker, generate production
changes or run model output. Legacy unmetered adapters stay blocked. No key or paid call is
needed for installation, status, quotations, or fault tests.

## Financial contract

Before network I/O, one SQLite BEGIN IMMEDIATE transaction records the request fingerprint,
stable request key and maximum-cost hold. The maximum uses the entire reviewed model input
ceiling (272,000 tokens), plus the configured output cap (default 2,048, maximum 4,096).
It does not depend on an approximate prompt tokenizer. Model, prices and endpoint cannot be
selected by model output. Integer micro-USD arithmetic rounds costs upwards.

Only one paid call may be unresolved at a time. The same completed request key returns its
persisted response; changing its input is rejected. The same pending/ambiguous key is never
resent. There is no HTTP/SDK retry or provider fallback, and no exactly-once delivery claim.
A crash after reservation, timeout, malformed receipt, unexpected model/tier, unpriced cache
write or excessive usage keeps the full hold and prevents further calls. The critical owner
notice is durable and deduplicated. Unresolved holds carry across UTC month boundaries.
Automatic dispatch is blocked during the last 60 seconds of a UTC month.
The recorded reservation month is checked again immediately before sending and after the
receipt. A delayed request crossing into a new month retains its full hold and stops the
provider rather than guessing which billing month the provider used.

A valid receipt atomically settles token costs and stores the response. Cached input is billed
using its reviewed rate; output tokens include reasoning tokens. Incomplete, refused, sensitive,
oversized or tool-containing output is marked unusable but valid usage is still charged.
No tools are supplied to the model; returned tool instructions are never executed. A returned
advisory plan is not proof of code changes or successful tests.

The hard application ceiling is $30/month and private policy may only lower it. At $24 an INFO
notice is created; insufficient headroom blocks the request before sending and creates one
DECISION notice per month. This is application accounting, not a provider invoice or visibility
into other applications using the same account. Provider billing controls remain a complementary
external layer where available. Taxes, unrelated account usage and future tariff changes are
outside this token ledger.

## Reviewed tariff catalog

Official model pages checked 2026-10-22 UTC:

| Snapshot | Input / 1M | Cached / 1M | Output / 1M | Maximum input |
| --- | ---: | ---: | ---: | ---: |
| gpt-5-mini-2025-08-07 | $0.25 | $0.025 | $2.00 | 272,000 |
| gpt-5-nano-2025-08-07 | $0.05 | $0.005 | $0.40 | 272,000 |

Sources: [GPT-5 Mini](https://developers.openai.com/api/docs/models/gpt-5-mini),
[GPT-5 nano](https://developers.openai.com/api/docs/models/gpt-5-nano),
[Responses create reference](https://developers.openai.com/api/reference/resources/responses/methods/create),
[text generation guide](https://developers.openai.com/api/docs/guides/text).
The reviewed catalog expires on 2026-11-21 UTC; a code-reviewed update is required afterwards.
It never silently chooses a newer or more expensive model. These are bounded initial options,
not a claim that they are the best models for every future developer task.

Requests use only https://api.openai.com/v1/responses, service_tier=default, store=false,
stream=false and tools=[]. TLS verification stays enabled; redirects are rejected before
forwarding credentials. Response bytes are capped; the client has a 20-second network timeout.
X-Client-Request-Id supports tracing, not a provider idempotency guarantee.

## Private operator configuration

The installed provider-policy.json is mode 0600 and enabled=false. There is no key in the
policy. The separate owner-only key file must also be mode 0600, owned by the execution user,
and not reached through symlinks. Environment keys, Telegram messages and GitHub source files
are not key inputs. This increment never reads Inventory credentials for model use.

Only the private operator CLI may explicitly call this transport after configuration. It is
not exposed as a Telegram paid-call command. The operations worker and sandbox never receive
the key. A future authenticated credential broker and developer queue handler still need to
be implemented and tested; setting a key alone does not activate autonomous coding.

CLI operations: provider_cli.py status, quote, plan. Each requires --db and --policy. plan
also requires --key-file, --task-file (private text, mode 0600), and --request-id. It accepts
only the control project; no project code or client data is automatically collected. Raw
prompts, private keys and HTTP error payloads are never printed. Advisory text stays in the
private database. Telegram /provider4 reports configuration/accounting without reading a key.

## Recovery of ambiguous calls

Keep the transport stopped. Use the stored request trace ID, timestamp and provider-side
usage/billing evidence to reconcile the specific hold. Do not delete rows, reset month totals,
replay requests with a new key, or automatically release a hold because it is old. A separate
reviewed reconciliation operation is required; there is intentionally no chat unfreeze button.

Validation includes concurrent duplicate requests, timeouts/restart/month rollover, quota
exhaustion, private-file boundaries, redirect rejection, cached-token arithmetic, refused/tool
output and missing/unpriced/excessive receipts. These tests use deterministic fake responses,
not paid API calls. Live billing and actual model behavior remain unverified until private setup.

The trusted dispatcher, operator CLI and operations worker currently share the VPS Linux user.
Keeping keys out of their environments is logical separation, not an OS permission boundary
between same-UID processes. Before general agent tools receive broader host access, the future
credential broker needs an independently reviewed OS access boundary. The existing untrusted
Python test sandbox does not mount host home/configuration directories.
