from collections import Counter
from dataclasses import dataclass, field
from io import BytesIO
from typing import Literal
from zipfile import ZipFile

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from .projects import ProjectDraft, WorkType

MAX_FILE_BYTES = 5 * 1024 * 1024


class PreviewError(ValueError):
    pass


HEADERS = (
    "Job #",
    "Site ID",
    "Site Name",
    "Description",
    "Customer",
    "Crew Type",
    "Crew Count",
    "Estimated Half-days",
)
REQUIRED = HEADERS[:3]
WORK_FIELDS = HEADERS[5:]
ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def job_key(value: str) -> str:
    return value.strip().translate(ASCII_LOWER)


@dataclass(frozen=True)
class ExistingProject:
    id: int
    site_id: str
    site_name: str
    work_items: tuple[tuple[str, int, int], ...]


@dataclass(frozen=True)
class Diagnostic:
    source: str
    message: str
    severity: Literal["Error", "Warning"] = "Error"


@dataclass
class PreviewRow:
    source: str
    values: dict[str, str]
    action: Literal["Create", "Update", "Skip"] = "Create"
    status: Literal["Ready", "Duplicate", "Review", "Invalid"] = "Ready"
    diagnostics: list[Diagnostic] = field(default_factory=list)


@dataclass
class ImportPreview:
    rows: list[PreviewRow]
    diagnostics: list[Diagnostic]
    counts: dict[str, int]


def location(sheet: str, coordinate: str) -> str:
    return "'" + sheet.replace("'", "''") + "'!" + coordinate


def whole_number(value) -> int:
    if type(value) is int or (type(value) is float and value.is_integer()):
        result = int(value)
    elif (
        isinstance(value, str) and value.strip().isascii() and value.strip().isdecimal()
    ):
        result = int(value.strip())
    else:
        raise ValueError("Enter a positive whole number.")
    if not 1 <= result <= 2_147_483_647:
        raise ValueError("Enter a whole number from 1 to 2147483647.")
    return result


def preview_row(sheet, number, cells, columns, existing) -> PreviewRow:
    start, end = f"A{number}", f"{get_column_letter(len(cells))}{number}"
    row = PreviewRow(location(sheet, f"{start}:{end}"), {})
    for index, (label, cell) in enumerate(zip(columns, cells, strict=True), 1):
        value = cell.value
        if value is None:
            value = ""
        text = str(value).strip()
        row.values[label] = text[:2000]
        source = location(sheet, f"{get_column_letter(index)}{number}")
        if len(text) > 2000:
            row.diagnostics.append(
                Diagnostic(
                    source, "Cell exceeds 2000 characters; preview text is truncated."
                )
            )
        if cell.data_type in ("f", "e"):
            row.diagnostics.append(
                Diagnostic(
                    source,
                    "Formula or Excel error cannot be resolved. Replace it with a verified value.",
                )
            )
        if text and label not in HEADERS:
            row.diagnostics.append(
                Diagnostic(
                    source,
                    "Column is not mapped. Dates, IDs and other fields need an approved mapping.",
                    "Warning",
                )
            )
        if text and label in ("Description", "Customer"):
            row.diagnostics.append(
                Diagnostic(
                    source,
                    f"{label} is visible for review; the current project model does not store it.",
                    "Warning",
                )
            )

    for label in REQUIRED:
        index = columns.index(label)
        value = cells[index].value
        if not isinstance(value, str) or not value.strip() or "\x00" in value:
            row.diagnostics.append(
                Diagnostic(
                    location(sheet, f"{get_column_letter(index + 1)}{number}"),
                    f"{label} must be nonempty text. Keep identifiers as text to preserve leading zeroes.",
                )
            )

    work_items = []
    if any(row.values.get(label, "") for label in WORK_FIELDS):
        for label in WORK_FIELDS:
            if label not in columns:
                row.diagnostics.append(
                    Diagnostic(
                        row.source,
                        f"Add the {label} column to describe this work item.",
                    )
                )
        if all(label in columns for label in WORK_FIELDS):
            kind = row.values["Crew Type"]
            try:
                WorkType(kind)
            except ValueError:
                row.diagnostics.append(
                    Diagnostic(
                        location(
                            sheet,
                            f"{get_column_letter(columns.index('Crew Type') + 1)}{number}",
                        ),
                        "Crew Type must be Small, Civil, Tower or Other.",
                    )
                )
            numbers = []
            for label in WORK_FIELDS[1:]:
                cell = cells[columns.index(label)]
                try:
                    numbers.append(whole_number(cell.value))
                except ValueError as error:
                    row.diagnostics.append(
                        Diagnostic(
                            location(
                                sheet,
                                f"{get_column_letter(columns.index(label) + 1)}{number}",
                            ),
                            f"{label}: {error}",
                        )
                    )
            if len(numbers) == 2:
                work_items.append((kind, *numbers))

    if any(issue.severity == "Error" for issue in row.diagnostics):
        row.status, row.action = "Invalid", "Skip"
        return row

    draft = ProjectDraft(
        row.values["Job #"], row.values["Site ID"], row.values["Site Name"], []
    )
    match = existing.get(job_key(draft.job_number))
    if match:
        unchanged = (
            match.site_id == draft.site_id and match.site_name == draft.site_name
        )
        if work_items:
            unchanged = unchanged and match.work_items == tuple(work_items)
        row.action = "Skip" if unchanged else "Update"
        row.status = "Duplicate" if unchanged else "Review"
        row.diagnostics.append(
            Diagnostic(
                row.source,
                f"Job # matches existing project #{match.id}. Review the proposed {row.action.lower()} outcome.",
                "Warning",
            )
        )
    elif row.diagnostics:
        row.status = "Review"
    return row


