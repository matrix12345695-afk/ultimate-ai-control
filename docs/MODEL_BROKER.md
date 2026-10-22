# Developer broker and durable two-job pipeline

The broker is a short-lived Python subprocess with a narrow JSON protocol. The operations
worker sends only a protocol identifier, job ID and current lease token. Task text, project
and permissions are checked against the existing database, rather than accepted as arbitrary
process commands. Only an active control/review_change job owned by operations-1 with enough
lease time is authorized. Inventory and other project generation are not enabled.

## Execution path

1. /develop control TEXT creates a typed generation job. /developer_demo creates only the
   known demonstration job; ordinary requests cannot silently become that demonstration.
2. broker_client starts model_broker.py with a clean environment and bounded pipe protocol.
   It passes no Telegram token, API key, PYTHONPATH, command, endpoint or key path.
3. The broker checks lease, pause state, typed payload and private broker policy. Actual model
   calls need enabled=true and allow_paid=true, plus an enabled priced provider policy and a
   separate owner-private key at ~/.config/ultimate-review/openai-api.key. Both policies are
   installed disabled. The demo requires allow_demo=true and uses fixed source from this repo.
4. OpenAI receives only the bounded task and fixed Python-bundle instructions, with no tools.
   The existing $30 reservation/receipt guard remains mandatory. A stable developer-bundle:ID
   request key survives worker retries. Credentials and lease tokens never enter the prompt.
5. The broker accepts strict JSON with summary and files only. Duplicate fields, secret
   patterns, traversal, non-Python paths, missing test methods, bad syntax, oversized bundles
   and unexpected fields are rejected. It parses ASTs but never executes the generated code.
6. A bounded source capsule and its SHA-256 are persisted. Generation completion and creation
   of its test job are committed atomically. No passing test or publication is inferred here.
7. A later queue tick checks the committed parent-child binding and capsule digest, then runs
   exactly that bundle through the existing network-free Bubblewrap test runner. Code, manifest,
   report and provenance are saved privately. Passed drafts await owner review; failed tests
   fail the job and produce a critical notice. The source is never installed into a project.

The generation process has a 23-second parent deadline and bounded output. Tests run in a
separate job with their existing 20-second deadline, so the stages do not share one worker
tick deadline. Global queue concurrency and pause controls still apply. Work intervals are
measured separately for generation and testing; no imaginary parallel agent time is reported.

## Boundaries and recovery

The broker limits address space to 256 MiB, CPU to 12 seconds and descriptors to 64, disables
core dumps and process dump access, and requests death if its parent exits. Only the broker
code opens the private model key. Its stdout carries a checked source capsule or a short error
code; raw HTTP errors, prompts and credentials are not printed. Timeouts/protocol failures
stop that generation job without automatic paid retries. Ambiguous API holds remain frozen.

A completed paid response can be reused if a crash occurs before source staging. A persisted
capsule can be replayed after a generation-worker restart. Its original job identity, input
digest and source digest are checked. A follow-up job cannot be detached from its successful
generation parent or changed to another bundle. Each test artifact records the parent job,
provider request key, model and measured generation time.

The trusted processes still share one Linux user. A private file plus a separate process is
logical credential separation, not an OS boundary against other same-UID host processes.
The existing untrusted-code sandbox has no host home/configuration mounts; it never receives
the key. Broader agent host permissions, native dependencies, browser execution and a stronger
credential boundary remain separate work. No new sudo rights, users, Docker access or shared
service changes are part of this increment.

The component's own generated tests are evidence of executing those tests, not independent
proof that an arbitrary user request is satisfied. Independent acceptance tests and review
remain necessary before publication. No merge, deployment, permission change or commercial
action is authorized by a model response or passing draft test.

## Current mode and commands

The installed policy is {"enabled":false,"allow_paid":false,"allow_demo":true}. Actual model
and billing access remain unverified until private setup. The fixed demo is explicitly marked
offline_broker_demo and uses no LLM. It proves orchestration, isolation, artifacts and owner
notification, not general AI coding quality. General /work and free text retain their previous
safe waiting behavior; only /develop control submits this initial model-developer request.

- /broker4: policy and capsule status without opening a key.
- /developer_demo: known component -> separate sandbox tests -> artifact -> owner notice.
- /develop control TEXT: model draft request, waiting when private policies are disabled.
- /artifact ID and /artifact_code ID INDEX: review the exact tested draft.

The model provider status now reports whether both queue policies permit calls; it explicitly
does not claim key/account readiness. No chat command enables paid policy or accepts a key.
The price catalog and conservative financial contract in METERED_PROVIDER.md still apply.
