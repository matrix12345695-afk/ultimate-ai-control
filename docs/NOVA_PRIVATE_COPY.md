# NOVA private-copy draft: exact acceptance and remaining gate

NOVA Draft17 adds explicit encrypted application-data export and isolated recovery tools. It is not installed/published, registers no application route/Telegram command/schedule/startup and changes no dependency. Exact candidate9df2a1c9fcc35e83f1a2fe35bee2480afac3254f is based on Draft16a3c3e77e0e74d33241935d25dd3bdfdd306ccd90. The release protocol still binds its separate previously reviewed candidate; this draft receives no implicit publication approval.

The exporter requires the fixed internal NOVA host/database/user/service scope, an existing recipient certificate and private directory. One read-only repeatable snapshot and100-row cursors cover all4 supported application tables. Values remain text, including raw jsonb and bigint values, with canonical UTC/ISO timestamp output. PG18 NOT NULL constraints are checked through column attributes; other keys/constraints and unsupported schema objects are checked explicitly. The custom application-data format is not a full arbitrary PostgreSQL/cluster dump.

Plaintext streams directly into standard OpenSSL3 CMS authenticated encryption (AES-256-GCM/RSA-OAEP-SHA256). RSA3072-or-stronger current recipient certificate, private0600 output in0700 directory, bounded byte/row/time limits, pinned descriptor inputs, exclusive file publication, partial cleanup and source rollback on failures are tested. No production key is created, read or installed by ULTIMATE. A recovery key is used only in the isolated fixture. Sender authenticity is not implied by possession of the public recipient certificate: expected checksum/source identity must be confirmed privately. Key custody and separate key recovery remain owner decisions.

Recovery authenticates and validates all encrypted/structured data before opening the target. It permits only127.0.0.1:15432/nova_private_restore and an empty PostgreSQL18 target. Static reviewed DDL, parameterized inserts, sequence checks and full text readback run in one transaction before commit. There is no production-target override, arbitrary SQL execution from the copy, --clean/CASCADE or network expansion.

Hosted gate3901bc71308f1f473a02b519bf1c6c55e05789a4 / required push40290801445/job121465134159 passed30 checks:18 native unit/fault tests and12 actual PostgreSQL18 cases.5003 synthetic leads/all4 tables were encrypted and restored; a later concurrent write was excluded, source state stayed unchanged, large bigint/JSON numbers beyond JavaScript safe integer, Unicode and microseconds were preserved. Event sequence, FK, Telegram/reminder dedup and transactional failure rollback are verified. Native developer unit runtime24.19.0/OpenSSL3.5.7 was used for iteration; the hosted acceptance runs the required Node24.21.0, OpenSSL3.0.13 and PostgreSQL18.6. No local24.19 runtime result is presented as24.21 acceptance. The initial d09def38 source/harnessbfdec31b failed on PG18 catalog differences; this was corrected before successful acceptance.

Source-manifest SHA256625080dec4cdce53139b8d5692ab8143a93413b919d45beb9ce67b35d5e33ca1. Production lock remains9db9b93b90b4fbeabb5fb780eefe6345e5f87a08d9e2b530cd93335f46efafcf. Same official PostgreSQL18 image9770878138a2e83abcb10856d30cc3f24dae0d317bb956db6ab9159de6c3c80d and reviewed14-package pg8.23.1 tree. See [harness review](../ci/nova-private-copy/REVIEW.md); a full dependency/cryptographic audit is not claimed.

Archive12636252081,1424 bytes, SHA256c290a6e7da296ac9091ee2bc0c08c45851f5c620eb693a2596efaae374a0fb3a, expiry2026-11-25T08:14:12Z. ZIP and entries verified: report.json and public source-pins.json only. Report-file SHA2564940583a2330b07d1cf0ab975bedb74dfa5ee3e9ea0c545dc73972ab6ad75850. No plaintext/ciphertext backup or fixture certificate/private key is archived. All DB state is synthetic and temporary.

UAC /nova_copy and “🔐 Копия NOVA” use a separate exact-contract read-only App broker/profile, immutable report, queue delivery, typed memory and a completed Plan9 subtask while that stage remains active. /test_nova_copy only revalidates fixed GitHub CI/archive, never SQL or keys. /nova_recovery links the new draft. The original delivered owner follow-up157/message380 is retained unchanged; no duplicate decision or implicit approval is created. Report booleans production_backup_verified, production_key_generated, durable_retention_verified, Render_execution_path_available and publish_allowed remain false.

## Why real export remains blocked

Current verified Render docs https://render.com/docs/free state that Free web services have no SSH/Dashboard shell or one-off jobs. https://render.com/docs/private-network permits outbound private-network connections, but current tools provide no execution path inside the service; runtime OpenSSL and current DB binding are not verified. The hosted SQL connector is blocked by the database's empty external allowlist. No network setting, service plan, new role or public endpoint was changed. A CLI left in a draft branch does not become a running export job.

An explicit reviewed invocation path, recipient/key custody and private durable destination are still required, followed by an actual private export and isolated recovery of that exact object. Render files are ephemeral: leaving encrypted output there is not durable retention. The known Free NOVA database expires19November2026 at13:40 Tashkent. Payments, access changes and exact-version publication require separate owner decisions; the new report grants none of them. Model setup is still deferred, paid calls0 and hourly coding automation stays disabled.

[UAC-only rollout40291224949](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40291224949)
passed61 transport and524 app tests on VPS: default pass skips15 host-dependent cases,
full explicit sandbox-enabled pass executes all15 without skips. Actual App read-only
CI authentication and restored-copy pending/report-tamper/memory probes pass. VPS job869,
report9b16c0fa183b178dfa4de2e6e7d5d6d84a221fb1364ee268985533a845a31abe,
memory870 and Telegram result384 accepted. Original owner-followup157/message380 content
and receipt unchanged. One dispatcher1622690, one credential-free worker1622307, Inventory67760
and source/config unchanged. Model setup deferred, paid calls/holds/spend0; no new coding
schedule, service, production key or NOVA/Render/DB/network/payment/publication mutation.
Own backup tested through isolated restored copy:
/home/maksim/.ultimate-review-data/backups/before-uac4-1793002788670285838.sqlite3.
Transportc5dcf0f53a85f6a07c793699fb1f30577846b94b; bridge-agenta468d1ae4d319efbf50695468e84ed7627a48c9a.
Installed appcd8aa269; subsequent checkpoint documentation does not change installed code.
[Independent verify40291828696](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40291828696)
passed with the same source/report/archive, result receipt, typed memory/Plan, original
owner-followup content, Inventory metadata and disabled paid policies.
