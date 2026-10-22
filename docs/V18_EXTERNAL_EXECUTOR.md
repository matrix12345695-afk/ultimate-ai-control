# v1.8 external Draft PR adapter

The pure adapter accepts a separately supplied narrow GitHub client. It verifies content hashes and base commit, creates a review branch and Draft PR, never merges or deploys. No GitHub client credentials or autonomous worker installed; production bot does not call this adapter. The boolean approved argument is NOT a substitute for authenticating the approval record. A secure independent runner, exact repository allowlist, post-write verification, failure reconciliation, and protected CI permissions are required before enabling actual writes.
