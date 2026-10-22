# Durable task queue: foundation

This is an unactivated library increment. It does not execute tasks, start agents, publish code,
change permissions or make API calls. The installed notifications dispatcher remains unchanged.

task_queue.py stores jobs, lease tokens, bounded attempts, retries and lifecycle events in SQLite.
Independent workers serialize claims with BEGIN IMMEDIATE. Default concurrency is one;
the configurable upper bound is three, subject to later host load testing. A worker can hold
one job at a time. Expired leases are recovered and old workers cannot complete reclaimed work.

An awaiting_owner job releases its slot. Other projects can continue independently.
Pausing the queue prevents claims; running workers learn the pause flag through heartbeat
and must stop at a safe boundary. Cancellation only affects queued/awaiting jobs.
There are no operating-system kill operations and Inventory is not an enabled queue project.

Work spans are supplied by trusted workers from measured execution, testing or waiting intervals.
Reports clip them to the requested UTC interval, reject overlaps, and include failed attempts.
Missing measurements remain unknown. Time spent holding a lease is never reported as active work.

Before activation, add isolated typed workers, an authenticated Telegram adapter, CPU/RAM/time
limits, atomic blocker notifications, shutdown checkpoints and provider cost accounting.
Do not connect a generic shell executor or point any worker at /home/maksim/inventory-bot.

Validation: full suite 226 tests, including concurrent claims from four SQLite connections,
cross-worker concurrency, lease replay, crash recovery, retry exhaustion, emergency pause,
independent work while approval is pending, and measured-time clipping.
