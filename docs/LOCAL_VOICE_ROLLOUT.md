# Local voice acceptance pilot —26 October2026

## Source and tested scope

App b8ed9187d4919c37db7cd48460a9bddb8c33b6ab, Draft PR52 stacked on PR51; previous
installed app a37642bfd9a2c19a86ed92ea2c33e7dee53ef947. This is an acceptance-only native
speech candidate, not completed voice control. Private Telegram audio capture, Russian/
Uzbek accuracy and transcript-confirmed task creation remain pending. No real user audio
or third-party paid model is used.

Local full suite565 passes, zero skips (all17 host-dependent integration checks execute).
Exact app hosted baseline CI push40303932769 and PR40303941488 pass with17 expected skips.
Transport helper suite70 passes. Staging fe6de03a0f3fffb0b249327b79cb56d98972af56;
bridge agent9f0b84e330ffd5dac3767be23f18eefd15197658. First prepare40302653676 failed
after building the portable candidate; diagnostic40303451947 showed
Opus decoder exit0, native inference exit132(SIGILL) during graph initialization. No
application activation occurred. The scalar-only local candidate also exceeded the10CPU-second
cap. A separately versioned host-native v2 build retains the same source/model/decoder pins;
it is not portable to another CPU. No runtime protection was relaxed.
Native prepare request f5dd2c54e0e439d15ba6c6b1f4b95ba6c83b551c;
run40304032348/job121508590972 succeeds at15:03 Asia/Tashkent. Public8-second OGG/Opus
fixture recognized in8.0416 seconds, without owner audio ingestion or paid API. Manifest SHA256
1bffbfd6f48f912da6e303f9b89f9c8131e205cc29a1e008f636bc2bfb04228b.
First activation40368389716/job121732199464 did not replace the app: baseline565 passes
with17 expected skips and real-sandbox565 passes with zero skips; restored backup integrity
passed, then the disposable-copy gate failed because stage10 was still planned before its
installation seed. Corrected that test-copy state transition and verified the complete copy
probe locally starting from a fresh planned stage. Production roadmap was not changed by
that probe. Backup retained:
/home/maksim/.ultimate-review-data/backups/before-uac4-1793035659670913239.sqlite3.
Retry request5865e9834aca97d2fd0b713f073dd3c9f8343c70,
activation40369057736/job121734547934 succeeds at22:33 Asia/Tashkent. Baseline565 pass
with17 expected skips; full real-sandbox565 pass with zero skips. Restored-copy migration,
real OGG/Opus recognition, typed-memory tamper detection and partial Plan projection pass.
Installed app b8ed9187d4919c37db7cd48460a9bddb8c33b6ab; dispatcher2195006,
credential-free worker2194680. Inventory PID67760 and source/configuration metadata unchanged.
Backup/restore verified:
/home/maksim/.ultimate-review-data/backups/before-uac4-1793035912154328711.sqlite3.
Live queue job1056 succeeds, report SHA256
2d28565a56143cd1b41f699eacf351283077239dcca8f9a9123bc5c2804fd647;
manifest1bffbfd6f48f912da6e303f9b89f9c8131e205cc29a1e008f636bc2bfb04228b,
recognition7.8751 seconds for the8-second public English fixture; typed memory1057.
Telegram accepted announcement390 and result391, with persisted receipts. These are not
owner reading or approval. /voice4/menu, completed pilot subtask and stage10 still active
verified. Owner audio ingestion remains disabled. No paid call/hold/spend or new schedule.
Independent verification40370142991/job121738363286 succeeds at22:36 Asia/Tashkent;
same installed SHA, report/manifest digests, job/memory, Telegram receipt and process IDs.
No live rollback executed. The documentation checkpoint commit is separate from installed code.

## Private assets and boundaries

Rootless runtime target /home/maksim/.ultimate-tools/voice-4979-tiny-q5-v2; owner-private
policy /home/maksim/.ultimate-review-data/live/voice-candidate-policy-v2.json, mode acceptance_only.
Whisper.cpp source4979e04f, model revision5359861c, source archive/model/decoder/wheel
hashes are pinned in voice_assets_contract.json. Runtime manifest records the locally
compiled binary and copied library hashes. Native stages see only selected read-only
files and system libraries; no credentials, DB, project mounts or network. All original
emergency source files retain implementation digest
314aa918ef73dfce63523abdb0aa345ca71e93403fca695aa4289fb6f05e118f.

## Rollback and next gate

Only uac4_voice_rollback may revert this exact installed app to the previous emergency-aware
version. It drains UAC jobs, preserves owner pauses/emergency state, retains reports/policy/
assets/receipts/accounting and cancels only unsupported queued voice-local-v1 acceptance
jobs. No live DB restore or independent service/schedule change. Older code needs the newer
reader for typed speech references. Never use the preceding legacy rollback after an actual
emergency epoch change. No live rollback has been executed.

Next: bounded owner-only Telegram file transport with TTL/quota/deduplication; never expose
its bot token to decoders. Show the recognized text and frozen/explicit project before an
owner confirmation creates a text task. Replayed confirmations must not duplicate tasks;
expired/rejected/secret-containing transcripts fail closed. Keep emergency gates, budget
and publication permissions in force; verify a real voice round-trip before completing stage10.
