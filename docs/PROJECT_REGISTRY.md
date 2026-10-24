# Pinned public source registry

`project_registry.py` defines read scopes for NOVA WEB and the Kinder Spa Android scaffold.
Identity is bound to GitHub's numeric repository and owner IDs, exact full names and public,
non-fork visibility. Revisions are immutable reviewed commit IDs. Four NOVA files and two
Kinder documentation files have fixed paths, byte lengths and Git blob IDs; all bytes must
match. Changes to the public main branch do not silently expand the accepted scope.

`/projects4` and the Projects menu show the scopes and the last valid committed queue result.
`/repo_check nova` or `/repo_check kinder` creates a typed inspect_repository job. The input
cannot select a URL, ref, repository, extra path or secret file. Inventory and Mini App remain
denied; projects without verified mappings remain unavailable to this handler. Existing
ULTIMATE local source inspection stays separate.

The worker performs only bounded HTTPS GETs: one GitHub metadata request, then the exact
allowlisted raw files at the pinned commit. It sends no authorization header and reads no
credential environment variable. Redirects and compressed/oversized responses are rejected.
Each request is at most five seconds, the total observation budget eighteen seconds, metadata
at most 64 KiB and each source response at most its exact reviewed byte length plus one.
TLS and inherited network proxy settings stay intact. Rate limits and transport errors use
the existing finite queue retries. Identity/hash/scope violations fail permanently and create
an owner critical notification without copying untrusted source or response payloads into it.

Source bytes exist only in memory. The journal saves paths, sizes, Git blob IDs, SHA-256
fingerprints, a manifest digest and limited manifest facts. It does not save source text,
customer records, configuration, scripts or arbitrary provider responses. Package scripts,
build hooks and repository code are never executed. No checkout, dependency installation,
project write, deployment or new schedule is performed.

Results explicitly state code_executed=false, tests_executed=false, published=false and
complete_project_audit=false. Finding a test script is not running it. Kinder documentation
is not an Android build or backend. A repository commit is not proof of the deployed website
version. Plan4.0 counts only valid committed observations and keeps stage7 active while wider
project mappings, isolated execution, change preparation and approvals remain unfinished.

Local real GETs verified NOVA source digest
`7b94e668d1ef836d6aa94b7cc70a5abf48f091fce2b026e01389281cbee9c094` and Kinder digest
`67a196b9a3835e49ad8fa4e6e1e7fc570727305de11179006e1510b37627ccd9`.
Server rollout and live queue evidence will be recorded in PROJECT_STATUS.md after verification.
