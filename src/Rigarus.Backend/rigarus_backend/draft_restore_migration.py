"""Independent immutable inverse versions/receipts; original versions stay intact."""

DRAFT_RESTORE = "20261127010000_AddDraftRestoreVersions"
DRAFT_RESTORE_TABLES = {"DraftRestoreVersions", "DraftRestoreReceipts"}
CREATE_DRAFT_RESTORE = (
    """CREATE TABLE DraftRestoreVersions (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        SourceDraftVersionId INTEGER NOT NULL REFERENCES DraftVersions(Id) ON DELETE RESTRICT,
        ProfileId TEXT NOT NULL REFERENCES DayEditorWorkspace(ProfileId) ON DELETE RESTRICT,
        RequestId TEXT NOT NULL UNIQUE CHECK(length(RequestId)=36),
        PlanSha TEXT NOT NULL CHECK(length(PlanSha)=64),
        ResultJson TEXT NOT NULL CHECK(json_valid(ResultJson)),
        RecordedAt TEXT NOT NULL
    )""",
    """CREATE TABLE DraftRestoreReceipts (
        RequestId TEXT PRIMARY KEY NOT NULL CHECK(length(RequestId)=36),
        PayloadSha TEXT NOT NULL CHECK(length(PayloadSha)=64),
        ProfileId TEXT NOT NULL REFERENCES DayEditorWorkspace(ProfileId) ON DELETE RESTRICT,
        SourceDraftVersionId INTEGER REFERENCES DraftVersions(Id) ON DELETE RESTRICT,
        RestoreVersionId INTEGER UNIQUE REFERENCES DraftRestoreVersions(Id) ON DELETE RESTRICT,
        ResultJson TEXT NOT NULL CHECK(json_valid(ResultJson)),
        RecordedAt TEXT NOT NULL
    )""",
    *tuple(
        f"CREATE TRIGGER {table}_No{action.title()} BEFORE {action} ON {table} "
        "BEGIN SELECT RAISE(ABORT,'Draft restore audit/receipts are immutable.'); END"
        for table in ("DraftRestoreVersions", "DraftRestoreReceipts")
        for action in ("UPDATE", "DELETE")
    ),
)
