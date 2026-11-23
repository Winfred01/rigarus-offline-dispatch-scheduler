"""Test-only reconstruction of legacy fixtures, never an operational downgrade."""

from rigarus_backend.storage import ASSIGNMENT_STAFFING, EMPLOYEE_AVAILABILITY


def remove_staffing_schema(connection):
    remove_availability_schema(connection)
    connection.execute("DROP TABLE AssignmentStaffingMembers")
    connection.execute("DROP TABLE AssignmentStaffingChanges")
    connection.execute(
        "DELETE FROM __EFMigrationsHistory WHERE MigrationId=?", (ASSIGNMENT_STAFFING,)
    )


def remove_availability_schema(connection):
    connection.execute("DROP TABLE EmployeeAvailability")
    connection.execute("DROP TABLE EmployeeAvailabilityChanges")
    connection.execute(
        "DELETE FROM __EFMigrationsHistory WHERE MigrationId=?",
        (EMPLOYEE_AVAILABILITY,),
    )
