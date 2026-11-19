from dataclasses import dataclass


@dataclass(frozen=True)
class RigDraft:
    number: str
    type: str
    notes: str = ""
    default_crew_id: int | None = None
    active: bool = True

    def __post_init__(self):
        for field, label, minimum, maximum in (
            ("number", "Rig #", 1, 50),
            ("type", "Rig type", 1, 100),
            ("notes", "Notes", 0, 2000),
        ):
            value = getattr(self, field).strip()
            if not minimum <= len(value) <= maximum or "\x00" in value:
                raise ValueError(
                    f"{label} must contain {minimum} to {maximum} characters."
                )
            object.__setattr__(self, field, value)


@dataclass(frozen=True)
class Rig:
    id: int
    number: str
    type: str
    notes: str
    default_crew_id: int | None
    active: bool


class RigNotFound(ValueError):
    pass


class DuplicateRigNumber(ValueError):
    pass
