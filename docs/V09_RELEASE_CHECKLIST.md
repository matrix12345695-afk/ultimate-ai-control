# v0.9 Telegram menu release checklist

- [ ] CI unit tests pass on candidate commit
- [ ] Verify private-admin-only behavior
- [ ] Confirm the keyboard is shown by /start
- [ ] Check /status and /projects
- [ ] Confirm secrets remain in Render environment only
- [ ] Obtain owner approval of deployment
- [ ] Trigger Render deploy with auto-deploy disabled
- [ ] Verify runtime logs and Telegram responses

Deployment must not be performed automatically by this PR. Existing production is v0.8 until a new deployment is verified.
