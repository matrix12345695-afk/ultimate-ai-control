# ULTIMATE AI CONTROL
Autonomous Telegram control-plane starter. Python 3.11+, standard library only.

**This is an MVP, not yet a self-directed AI agent.** It stores tasks, checks HTTPS websites and responds to administrator commands. It does not execute project tasks, deploy code, mutate project data or use paid APIs.

## Configuration
Copy `.env.example` to `.env` on a trusted runtime; never commit .env or bot tokens. Variables:
- TELEGRAM_BOT_TOKEN: token of a NEW bot from BotFather.
- ADMIN_TELEGRAM_ID: numeric Telegram user ID.
- MONITOR_URLS: comma-separated trusted HTTPS URLs.
- DB_PATH: database file location (optional).

Load environment variables before starting `python3 main.py`. The sample `systemd` unit loads .env on Ubuntu when installed in /opt/ultimate-ai-control.

Commands: /start /help /status /projects /check /tasks /task nova Check website

## Safety
Only the configured numeric admin ID, in Telegram private chat, may interact. No arbitrary shell execution. No live project credentials in repository. Monitor only URLs you own. Backup the SQLite data directory. GitHub alone does not host an always-running Telegram bot.

## Next milestones
1. Dedicated 24/7 hosting, secure secret storage, structured audit log and backups.
2. Read-only GitHub/Render/site adapters.
3. Explicit approval workflow for deploying changes.
4. Optional AI model provider with budget limits and opt-in credentials.
