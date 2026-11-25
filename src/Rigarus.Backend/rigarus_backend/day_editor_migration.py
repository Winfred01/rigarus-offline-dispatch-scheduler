"""Additive durable operation receipts; never rewrite scheduling facts."""

DAY_EDITOR = "20261125040000_AddDayEditorReceipts"
DAY_EDITOR_TABLES = {"DayEditorWorkspace", "DayEditorReceipts"}
CREATE_DAY_EDITOR = (
    """CREATE TABLE DayEditorWorkspace (
        Id INTEGER PRIMARY KEY CHECK(Id=1),
        ProfileId TEXT NOT NULL UNIQUE CHECK(length(ProfileId)=36)
    )""",
    """CREATE TABLE DayEditorReceipts (
        RequestId TEXT PRIMARY KEY CHECK(length(RequestId)=36),
        PayloadSha TEXT NOT NULL CHECK(length(PayloadSha)=64),
        ResultJson TEXT NOT NULL CHECK(json_valid(ResultJson)),
        RecordedAt TEXT NOT NULL
    )""",
    *tuple(
        f"CREATE TRIGGER {table}_No{action.title()} BEFORE {action} ON {table} "
        "BEGIN SELECT RAISE(ABORT,'Day editor identity and receipts are immutable.'); END"
        for table in ("DayEditorWorkspace", "DayEditorReceipts")
        for action in ("UPDATE", "DELETE")
    ),
)
