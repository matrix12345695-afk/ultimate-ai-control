# Independent contracts for reviewed recipes

The queue's existing safe-paths and sha-check recipes now have separate first-party behavioral
contracts: review-path-v1 and git-commit-v1. Each has eight tests, beyond the candidate's own
three path tests or two commit tests. The prior bounded-percent-v1 demonstration retains its exact original seven-test
harness and hash; existing demo artifacts remain recoverable without a changed contract.

The path contract checks permitted namespaces, traversal/empty components, separators,
case-insensitive sensitive words, the 120-character suffix bound, ASCII/full-string matching
and wrong types. This is the existing conservative recipe policy, not a new deployment scope.
The commit contract checks exact lowercase hexadecimal SHA-1 identifiers, length, characters,
whitespace, Unicode lookalikes, types and accidental path/ref input.
These are lexical checks: they do not prove filesystem/symlink safety, commit existence,
repository ownership or publication authorization. Those require their separate existing gates.

The trusted recipe name determines the acceptance profile. Candidate code or tests cannot
choose or disable it. The engine/profile pairing is checked; arbitrary model output does not
inherit a demo or recipe contract. These are reviewed narrow contracts, not a general grader
for every free-text task or project. Other language/framework/business acceptance remains
unfinished, and the paid model remains disabled by the owner's deferral.

Acceptance runs in its own network-free Bubblewrap namespace. It receives only one matching
recipe source module and the first-party test file. Candidate tests, package initializers,
shadow modules and extra source files are excluded. The selected module has an AST gate for
the reviewed function signature, re import, regex/blocked-word constants and stateless helper
operations. Imports, module-level side effects, nested functions, dunder access and global
rebinding are rejected. Each phase has eight seconds, within the existing worker deadline.

Both phases must pass. A failed, timed-out or invalid acceptance report produces a failed
artifact/job and a critical notification; it never becomes owner-ready. Reports bind the
original source manifest, acceptance bundle digest, profile and harness SHA-256. Crash recovery
validates the matching profile's harness and reuses the complete report without re-execution.
Changed requirements/source/evidence fail closed. Old recipe artifacts without independent
acceptance stay legacy; a retry cannot silently upgrade them or assign a new passed contract.

`/acceptance4` and the Acceptance button show all three reviewed profiles, test counts, hashes
and passed artifact counts. Plan4.0 marks this component verified while stage5 stays active.
No publication, source adoption, other-project access or new schedule is granted.

Tests prove namespace separation, AST rejection, profile/engine boundaries, failed-phase gates,
digest binding, recovery, legacy preservation and real sandbox rejection of four mutations:
always-allow paths, removed sensitive-word protection, nonempty-string commits and uppercase
commit acceptance. Their deliberately inadequate candidate tests pass; independent tests fail.
Artificial runner fixtures remain explicitly labeled. VPS/Telegram evidence is recorded in
PROJECT_STATUS.md only after actual rollout and real queued recipe tests.
