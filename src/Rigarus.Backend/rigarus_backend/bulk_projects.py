import base64
import binascii
import csv
import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from io import BytesIO, StringIO

from openpyxl import Workbook

from .import_preview import (
    REQUIRED,
    Diagnostic,
    ExistingProject,
    ImportPreview,
    PreviewError,
    PreviewRow,
    job_key,
    preview_row,
    preview_workbook,
)

TEMPLATE_HEADERS = ("Project Number", "Site ID", "Site Name")


@dataclass(frozen=True)
class TextCell:
    value: str
    data_type: str = "s"


@dataclass
class BulkPreview:
    preview: ImportPreview
    preview_id: str
    ready_count: int
    skipped_count: int


def text_rows(content: str) -> ImportPreview:
    if len(content.encode("utf-8")) > 5 * 1024 * 1024:
        raise PreviewError("Paste CSV text of at most 5 MiB.")
    reader = csv.reader(
        StringIO(content.removeprefix("\ufeff"), newline=""), strict=True
    )
    try:
        headers = next(reader, [])
        if [h.strip().lower() for h in headers] != [
            h.lower() for h in TEMPLATE_HEADERS
        ]:
            raise PreviewError("Use CSV headers: Project Number,Site ID,Site Name.")
        rows = []
        while True:
            start = reader.line_num + 1
            values = next(reader, None)
            if values is None:
                break
            if not values or all(not value.strip() for value in values):
                continue
            if len(rows) >= 2000:
                raise PreviewError("Bulk Add supports up to 2000 data rows.")
            source = f"Paste Text line {start}"
            if reader.line_num != start:
                source += f"-{reader.line_num}"
            if len(values) != 3:
                rows.append(
                    PreviewRow(
                        source,
                        {},
                        "Skip",
                        "Invalid",
                        [
                            Diagnostic(
                                source, "Each CSV row must have exactly three fields."
                            )
                        ],
                    )
                )
                continue
            row = preview_row(
                "Paste Text", start, [TextCell(v) for v in values], list(REQUIRED), {}
            )
            row.source = source
            row.diagnostics = [
                Diagnostic(source, d.message, d.severity) for d in row.diagnostics
            ]
            rows.append(row)
    except csv.Error as error:
        raise PreviewError(
            "Could not read CSV. Check quoting and field lengths."
        ) from error
    return ImportPreview(rows, [], {})


def preview_bulk(
    kind: str, content: str, existing: dict[str, ExistingProject]
) -> BulkPreview:
    if kind == "text":
        preview = text_rows(content)
    elif kind == "xlsx":
        try:
            raw = base64.b64decode(content, validate=True)
        except (ValueError, binascii.Error) as error:
            raise PreviewError("Workbook content could not be decoded.") from error
        try:
            preview = preview_workbook(raw, {}, project_only=True)
        except PreviewError:
            raise
        except Exception as error:
            raise PreviewError(
                "Could not read this .xlsx workbook. Check the file and try again."
            ) from error
    else:
        raise PreviewError("Choose Paste Text or Upload Excel.")

    repeated = Counter(job_key(row.values.get("Job #", "")) for row in preview.rows)
    for row in preview.rows:
        key = job_key(row.values.get("Job #", ""))
        if any(value for label, value in row.values.items() if label not in REQUIRED):
            row.status, row.action = "Invalid", "Skip"
            row.diagnostics.append(
                Diagnostic(
                    row.source,
                    "Bulk Add stores only Project Number, Site ID and Site Name. Remove other populated fields.",
                )
            )
        if row.status == "Invalid":
            continue
        if key in existing or (key and repeated[key] > 1):
            row.status, row.action = "Duplicate", "Skip"
            row.diagnostics.append(
                Diagnostic(
                    row.source,
                    "Project Number already exists or is repeated in this input. Existing records will not be changed.",
                    "Warning",
                )
            )
    if not preview.rows and not preview.diagnostics:
        preview.diagnostics.append(Diagnostic("Input", "No data rows found."))
    preview.counts = dict(Counter(row.status for row in preview.rows))
    ready = sum(
        row.status == "Ready" and row.action == "Create" for row in preview.rows
    )
    fingerprint = json.dumps(
        [kind, content, asdict(preview)], sort_keys=True, ensure_ascii=True
    ).encode()
    return BulkPreview(
        preview,
        hashlib.sha256(fingerprint).hexdigest(),
        ready,
        len(preview.rows) - ready,
    )


def project_template() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Projects"
    sheet.append(TEMPLATE_HEADERS)
    sheet.freeze_panes = "A2"
    for column, width in zip("ABC", (24, 20, 40), strict=True):
        sheet.column_dimensions[column].width = width
        # Preformat the full supported entry range to retain leading zeroes.
        for row in range(2, 2002):
            sheet[f"{column}{row}"].number_format = "@"
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()
