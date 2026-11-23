"""Explicit Draft visit membership, independent of HTTP and Home Crew ownership."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AssignedWorker:
    employee_id: int
    name: str
    home_crew_id: int
    active: bool
    driver_status: str


@dataclass(frozen=True)
class StaffingState:
    configured: bool = False
    change_id: int = 0
    workers: list[AssignedWorker] = field(default_factory=list)


def worker_ids(values: list[int]) -> tuple[int, ...]:
    if any(
        type(value) is not int or not 1 <= value <= 9_007_199_254_740_991
        for value in values
    ):
        raise ValueError("Select existing employee IDs.")
    if len(set(values)) != len(values):
        raise ValueError("Select each employee only once.")
    return tuple(sorted(values))