def preview_workbook(
    content: bytes, existing: dict[str, ExistingProject]
) -> ImportPreview:
    if not content or len(content) > MAX_FILE_BYTES:
        raise PreviewError("Choose an .xlsx workbook of at most 5 MiB.")
    with ZipFile(BytesIO(content)) as archive:
        entries = archive.infolist()
        if (
            len(entries) > 1000
            or sum(item.file_size for item in entries) > 25 * 1024 * 1024
        ):
            raise PreviewError("Workbook exceeds the preview archive limits.")
        if any(item.filename.lower().endswith("vbaproject.bin") for item in entries):
            raise PreviewError("Choose an .xlsx workbook without macros.")
    workbook = load_workbook(
        BytesIO(content), read_only=True, data_only=False, keep_links=False
    )
    rows, diagnostics = [], []
    seen: dict[str, list[PreviewRow]] = {}
    try:
        if len(workbook.worksheets) > 10:
            raise PreviewError("Preview supports up to 10 worksheets.")
        for sheet in workbook.worksheets:
            if (sheet.max_row or 0) > 2001 or (sheet.max_column or 0) > 40:
                raise PreviewError(
                    "Each worksheet must fit within 2000 data rows and 40 columns."
                )
            width = max(1, sheet.max_column or 1)
            sheet_rows = sheet.iter_rows(max_row=2001, max_col=width)
            header_cells = next(sheet_rows, ())
            canonical = {label.lower(): label for label in HEADERS}
            columns = [
                canonical.get(
                    str(cell.value or "").strip().lower(), str(cell.value or "").strip()
                )
                for cell in header_cells
            ]
            if not any(columns):
                continue
            columns = [
                label or f"Column {get_column_letter(index)}"
                for index, label in enumerate(columns, 1)
            ]
            duplicates = [
                label
                for label, count in Counter(columns).items()
                if label and count > 1
            ]
            missing = [label for label in REQUIRED if label not in columns]
            if duplicates or missing:
                diagnostics.append(
                    Diagnostic(
                        location(sheet.title, f"A1:{get_column_letter(width)}1"),
                        "Check header row. Missing: "
                        + (", ".join(missing) or "none")
                        + ". Repeated: "
                        + (", ".join(duplicates) or "none")
                        + ".",
                    )
                )
                continue
            for number, cells in enumerate(sheet_rows, 2):
                if all(cell.value is None for cell in cells):
                    continue
                if len(rows) >= 2000:
                    raise PreviewError(
                        "Preview supports up to 2000 data rows across the workbook."
                    )
                row = preview_row(sheet.title, number, cells, columns, existing)
                rows.append(row)
                key = job_key(row.values.get("Job #", ""))
                if key:
                    seen.setdefault(key, []).append(row)
        for matches in seen.values():
            if len(matches) > 1:
                sources = ", ".join(row.source for row in matches[:5])
                for row in matches:
                    row.action = "Skip"
                    if row.status != "Invalid":
                        row.status = "Duplicate"
                    row.diagnostics.append(
                        Diagnostic(
                            row.source,
                            "Repeated Job # in this workbook. Check rows "
                            + sources
                            + ".",
                        )
                    )
        if not rows and not diagnostics:
            diagnostics.append(
                Diagnostic(
                    "Workbook", "No data rows found. Put the mapped headers in row 1."
                )
            )
        return ImportPreview(
            rows, diagnostics, dict(Counter(row.status for row in rows))
        )
    finally:
        workbook.close()
