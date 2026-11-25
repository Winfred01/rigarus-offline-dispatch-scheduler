"""Independent slotless company assertions; never convert legacy approvals."""

DAILY_DRIVERS = "20261124050000_AddDailyDriverApprovals"
DAILY_DRIVER_TABLES = {"DailyDriverApprovalChanges", "DailyDriverApprovalCells"}
CREATE_DAILY_DRIVERS = (
    """CREATE TABLE DailyDriverApprovalChanges (
      Id INTEGER PRIMARY KEY AUTOINCREMENT,
      EmployeeId INTEGER NOT NULL REFERENCES Employees(Id) ON DELETE RESTRICT,
      Revision INTEGER NOT NULL CHECK(typeof(Revision)='integer' AND Revision>0),
      StartDate TEXT NOT NULL CHECK(length(StartDate)=10 AND substr(StartDate,1,4) BETWEEN '0001' AND '9999' AND StartDate IS strftime('%Y-%m-%d',StartDate,'+0 days')),
      EndDate TEXT NOT NULL CHECK(length(EndDate)=10 AND substr(EndDate,1,4) BETWEEN '0001' AND '9999' AND EndDate IS strftime('%Y-%m-%d',EndDate,'+0 days') AND EndDate>=StartDate),
      State TEXT NOT NULL CHECK(State IN ('Unverified','Active','Suspended','Expired')),
      CompanyConfirmed INTEGER NOT NULL CHECK(CompanyConfirmed=1),
      FullDayConfirmed INTEGER NOT NULL CHECK(FullDayConfirmed=1),
      LegacyReviewed INTEGER NOT NULL CHECK(LegacyReviewed IN (0,1)),
      LegacyRevision INTEGER NOT NULL CHECK(typeof(LegacyRevision)='integer' AND LegacyRevision>=0),
      LegacySnapshot TEXT NOT NULL CHECK(length(LegacySnapshot)<=250000),
      Reference TEXT NOT NULL CHECK(length(trim(Reference)) BETWEEN 1 AND 200 AND instr(Reference,char(0))=0),
      Notes TEXT NOT NULL CHECK(length(Notes)<=2000 AND instr(Notes,char(0))=0),
      RecordedAt TEXT NOT NULL,
      UNIQUE(EmployeeId,Revision), UNIQUE(Id,EmployeeId,State)
    )""",
    """CREATE TABLE DailyDriverApprovalCells (
      EmployeeId INTEGER NOT NULL REFERENCES Employees(Id) ON DELETE RESTRICT,
      LocalDate TEXT NOT NULL CHECK(length(LocalDate)=10 AND substr(LocalDate,1,4) BETWEEN '0001' AND '9999' AND LocalDate IS strftime('%Y-%m-%d',LocalDate,'+0 days')),
      State TEXT NOT NULL, ChangeId INTEGER NOT NULL,
      LegacyFingerprint TEXT NOT NULL CHECK(length(LegacyFingerprint)=64 AND LegacyFingerprint NOT GLOB '*[^0-9a-f]*'),
      PRIMARY KEY(EmployeeId,LocalDate),
      FOREIGN KEY(ChangeId,EmployeeId,State) REFERENCES DailyDriverApprovalChanges(Id,EmployeeId,State) ON DELETE RESTRICT
    )""",
    "CREATE INDEX IX_DailyDriverApprovalCells_Date ON DailyDriverApprovalCells(LocalDate,EmployeeId)",
    *tuple(
        f"CREATE TRIGGER DailyDriverApprovalChanges_No{action.title()} BEFORE {action} ON DailyDriverApprovalChanges "
        "BEGIN SELECT RAISE(ABORT,'Daily driver history is immutable.'); END"
        for action in ("UPDATE", "DELETE")
    ),
    *tuple(
        f"CREATE TRIGGER DailyDriverApprovalCells_Context{action.title()} BEFORE {action} ON DailyDriverApprovalCells "
        "WHEN NOT EXISTS(SELECT 1 FROM DailyDriverApprovalChanges h WHERE h.Id=NEW.ChangeId AND h.EmployeeId=NEW.EmployeeId AND h.State=NEW.State AND NEW.LocalDate BETWEEN h.StartDate AND h.EndDate) "
        "BEGIN SELECT RAISE(ABORT,'Daily driver cell history context mismatch.'); END"
        for action in ("INSERT", "UPDATE")
    ),
)
