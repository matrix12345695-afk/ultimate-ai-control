# Outbound-only HTTPS channel (v3.6)

Code status: adapter and mocked tests only. No mailbox endpoint or live channel is provisioned.

Both Render and VPS may make outbound HTTPS connections to an independently hosted mailbox. The mailbox holds encrypted-at-rest, short-lived signed handoff envelopes and signed receipts; it must not hold private GitHub keys or Telegram tokens.

Security requirements:
- Separate authenticated producer/consumer identities for mailbox access, in addition to signed envelopes and receipts.
- TLS certificate validation, rate limits, strict size limits and no request-content logging.
- A persistent replay database on VPS. Do not retry remote GitHub writes after an unknown outcome.
- VPS verifies envelope signatures and immutable hashes before executing; Render verifies signed receipt.
- Mailbox deletion/ack must not be mistaken for actual PR creation or a successful Telegram delivery.
- Never enable endpoint via unreviewed environment variables. Keep REVIEW_EXECUTOR_ENABLED=false.
- Not yet implemented: actual mailbox service, access control, durable acknowledgement, retries and live verification.

No new public inbound VPS port or Render deployment is needed for these source-only changes.
