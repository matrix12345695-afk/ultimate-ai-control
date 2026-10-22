# Render deployment readiness (NOT DEPLOYED)

The render.yaml file is a deployment reference. Its worker plan may incur costs and MUST NOT be applied until the owner approves the exact price and configuration.

Prerequisites:
1. Move the GitHub repository to Private and protect main branch with required CI and pull request reviews.
2. Choose an always-on hosting tier, verify current pricing.
3. Arrange persistent data storage: do not rely on ephemeral SQLite on Render worker.
4. Supply TELEGRAM_BOT_TOKEN and ADMIN_TELEGRAM_ID as protected environment variables through Render UI, never in GitHub or chat.
5. Keep AI_ENABLED=false and zero budget. Do not connect AI_API_KEY yet.
6. Test startup and health, then verify Telegram private-chat admin access.
7. Add backups and restore checks before accepting real workloads.

Do not enable automatic deployments of unreviewed main-branch changes.
