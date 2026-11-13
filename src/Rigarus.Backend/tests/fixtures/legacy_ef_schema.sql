CREATE TABLE IF NOT EXISTS "__EFMigrationsHistory" (
    "MigrationId" TEXT NOT NULL CONSTRAINT "PK___EFMigrationsHistory" PRIMARY KEY,
    "ProductVersion" TEXT NOT NULL
);

BEGIN TRANSACTION;
CREATE TABLE "DemoProjects" (
    "Id" INTEGER NOT NULL CONSTRAINT "PK_DemoProjects" PRIMARY KEY,
    "JobNumber" TEXT NOT NULL,
    "SiteName" TEXT NOT NULL,
    "Note" TEXT NOT NULL,
    CONSTRAINT "CK_DemoProjects_NoteLength" CHECK (length(Note) <= 200)
);

CREATE UNIQUE INDEX "IX_DemoProjects_JobNumber" ON "DemoProjects" ("JobNumber");

INSERT INTO "DemoProjects" ("Id", "JobNumber", "SiteName", "Note")
VALUES (1, 'DEMO-001', 'Example Site', 'Synthetic sample for M0.');
SELECT changes();


INSERT INTO "__EFMigrationsHistory" ("MigrationId", "ProductVersion")
VALUES ('20261112045924_InitialDemo', '10.0.15');

COMMIT;

BEGIN TRANSACTION;
CREATE TABLE "Projects" (
    "Id" INTEGER NOT NULL CONSTRAINT "PK_Projects" PRIMARY KEY AUTOINCREMENT,
    "JobNumber" TEXT COLLATE NOCASE NOT NULL,
    "SiteId" TEXT NOT NULL,
    "SiteName" TEXT NOT NULL,
    CONSTRAINT "CK_Projects_JobNumber" CHECK (length(JobNumber) > 0 AND JobNumber = trim(JobNumber)),
    CONSTRAINT "CK_Projects_SiteId" CHECK (length(trim(SiteId)) > 0),
    CONSTRAINT "CK_Projects_SiteName" CHECK (length(trim(SiteName)) > 0)
);

CREATE TABLE "WorkItems" (
    "Id" INTEGER NOT NULL CONSTRAINT "PK_WorkItems" PRIMARY KEY AUTOINCREMENT,
    "ProjectId" INTEGER NOT NULL,
    "Type" TEXT NOT NULL,
    "RequiredCrewCount" INTEGER NOT NULL,
    "EstimatedHalfDays" INTEGER NOT NULL,
    CONSTRAINT "CK_WorkItems_EstimatedHalfDays" CHECK (typeof(EstimatedHalfDays) = 'integer' AND EstimatedHalfDays BETWEEN 1 AND 2147483647),
    CONSTRAINT "CK_WorkItems_RequiredCrewCount" CHECK (typeof(RequiredCrewCount) = 'integer' AND RequiredCrewCount BETWEEN 1 AND 2147483647),
    CONSTRAINT "CK_WorkItems_Type" CHECK (Type IN ('Small', 'Civil', 'Tower', 'Other')),
    CONSTRAINT "FK_WorkItems_Projects_ProjectId" FOREIGN KEY ("ProjectId") REFERENCES "Projects" ("Id") ON DELETE RESTRICT
);

CREATE UNIQUE INDEX "IX_Projects_JobNumber" ON "Projects" ("JobNumber");

CREATE INDEX "IX_WorkItems_ProjectId" ON "WorkItems" ("ProjectId");

INSERT INTO "__EFMigrationsHistory" ("MigrationId", "ProductVersion")
VALUES ('20261112072258_AddProjectsAndWorkItems', '10.0.15');

COMMIT;
