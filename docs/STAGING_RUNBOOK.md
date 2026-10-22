# VPS staging execution

**Never run this without inspecting it.** This installer creates a dedicated
system identity and isolated staging checkout on existing Ubuntu 22.04.
It does not configure GitHub credentials, start an executor or modify Render.

1. SSH into the VPS using your own administrator session.
2. Download or review `deploy/setup_vps_staging.sh` from the feature branch.
3. Verify the code and execute `sudo bash deploy/setup_vps_staging.sh` from a local working copy.
4. Review unit test results. On failure stop; do not proceed to credentials.
5. Do not turn on the systemd unit in this branch: it is a testing placeholder, not an actual executor.
6. Do not share private PEM content, access tokens or passwords in chat.
7. Use a separate follow-up security review to provision GitHub App token issuance, mailbox TLS and approval transport before any actual GitHub writes.

Known blockers: GitHub App authentication implementation and secure delivery channel are not live;
the mailbox API is not deployed; trusted Render approval messages are not transferred.
