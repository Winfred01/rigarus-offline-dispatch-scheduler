from dataclasses import dataclass


@dataclass(frozen=True)
class ForemanChange:
    id: int
    crew_id: int
    employee_id: int | None
    crew_name: str
    employee_name: str | None
    recorded_at: str


@dataclass(frozen=True)
class ForemanState:
    crew_id: int
    revision: int
    employee_id: int | None
    employee_name: str | None
    employee_active: bool | None
    employee_eligible: bool | None
    history: list[ForemanChange]


class StaleForemanChange(ValueError):
    pass
