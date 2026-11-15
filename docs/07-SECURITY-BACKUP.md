# Local data and backup

Runtime data belongs to the operator's local Windows profile. Keep the database, its WAL sidecars, attachments and diagnostic files out of GitHub and shared demo packages. Commit fictional source fixtures only. The CI privacy gate checks tracked paths and common secret formats. Review staged text and synthetic inputs for customer information as well.

Future backup and restore work must use a consistent SQLite snapshot and include attachments, schema version and hashes. Verify before replacing files, keep a pre-restore copy, and preserve the ability to roll back. Copying an active WAL-mode database file on its own can omit recent changes. M0 provides a disposable synthetic database and does not implement backup or restore.

The [proposed SQLite backup and restore ADR](adr/ADR-002-sqlite-backup-restore.md) defines the maintenance boundary, archive format, recovery procedure and M7 test matrix.
