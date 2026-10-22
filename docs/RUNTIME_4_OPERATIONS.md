# ULTIMATE 4.0 operations increment

## Real capabilities

The persistent scheduler enqueues NOVA WEB availability checks every 15 minutes, a daily AST
inspection of ULTIMATE's own source, and a daily report at 09:00 UTC. Catch-up is bounded;
event keys prevent duplicate schedule jobs after restart. SQLite stores leases, results,
measured work intervals, state transitions and delivery receipts. Default concurrency is one.
The worker uses a 384 MiB address-space limit, 128 descriptors, lowered priority and a
30-second tick timeout. It has no bot token and never polls Telegram or executes project code.
The existing authenticated dispatcher remains the sole Telegram polling process.

The 16-stage roadmap, owner policies and all nine project descriptions are seeded into the
ULTIMATE database, preserving existing records. Completion states require inspectable evidence.
Only explicitly tested stages are marked complete. Windows UI automation is unavailable on Ubuntu.
Inventory and its Mini App are protected from worker access.

## Telegram

/start refreshes the menu. /roadmap, /queue, /agents, /daily, /memory <project>, /budget4,
/project <name>, /work <project> <task>, /job <id>, /job_cancel <id>, /pause and /resume
operate on the new runtime. Legacy /task and /tasks remain a separate historical queue.
Plain owner text is queued for the selected project. The Telegram update ID is its idempotency
key. Commands are accepted only from the configured owner in a private conversation.
Voice input currently receives an explicit unsupported-feature response.

/chat_bind stores an owner-supplied private chatgpt.com conversation URL. Notifications can
then include an inline return button. /chat_link explains this association. It does not grant
the bot access to ChatGPT, read new chat messages, write replies or resume Codex automatically.
The current handover and instruction are explicitly imported during rollout. Future chat tasks
can be imported through the bounded bridge action by the active assistant. ChatGPT does not
expose a conversation subscription to this server.

## Financial gate and pending execution

The new ledger uses integer micro-USD, BEGIN IMMEDIATE reservations, a fixed $30/month maximum,
attribution and usage settlement. Uncertain requests keep their reservation. The unmetered
legacy HTTP model adapter is disabled. No priced provider transport or key is enabled.
General code-writing jobs wait for an isolated model executor; they are not reported as complete.
This blocker generates one persistent owner decision notification, while operational checks
continue. Speech, arbitrary code generation, isolated test workers and controlled publication
remain roadmap work. Do not describe this increment as a complete autonomous AI company.

## Host supervision and rollback

Keep the existing ULTIMATE dispatcher supervisor. Add only an isolated ULTIMATE scheduler
supervisor with its own lock, log, activation marker and cron line. Its environment contains
only HOME, PATH, LANG and DB_PATH, without Telegram/GitHub/model credentials.
Back up the DB using SQLite's backup API and verify a restored copy before migration.
Pinned source tests run with a temporary HOME/DB and no credentials.
On rollback, remove only the ULTIMATE scheduler cron entry and activation marker, terminate only
its exact worker/supervisor processes, restore the prior code SHA and restart only ULTIMATE.
Additive tables stay in place to preserve tasks and notification history. Inventory's standard
deploy/start/stop/restart actions must never be used for this rollout.
