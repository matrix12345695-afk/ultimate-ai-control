# Independent acceptance of the progress demo

The offline progress demo now runs two suites in separate Bubblewrap namespaces. Its own
four tests run first. If those pass, a reviewed seven-test contract from acceptance_checks.py
checks the exact draft_component.py source without importing any candidate tests or other
candidate modules. Each run has an eight-second deadline inside the worker's existing
30-second tick. Network, processes, threads and host credentials remain unavailable.

The fixed contract bounded-percent-v1 covers zero, integer floor rounding, completion/capping,
large integers, invalid bounds, strict integer types, range and monotonicity. Candidate code
must be exactly one pure bounded_percent(done,total) function within a narrow AST allowlist:
no imports, attributes, decorators, recursion, arbitrary calls, assignments or loops. The host
only parses source; execution remains inside Bubblewrap. This restriction applies only to
the small reviewed demo contract, not general-purpose Python development.

The second bundle contains only the selected component and first-party acceptance suite.
Candidate test code cannot patch its unittest or shadow a standard module. The stored report
includes both suite outcomes, candidate capsule SHA-256, acceptance bundle digest, profile and
harness SHA-256. Artifact replay verifies the exact capsule, engine, profile and harness.
An acceptance failure, timeout or source-contract refusal makes the artifact and queue job
failed, preserves the report and produces a critical owner notice rather than owner-ready
status. Publication is never performed by either suite.

Legacy artifacts retain their original evidence. They are not retroactively called
independently verified. General OpenAI bundles report not_configured for independent
acceptance: a custom reviewed contract must be added before claiming those requests satisfy
owner requirements. This increment does not provision a key or enable paid policies.

Validation includes three incorrect implementations (constant output, missing cap and ceil
rounding) whose own artificial tests return success after patching unittest assertions. Their
independent suites fail in fresh real Bubblewrap namespaces. Additional tests cover source
side effects, shadow modules, digest/profile/harness mismatch, failed/timed-out acceptance,
artifact replay and worker failure/critical notification behavior. Artificial fixture reports
are labeled as such; the real mutation tests are enabled only with UAC_SANDBOX_TEST_BINARY.
