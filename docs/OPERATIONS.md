# v1.0 operations

- Daily local SQLite snapshots are verified by restoring to an in-memory database.
- Seven local backups retained (not offsite; disk failure can destroy them all).
- New /backups command reports only local copy count.
- Telegram error alert cooldown is 1 hour per category.
- An external encrypted backup destination remains mandatory before treating this as complete disaster recovery.
- This branch is a CI review candidate only. Do not deploy without owner approval.
