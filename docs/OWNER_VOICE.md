# Owner voice intake and explicit text-task confirmation

This increment connects short owner Telegram voice messages to the existing native speech
runtime. It creates a text task only after the owner views the exact transcript, checks the
project and confirms with its current code. This confirmation never approves a publication,
purchase, business-rule change or permission expansion. The paid model remains deferred;
confirmed general development tasks still wait for its separately authorized executor.

## Owner flow

1. `/start`, then «🎙 Голос 4.0». Select an existing project with `/project nova`, for example.
2. `/voice_lang ru` or `/voice_lang uz` chooses the language of subsequent recordings. RU is
   the default; neither setting alters a recording already accepted.
3. Send a mono OGG/Opus voice message, at most10 seconds/256KiB. Do not include passwords or
   API credentials. Up to5 messages may wait; at most30 are accepted in a rolling24-hour window.
4. A notification links to `/voice NUMBER`. This shows the text, frozen project, deadline
   in Asia/Tashkent and `/voice_confirm NUMBER PROJECT CODE`. Opening the preview is required.
5. `/voice_project NUMBER nova` changes the target, invalidates the old code and shows a new
   preview. `/voice_reject NUMBER` cancels an unconfirmed input. Incorrect text can be rejected
   and sent as a normal text task; transcripts are never routed as Telegram commands.
6. Confirmation atomically inserts one ordinary text task. Repeating the same confirmation
   returns that task's ID, including after expiry or a later stop; it performs no new action.
   A different code/project fails closed. Confirmed tasks use `/job` and `/job_cancel`.

The preview expires15 minutes after capture, including time spent paused. After an emergency
stop/reset, old epochs cannot confirm. Ordinary queue pause may hold a newly confirmed task;
it does not authorize its execution or any later publication. Delivery of a notification and
manual resolution of that inbox item are distinct from transcript confirmation.

## Boundaries and durability

The existing dispatcher authenticates the one configured owner/private chat, and intake
checks both sender and chat IDs again before any download. A separate trusted transport
process receives the bot credential through stdin, never argv, environment, file, worker or
decoder. It has an8-second parent-enforced deadline including DNS,256MiB virtual-memory and
4CPU-second caps, and a parent-death SIGKILL. It accepts only the fixed HTTPS Telegram getFile
and file endpoints, validates the returned voice path/size, refuses redirects and bounds
metadata/body reads. Errors never return the token, URL or arbitrary response text.

Audio is stored in owner-private `voice-audio/NUMBER.ogg` files, outside the control database
and its SQLite snapshots. The directory must be0700, files0600; symlinks and changed hashes
are rejected. A receiving row is committed before file IO; job insertion and row linking
are atomic. Replayed update IDs do not redownload or enqueue duplicates. Interrupted capture
becomes failed after30 seconds without automatic network retry. Queue attempts are bounded
to one per recognition input; failures ask for a shorter recording or text.

Ogg page structure/serial/sequence, mono OpusHead, byte/granule limits and actual decoded PCM
duration are checked. Oversized/chained/stereo/truncated input, silent PCM, changed bytes,
secret-like/empty/oversized text or mismatched receipts cannot produce a preview/task.
Detection of obvious credential patterns is not comprehensive speech DLP.

Decoding and Whisper run in separate credential-free Bubblewrap namespaces. They see only
selected read-only native assets, one input and system libraries. Network/forks/host project
files are denied; reviewed pthread flags remain allowed. Each child retains the existing
1CPU affinity/768MiB virtual-space/10CPU-second caps, decoder4s and recognizer18s wall limits,
bounded output and no host fallback. No native dependency, model, system package or service
is replaced by this increment. Private manifest/model/source pins are unchanged.

Raw audio is deleted after processing/rejection, or by cleanup when expired/interrupted.
Cleanup runs even while the queue is paused; an offline/stopped worker can delay physical
removal. Confirmation always checks the deadline independently. Failed cleanup does not
follow symlinks or delete foreign files. Unconfirmed preview text is cleared on expiry,
rejection or confirmation; private DB backups may retain earlier text. Confirmed task text,
metadata and immutable recognition receipt remain in the journal. Evidence memory records
hashes/timing/language, not the transcript or raw audio. Pending voice notifications are
resolved only by that input's confirmation/rejection/expiry; unrelated decisions are retained.

## Activation and rollback

Owner processing needs both a0600 `voice-owner-policy-v1.json` with mode `owner_preview`
and `voice_intake_gate=enabled` in UAC settings. Installation starts with the gate disabled,
validates source/native tests and a restored disposable DB, then explicitly enables it.
Emergency admission/epoch guards are separate and remain in force; their source digest is
unchanged. API budget/policies, hourly automation and Inventory remain untouched.

Rollback disables that gate before draining UAC, replaces only its dispatcher to terminate
in-flight downloads, then expires unconfirmed inputs, resolves their decisions, cancels only
matching queued recognition jobs and removes their private files. Already confirmed normal
text tasks, receipts, history and other owner decisions are retained. It restores the preceding
emergency-aware UAC code and its worker/dispatcher; no DB restore, independent service action
or schedule change is involved. The private policy/assets stay available for an authorized
forward reactivation. Downgrading emergency-aware code to legacy after a stop remains forbidden.

## Verification and remaining owner gate

`/test_voice_flow` executes one real native public-English OGG test and eight explicitly
synthetic state-machine cases on a separate disposable DB. The report states actual incoming
Telegram round-trip and real owner confirmation are **not** verified by these fixtures.
It is immutable/hash-bound, linked to typed evidence memory and the live partial Plan.
Historical engine evidence remains valid history without claiming incoming owner audio.

The source suite adds48 tests: authentication, quotas/metadata, replay and atomicity, two
SQLite connections, storage/crash/lease/tamper, stop/reset/gate behavior, cancellation and
rollback privacy, exact project/preview binding, plain slash text, receipt/memory/Plan, URL/
redirect/truncation/slow-stream/credential handling, real parent-death/resource limits and
the real isolated recognition/fixture chain. Full source suite613 with all18 host-dependent
checks configured; hosted baseline skips those18. Rollout evidence is recorded separately.

RU/UZ quality, accents/noise and an actual owner Telegram voice -> preview -> confirmation
still require a genuine recording after activation. The first-sample request is sent only
once via the owner's notification inbox. Keep stage10 in progress until the actual acceptance
gate is observed; do not report these synthetic cases as the owner's action or approval.
