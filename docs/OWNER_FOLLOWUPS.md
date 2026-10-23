# Owner follow-ups without repeated setup requests

The owner asked to continue independent work and retain their actions for later. `/owner_later`
and the `📌 Для владельца` button provide a paginated view backed by the existing SQLite inbox
and owner settings. They never generate a model answer, notification, payment, approval or
schedule. Four actionable items per page keep all pending decisions reachable without message
truncation. Critical requests precede decisions; informational updates are excluded.

`/owner_item ID` shows a full bounded request, original reason/action, task, timestamps and
delivery receipt. A receipt does not prove reading or authorize an action. Closed records
remain inspectable. The two known API setup requests display as deferred while the persisted
owner deferral is active; they are not presented as completed provisioning. All other resolved
records retain the neutral journal status without inferring approval or deployment.

The API deferral is shown separately from active requests. No key is requested, read or
installed. A missing return-chat URL appears as an optional future step, never as an obstacle
to independent operations. An existing URL suppresses that optional reminder. This feature
does not give the VPS access to new ChatGPT messages.

The list is a read-only projection of existing durable state, so reopening the bot or database
retains pending and deferred actions. Viewing it neither resolves notes nor changes delivery,
queue state or provider policy. Critical incidents remain visible; a general promise to act
later does not silently defer every critical request. Publication decisions still require the
separate exact project/version/digest gate. No new owner deferral or approval command is added.

Tests cover pagination without missing/duplicate requests, priority, bounded Telegram output,
full action detail, persisted deferral/receipts after reopening, malformed/oversized IDs and
read-only behavior. Plan4.0 reports this verified component without completing the whole
memory stage. Server evidence belongs in PROJECT_STATUS.md after actual rollout.
