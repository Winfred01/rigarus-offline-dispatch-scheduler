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
    for table in (
        "CapabilityEvidenceCells",
        "CapabilityEvidenceChanges",
        "CapabilityEvidenceOwners",
    ):
        connection.execute(f"DROP TABLE IF EXISTS {table}")
    connection.execute(
        "DELETE FROM __EFMigrationsHistory WHERE MigrationId=?", (CAPABILITY_EVIDENCE,)
    )
