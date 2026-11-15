from dataclasses import dataclass
from typing import Literal

CrewType = Literal["Civil", "Tower"]


@dataclass(frozen=True)
class CrewDraft:
    name: str
    type: CrewType
    active: bool = True

    def __post_init__(self):
        name = self.name.strip()
        if not name or len(name) > 100 or "\x00" in name:
            raise ValueError("Crew name must contain 1 to 100 characters.")
        object.__setattr__(self, "name", name)


@dataclass(frozen=True)
class Crew:
    id: int
    name: str
    type: CrewType
    active: bool


class CrewNotFound(ValueError):
    pass


@dataclass(frozen=True)
class EmployeeDraft:
    name: str
    home_crew_id: int
    skill_level: int
    foreman_eligible: bool = False
    active: bool = True

    def __post_init__(self):
        name = self.name.strip()
        if not name or len(name) > 100 or "\x00" in name:
            raise ValueError("Employee name must contain 1 to 100 characters.")
        if type(self.skill_level) is not int or not 1 <= self.skill_level <= 3:
            raise ValueError("Select a skill level from 1 to 3.")
        object.__setattr__(self, "name", name)


@dataclass(frozen=True)
class Employee:
    id: int
    name: str
    home_crew_id: int
    skill_level: int
    foreman_eligible: bool
    active: bool
    driver_status: Literal["Unverified"]


class EmployeeNotFound(ValueError):
    pass
