from dataclasses import dataclass
from enum import StrEnum


class WorkType(StrEnum):
    SMALL = "Small"
    CIVIL = "Civil"
    TOWER = "Tower"
    OTHER = "Other"


@dataclass(frozen=True)
class WorkItemDraft:
    id: int | None
    type: WorkType
    required_crew_count: int
    estimated_half_days: int


@dataclass(frozen=True)
class ProjectDraft:
    job_number: str
    site_id: str
    site_name: str
    work_items: list[WorkItemDraft]

    def __post_init__(self):
        for field, label in (
            ("job_number", "Job #"),
            ("site_id", "Site ID"),
            ("site_name", "site name"),
        ):
            value = getattr(self, field).strip()
            if not value or "\0" in value:
                raise ValueError(f"Enter a valid {label}.")
            object.__setattr__(self, field, value)


@dataclass(frozen=True)
class ProjectSummary:
    id: int
    job_number: str
    site_id: str
    site_name: str
    work_item_count: int


@dataclass(frozen=True)
class ProjectDetail:
    id: int
    job_number: str
    site_id: str
    site_name: str
    work_items: list[WorkItemDraft]


class ProjectNotFound(ValueError):
    pass


class DuplicateJobNumber(ValueError):
    pass
