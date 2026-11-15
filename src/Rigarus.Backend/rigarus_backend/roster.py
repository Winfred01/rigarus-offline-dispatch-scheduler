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
