"""Independent daily policy/qualification provenance, preserving all legacy data."""

DAILY_CAPABILITIES = "20261125010000_AddDailyCapabilities"
DAILY_CAPABILITY_TABLES = {"DailyCapabilityChanges", "DailyCapabilityCells"}
CREATE_DAILY_CAPABILITIES = (
    """CREATE TABLE DailyCapabilityChanges (
      Id INTEGER PRIMARY KEY AUTOINCREMENT,
      OwnerId INTEGER NOT NULL REFERENCES CapabilityEvidenceOwners(Id) ON DELETE RESTRICT,
      Revision INTEGER NOT NULL CHECK(typeof(Revision)='integer' AND Revision>0),
      StartDate TEXT NOT NULL CHECK(length(StartDate)=10 AND substr(StartDate,1,4) BETWEEN '0001' AND '9999' AND StartDate IS strftime('%Y-%m-%d',StartDate,'+0 days')),
      EndDate TEXT NOT NULL CHECK(length(EndDate)=10 AND substr(EndDate,1,4) BETWEEN '0001' AND '9999' AND EndDate IS strftime('%Y-%m-%d',EndDate,'+0 days') AND EndDate>=StartDate),
      Payload TEXT NOT NULL CHECK(length(Payload) BETWEEN 1 AND 20000 AND instr(Payload,char(0))=0),
      CompanyConfirmed INTEGER NOT NULL CHECK(CompanyConfirmed=1),
      FullDayConfirmed INTEGER NOT NULL CHECK(FullDayConfirmed=1),
      LegacyReviewed INTEGER NOT NULL CHECK(LegacyReviewed IN (0,1)),
      LegacyRevision INTEGER NOT NULL CHECK(typeof(LegacyRevision)='integer' AND LegacyRevision>=0),
      LegacySnapshot TEXT NOT NULL CHECK(length(LegacySnapshot)<=250000),
      Reference TEXT NOT NULL CHECK(length(trim(Reference)) BETWEEN 1 AND 200 AND instr(Reference,char(0))=0),
      RecordedAt TEXT NOT NULL,
      UNIQUE(OwnerId,Revision), UNIQUE(Id,OwnerId)
    )""",
    """CREATE TABLE DailyCapabilityCells (
      OwnerId INTEGER NOT NULL REFERENCES CapabilityEvidenceOwners(Id) ON DELETE RESTRICT,
      LocalDate TEXT NOT NULL CHECK(length(LocalDate)=10 AND substr(LocalDate,1,4) BETWEEN '0001' AND '9999' AND LocalDate IS strftime('%Y-%m-%d',LocalDate,'+0 days')),
      ChangeId INTEGER NOT NULL,
      LegacyFingerprint TEXT NOT NULL CHECK(length(LegacyFingerprint)=64 AND LegacyFingerprint NOT GLOB '*[^0-9a-f]*'),
      PRIMARY KEY(OwnerId,LocalDate),
      FOREIGN KEY(ChangeId,OwnerId) REFERENCES DailyCapabilityChanges(Id,OwnerId) ON DELETE RESTRICT
    )""",
    "CREATE INDEX IX_DailyCapabilityCells_Date ON DailyCapabilityCells(LocalDate,OwnerId)",
    *tuple(
        f"CREATE TRIGGER DailyCapabilityChanges_No{action.title()} BEFORE {action} ON DailyCapabilityChanges BEGIN SELECT RAISE(ABORT,'Daily capability history is immutable.'); END"
        for action in ("UPDATE", "DELETE")
    ),
    *tuple(
        f"CREATE TRIGGER DailyCapabilityCells_Context{action.title()} BEFORE {action} ON DailyCapabilityCells WHEN NOT EXISTS(SELECT 1 FROM DailyCapabilityChanges h WHERE h.Id=NEW.ChangeId AND h.OwnerId=NEW.OwnerId AND NEW.LocalDate BETWEEN h.StartDate AND h.EndDate) BEGIN SELECT RAISE(ABORT,'Daily capability history context mismatch.'); END"
        for action in ("INSERT", "UPDATE")
    ),
)
