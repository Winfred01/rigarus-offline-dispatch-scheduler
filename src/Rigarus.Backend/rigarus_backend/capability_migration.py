"""Additive schema twelve for explicit dated requirements and qualification evidence."""

CAPABILITY_EVIDENCE = "20261124020000_AddCapabilityEvidence"
CAPABILITY_TABLES = {
    "CapabilityEvidenceOwners",
    "CapabilityEvidenceChanges",
    "CapabilityEvidenceCells",
}
CREATE_CAPABILITY_EVIDENCE = (
    """CREATE TABLE CapabilityEvidenceOwners (
        Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        WorkItemId INTEGER UNIQUE REFERENCES WorkItems(Id) ON DELETE RESTRICT,
        EmployeeId INTEGER REFERENCES Employees(Id) ON DELETE RESTRICT,
        Code TEXT NOT NULL,
        CHECK ((WorkItemId IS NOT NULL AND EmployeeId IS NULL AND Code='')
          OR (WorkItemId IS NULL AND EmployeeId IS NOT NULL AND length(Code) BETWEEN 1 AND 50)),
        UNIQUE(EmployeeId,Code)
    )""",
    """CREATE TABLE CapabilityEvidenceChanges (
        Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        OwnerId INTEGER NOT NULL REFERENCES CapabilityEvidenceOwners(Id) ON DELETE RESTRICT,
        Revision INTEGER NOT NULL CHECK(typeof(Revision)='integer' AND Revision>0),
        StartDate TEXT NOT NULL CHECK(length(StartDate)=10 AND StartDate IS strftime('%Y-%m-%d',StartDate,'+0 days') AND substr(StartDate,1,4) BETWEEN '0001' AND '9999'),
        EndDate TEXT NOT NULL CHECK(length(EndDate)=10 AND EndDate IS strftime('%Y-%m-%d',EndDate,'+0 days') AND substr(EndDate,1,4) BETWEEN '0001' AND '9999' AND EndDate>=StartDate),
        Slot TEXT NOT NULL CHECK(Slot IN ('AM','PM','FullDay')),
        Payload TEXT NOT NULL CHECK(length(Payload) BETWEEN 1 AND 20000 AND instr(Payload,char(0))=0),
        CompanyConfirmed INTEGER NOT NULL CHECK(CompanyConfirmed=1),
        Reference TEXT NOT NULL CHECK(length(trim(Reference)) BETWEEN 1 AND 200 AND instr(Reference,char(0))=0),
        RecordedAt TEXT NOT NULL,
        UNIQUE(OwnerId,Revision), UNIQUE(Id,OwnerId)
    )""",
    """CREATE TABLE CapabilityEvidenceCells (
        OwnerId INTEGER NOT NULL REFERENCES CapabilityEvidenceOwners(Id) ON DELETE RESTRICT,
        LocalDate TEXT NOT NULL CHECK(length(LocalDate)=10 AND LocalDate IS strftime('%Y-%m-%d',LocalDate,'+0 days') AND substr(LocalDate,1,4) BETWEEN '0001' AND '9999'),
        Slot TEXT NOT NULL CHECK(Slot IN ('AM','PM')),
        ChangeId INTEGER NOT NULL,
        PRIMARY KEY(OwnerId,LocalDate,Slot),
        FOREIGN KEY(ChangeId,OwnerId) REFERENCES CapabilityEvidenceChanges(Id,OwnerId) ON DELETE RESTRICT
    )""",
    *tuple(
        f"CREATE TRIGGER {table}_No{action.title()} BEFORE {action} ON {table} "
        "BEGIN SELECT RAISE(ABORT,'Capability ownership/history is immutable.'); END"
        for table in ("CapabilityEvidenceOwners", "CapabilityEvidenceChanges")
        for action in ("UPDATE", "DELETE")
    ),
)
