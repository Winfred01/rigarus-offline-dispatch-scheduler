"""Additive immutable transaction receipt; never converts historical visits."""

DRAFT_VERSIONS = "20261126010000_AddDraftVersions"
DRAFT_VERSION_TABLES = {"DraftVersions"}
CREATE_DRAFT_VERSIONS = (
    """CREATE TABLE DraftVersions (
        Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        RequestId TEXT NOT NULL UNIQUE CHECK(length(RequestId)=36),
        PayloadSha TEXT NOT NULL CHECK(length(PayloadSha)=64),
        ProfileId TEXT NOT NULL CHECK(length(ProfileId)=36),
        PlanSha TEXT NOT NULL CHECK(length(PlanSha)=64),
        ResultJson TEXT NOT NULL CHECK(json_valid(ResultJson)),
        RecordedAt TEXT NOT NULL,
        FOREIGN KEY(ProfileId) REFERENCES DayEditorWorkspace(ProfileId) ON DELETE RESTRICT
    )""",
    *tuple(
        f"CREATE TRIGGER DraftVersions_No{action.title()} BEFORE {action} ON DraftVersions "
        "BEGIN SELECT RAISE(ABORT,'Draft versions are append-only.'); END"
        for action in ("UPDATE", "DELETE")
    ),
)
