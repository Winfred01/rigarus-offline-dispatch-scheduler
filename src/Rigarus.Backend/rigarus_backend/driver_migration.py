"""Additive schema eleven, preserving the Unverified employee-roster invariant."""

DRIVER_APPROVALS = "20261124010000_AddDriverApprovals"
DRIVER_TABLES = {"DriverApprovalChanges", "DriverApprovalCells"}
CREATE_DRIVER_APPROVALS = (
    """CREATE TABLE DriverApprovalChanges (
        Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        EmployeeId INTEGER NOT NULL REFERENCES Employees(Id) ON DELETE RESTRICT,
        Revision INTEGER NOT NULL CHECK(typeof(Revision)='integer' AND Revision>0),
        StartDate TEXT NOT NULL CHECK(length(StartDate)=10 AND StartDate IS strftime('%Y-%m-%d',StartDate,'+0 days') AND substr(StartDate,1,4) BETWEEN '0001' AND '9999'),
        EndDate TEXT NOT NULL CHECK(length(EndDate)=10 AND EndDate IS strftime('%Y-%m-%d',EndDate,'+0 days') AND substr(EndDate,1,4) BETWEEN '0001' AND '9999' AND EndDate>=StartDate),
        Slot TEXT NOT NULL CHECK(Slot IN ('FullDay','AM','PM')),
        State TEXT NOT NULL CHECK(State IN ('Unverified','Active','Suspended','Expired')),
        CompanyConfirmed INTEGER NOT NULL CHECK(CompanyConfirmed=1),
        Reference TEXT NOT NULL CHECK(length(trim(Reference)) BETWEEN 1 AND 200 AND instr(Reference,char(0))=0),
        RecordedAt TEXT NOT NULL,
        UNIQUE(EmployeeId,Revision), UNIQUE(Id,EmployeeId,State)
    )""",
    """CREATE TABLE DriverApprovalCells (
        EmployeeId INTEGER NOT NULL REFERENCES Employees(Id) ON DELETE RESTRICT,
        LocalDate TEXT NOT NULL CHECK(length(LocalDate)=10 AND LocalDate IS strftime('%Y-%m-%d',LocalDate,'+0 days') AND substr(LocalDate,1,4) BETWEEN '0001' AND '9999'),
        Slot TEXT NOT NULL CHECK(Slot IN ('AM','PM')),
        State TEXT NOT NULL CHECK(State IN ('Unverified','Active','Suspended','Expired')),
        ChangeId INTEGER NOT NULL,
        PRIMARY KEY(EmployeeId,LocalDate,Slot),
        FOREIGN KEY(ChangeId,EmployeeId,State)
            REFERENCES DriverApprovalChanges(Id,EmployeeId,State) ON DELETE RESTRICT
    )""",
    *tuple(
        f"CREATE TRIGGER DriverApprovalChanges_No{action.title()} BEFORE {action} ON DriverApprovalChanges "
        "BEGIN SELECT RAISE(ABORT,'Driver evidence history is immutable.'); END"
        for action in ("UPDATE", "DELETE")
    ),
)
