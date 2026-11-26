"""Test-only reconstruction of legacy fixtures, never an operational downgrade."""

from rigarus_backend.storage import ASSIGNMENT_STAFFING, EMPLOYEE_AVAILABILITY
from rigarus_backend.calendar_migration import WORKING_CALENDARS
from rigarus_backend.driver_migration import DRIVER_APPROVALS
from rigarus_backend.capability_migration import CAPABILITY_EVIDENCE


def remove_staffing_schema(connection):
    remove_availability_schema(connection)
    connection.execute("DROP TABLE AssignmentStaffingMembers")
    connection.execute("DROP TABLE AssignmentStaffingChanges")
    connection.execute(
        "DELETE FROM __EFMigrationsHistory WHERE MigrationId=?", (ASSIGNMENT_STAFFING,)
    )


def remove_availability_schema(connection):
    remove_working_calendar_schema(connection)
    connection.execute("DROP TABLE EmployeeAvailability")
    connection.execute("DROP TABLE EmployeeAvailabilityChanges")
    connection.execute(
        "DELETE FROM __EFMigrationsHistory WHERE MigrationId=?",
        (EMPLOYEE_AVAILABILITY,),
    )


def remove_working_calendar_schema(connection):
    remove_driver_schema(connection)
    for table in ("WorkingCalendarCells", "WorkingCalendarChanges", "WorkingCalendars"):
        connection.execute(f"DROP TABLE IF EXISTS {table}")
    connection.execute(
        "DELETE FROM __EFMigrationsHistory WHERE MigrationId=?", (WORKING_CALENDARS,)
    )


def remove_driver_schema(connection):
    remove_capability_schema(connection)
    for table in ("DriverApprovalCells", "DriverApprovalChanges"):
        connection.execute(f"DROP TABLE IF EXISTS {table}")
    connection.execute(
        "DELETE FROM __EFMigrationsHistory WHERE MigrationId=?", (DRIVER_APPROVALS,)
    )


def remove_capability_schema(connection):
    remove_day_schema(connection)
    for table in (
        "CapabilityEvidenceCells",
        "CapabilityEvidenceChanges",
        "CapabilityEvidenceOwners",
    ):
        connection.execute(f"DROP TABLE IF EXISTS {table}")
    connection.execute(
        "DELETE FROM __EFMigrationsHistory WHERE MigrationId=?", (CAPABILITY_EVIDENCE,)
    )


def remove_day_schema(connection):
    remove_daily_calendar_schema(connection)
    # Synthetic fixture construction only. Never ship an operational down migration.
    from rigarus_backend.day_migration import DAY_DRAFTS

    for name in ("DraftAssignments_DayInsert", "DraftAssignments_DayUpdate"):
        connection.execute(f"DROP TRIGGER IF EXISTS {name}")
    for table in ("DayDraftMembers", "DayDraftChanges", "DayDraftAssignments"):
        connection.execute(f"DROP TABLE IF EXISTS {table}")
    connection.execute(
        "DELETE FROM __EFMigrationsHistory WHERE MigrationId=?", (DAY_DRAFTS,)
    )


def remove_daily_calendar_schema(connection):
    remove_daily_driver_schema(connection)
    # Synthetic schema13 fixture only, never an operational down migration.
    from rigarus_backend.daily_calendar_migration import DAILY_CALENDARS

    for table in ("DailyCalendarCells", "DailyCalendarChanges", "DailyCalendarOwners"):
        connection.execute(f"DROP TABLE IF EXISTS {table}")
    connection.execute(
        "DELETE FROM __EFMigrationsHistory WHERE MigrationId=?", (DAILY_CALENDARS,)
    )


def remove_daily_driver_schema(connection):
    remove_daily_capability_schema(connection)
    # Synthetic schema14 only; never an operational downgrade.
    from rigarus_backend.daily_driver_migration import DAILY_DRIVERS

    for table in ("DailyDriverApprovalCells", "DailyDriverApprovalChanges"):
        connection.execute(f"DROP TABLE IF EXISTS {table}")
    connection.execute(
        "DELETE FROM __EFMigrationsHistory WHERE MigrationId=?", (DAILY_DRIVERS,)
    )


def remove_daily_capability_schema(connection):
    remove_daily_rig_schema(connection)
    # Synthetic15 reconstruction only, never operational downgrade.
    from rigarus_backend.daily_capability_migration import DAILY_CAPABILITIES

    for table in ("DailyCapabilityCells", "DailyCapabilityChanges"):
        connection.execute(f"DROP TABLE IF EXISTS {table}")
    connection.execute(
        "DELETE FROM __EFMigrationsHistory WHERE MigrationId=?", (DAILY_CAPABILITIES,)
    )


def remove_daily_rig_schema(connection):
    remove_daily_weekend_schema(connection)
    # Synthetic schema16 reconstruction only, never an operational downgrade.
    from rigarus_backend.daily_rig_migration import DAILY_RIGS

    for table in ("DayDraftAssignments", "DraftAssignments"):
        connection.execute(f"DROP TRIGGER IF EXISTS {table}_RigMove")
    for view in (
        "RigDailyOccupancy",
        "RigCurrentAllocations",
        "RigAssignmentContexts",
        "RigCurrentConditions",
    ):
        connection.execute(f"DROP VIEW IF EXISTS {view}")
    for table in (
        "RigAllocationChanges",
        "RigAllocations",
        "RigConditionChanges",
        "RigConditionPeriods",
    ):
        connection.execute(f"DROP TABLE IF EXISTS {table}")
    connection.execute(
        "DELETE FROM __EFMigrationsHistory WHERE MigrationId=?", (DAILY_RIGS,)
    )


def remove_daily_weekend_schema(connection):
    remove_day_editor_schema(connection)
    # Synthetic17 fixtures only. Never an operational downgrade.
    from rigarus_backend.daily_weekend_migration import DAILY_WEEKEND

    for table in ("WeekendConsentChanges", "WeekendConsentScopes"):
        connection.execute(f"DROP TABLE IF EXISTS {table}")
    connection.execute(
        "DELETE FROM __EFMigrationsHistory WHERE MigrationId=?", (DAILY_WEEKEND,)
    )


def remove_day_editor_schema(connection):
    remove_draft_version_schema(connection)
    # Synthetic18 reconstruction only, never an operational downgrade.
    from rigarus_backend.day_editor_migration import DAY_EDITOR

    for table in ("DayEditorReceipts", "DayEditorWorkspace"):
        connection.execute(f"DROP TABLE IF EXISTS {table}")
    connection.execute(
        "DELETE FROM __EFMigrationsHistory WHERE MigrationId=?", (DAY_EDITOR,)
    )


def remove_draft_version_schema(connection):
    # Synthetic schema19 reconstruction only. Never an operational downgrade.
    from rigarus_backend.draft_version_migration import DRAFT_VERSIONS

    connection.execute("DROP TABLE IF EXISTS DraftVersions")
    connection.execute(
        "DELETE FROM __EFMigrationsHistory WHERE MigrationId=?", (DRAFT_VERSIONS,)
    )
