# UAC emergency-control rollout — 26 October 2026

## Source and checks

- App: `a37642bfd9a2c19a86ed92ea2c33e7dee53ef947`,
  [Draft PR51](https://github.com/matrix12345695-afk/ultimate-ai-control/pull/51), stacked on PR50.
- Previous app: `cd8aa26964d27c2cea06360fc92a88b8fa2a3275`.
- Local full suite:551 tests pass, zero skips, including all15 sandbox checks and27 new
  emergency fault/integration cases. Fixture provider accounting uses synthetic credentials
  and in-process responses; these are not actual paid API calls.
- Exact-source Safe unit tests: push40297441230 and PR40297445882 succeed; hosted baseline
  skips15 host-dependent sandbox checks.
- Transport/rollout helper suite:67 tests pass.
- Staging transport: `eb33bca796d8ae5590c048d2af0e03f86d8d3e9f`.
- Bridge agent: `13d48b0ea09cd22caa9ab28dba1ef46dced49e29`.
- Deployment request: `112c782d34ee29cdcaef0af3f80286d82b1fe192`.
- Activation: [run40297890272](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40297890272),
  job121488316872 succeeds; completed26 October14:17 Asia/Tashkent. VPS baseline551 pass
  with15 expected skips; full sandbox suite551 pass, zero skips.
- Independent verification: [run40298557723](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40298557723),
  job121490516058 succeeds26 October14:19 Asia/Tashkent; same hashes, receipts, processes
  and evidence-backed Plan state.
- Runtime `/home/maksim/.ultimate-review-runtime`; own rootless cron/flock dispatcher1681469,
  credential-free worker1681143. No systemd unit or new schedule.
- Inventory process67760 unchanged; source fingerprints/config metadata match the baseline.
- Backup `/home/maksim/.ultimate-review-data/backups/before-uac4-1793006158200625461.sqlite3`;
  restored copy integrity, migration, persistent stop/reset, old approval invalidation,
  notification outbox and evidence-tamper detection pass.
- Live queue selftest890 passes8 scenarios on a separate in-memory DB; typed memory891.
  Report SHA256 `113c7b4d30d2ebda71639f5a497c69ac59acea04d4f7d41022f46bea508070af`;
  implementation SHA256 `314aa918ef73dfce63523abdb0aa345ca71e93403fca695aa4289fb6f05e118f`.
- Telegram accepted announcement388 and result389; persisted delivery receipts are not
  owner reading or approval. `/emergency`, menu status and completed Plan subtask pass.
- Live emergency remains unlatched/epoch0; no live emergency stop or rollback was executed.
- Paid policies remain disabled, no live provider costs/reservations. Existing owner
  follow-up157/Telegram380 and approval/candidate counts unchanged.

## Operational contract

See [EMERGENCY_CONTROL.md](EMERGENCY_CONTROL.md). Deployment tests real stop/reset only
on a restored disposable UAC database and the eight-case queue acceptance entirely in memory.
It does not activate a live emergency as a test. No service outside UAC is restarted; no
NOVA production mutation, schedule installation, key provisioning or paid policy change.

The limited legacy rollback `uac4_emergency_rollback` may restore the previous app only
while current code matches and control remains at epoch0/unlatched. It holds the DB writer
lock through its own dispatcher/worker replacement so a concurrent stop cannot be ignored.
After any live stop/reset it refuses downgrade before changing source; retain compatible
emergency-aware code and prepare a forward repair. Additive records, approvals, reports,
notifications, memory and accounting are retained; no live DB restore is authorized here.
