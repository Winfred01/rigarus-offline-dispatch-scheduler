import base64
import hashlib
import sqlite3
import tempfile
import unittest
from contextlib import closing
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from fastapi.testclient import TestClient
from openpyxl import Workbook

from rigarus_backend.api import create_app
from rigarus_backend.import_preview import (
    HEADERS,
    MAX_FILE_BYTES,
    ExistingProject,
    PreviewError,
    preview_workbook,
)
from rigarus_backend.import_preview_api import read_existing_projects


def workbook_bytes(rows, *, title="Synthetic Plan", headers=HEADERS):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = title
    sheet.append(list(headers))
    for row in rows:
        sheet.append(row)
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


class ImportPreviewTests(unittest.TestCase):
    def test_row_locations_duplicates_blanks_and_unresolved_values(self):
        content = workbook_bytes(
            [
                ["SYN-001", "0001", "Synthetic yard"],
                ["syn-001", "0001", "Repeated yard"],
                ["SYN-002", None, "Missing identifier"],
                ["SYN-003", "0003", "=1+1"],
                ["SYN-004", "0004", "#REF!"],
                [
                    "SYN-005",
                    "0005",
                    "External formula",
                    None,
                    None,
                    "Tower",
                    "='[External.xlsx]Sheet1'!A1",
                    3,
                ],
                [None] * 8,
                ["SYN-006", "0006", "Synthetic valid", None, None, "Civil", 1, 3],
            ],
            title="Synthetic 'Plan",
        )
        result = preview_workbook(content, {})
        self.assertEqual(result.counts, {"Duplicate": 2, "Invalid": 4, "Ready": 1})
        self.assertEqual(result.rows[0].source, "'Synthetic ''Plan'!A2:H2")
        self.assertEqual(result.rows[-1].values["Site ID"], "0006")
        self.assertEqual(result.rows[-1].action, "Create")
        self.assertIn(
            "'Synthetic ''Plan'!B4", [d.source for d in result.rows[2].diagnostics]
        )
        for row in result.rows[3:6]:
            self.assertTrue(
                any("Formula or Excel error" in d.message for d in row.diagnostics)
            )

    def test_existing_ids_unsupported_columns_and_work_item_validation(self):
        existing = {"syn-001": ExistingProject(44, "0001", "Existing yard", ())}
        result = preview_workbook(
            workbook_bytes(
                [
                    ["SYN-001", "0001", "Existing yard"],
                    [
                        "SYN-002",
                        "0002",
                        "Review",
                        "Synthetic description",
                        "Synthetic customer",
                    ],
                    ["SYN-003", 3, "Numeric identifier"],
                    [
                        "SYN-004",
                        "0004",
                        "Fractional estimate",
                        None,
                        None,
                        "Tower",
                        1,
                        1.5,
                    ],
                    ["SYN-005", "0005", "Unknown type", None, None, "Unknown", 1, 3],
                ]
            ),
            existing,
        )
        self.assertEqual(result.rows[0].action, "Skip")
        self.assertEqual(result.rows[0].status, "Duplicate")
        self.assertEqual(result.rows[1].status, "Review")
        self.assertEqual(result.rows[1].values["Description"], "Synthetic description")
        self.assertTrue(all(row.status == "Invalid" for row in result.rows[2:]))
        changed = preview_workbook(
            workbook_bytes([["SYN-001", "0009", "Changed yard"]]), existing
        ).rows[0]
        self.assertEqual((changed.status, changed.action), ("Review", "Update"))
        unknown = preview_workbook(
            workbook_bytes(
                [["SYN-007", "0007", "Dates need mapping", "2026-11-19"]],
                headers=("Job #", "Site ID", "Site Name", "Start date"),
            ),
            {},
        ).rows[0]
        self.assertEqual(unknown.status, "Review")
        self.assertEqual(unknown.diagnostics[0].source, "'Synthetic Plan'!D2")
        self.assertIn("not mapped", unknown.diagnostics[0].message)

    def test_bad_headers_and_repeated_jobs_across_worksheets(self):
        result = preview_workbook(
            workbook_bytes(
                [["SYN", "a", "b"]], headers=("Job #", "Site Name", "Site Name")
            ),
            {},
        )
        self.assertEqual(result.rows, [])
        self.assertIn("Missing: Site ID", result.diagnostics[0].message)
        self.assertEqual(result.diagnostics[0].source, "'Synthetic Plan'!A1:C1")
        workbook = Workbook()
        for sheet in (workbook.active, workbook.create_sheet("Second")):
            sheet.append(list(HEADERS))
            sheet.append(["SYN-007", "0007", "Synthetic yard"])
        output = BytesIO()
        workbook.save(output)
        workbook.close()
        result = preview_workbook(output.getvalue(), {})
        self.assertEqual(result.counts, {"Duplicate": 2})
        self.assertTrue(all(row.action == "Skip" for row in result.rows))

    def test_file_and_workbook_limits(self):
        with self.assertRaises(PreviewError):
            preview_workbook(b"x" * (MAX_FILE_BYTES + 1), {})
        with self.assertRaises(PreviewError):
            preview_workbook(
                workbook_bytes(
                    [["SYN", "001", "Synthetic"]],
                    headers=(
                        "Job #",
                        "Site ID",
                        "Site Name",
                        *[f"Column-{n}" for n in range(38)],
                    ),
                ),
                {},
            )
        output = BytesIO()
        with ZipFile(output, "w") as archive:
            archive.writestr("xl/vbaProject.bin", b"synthetic")
        with self.assertRaisesRegex(PreviewError, "without macros"):
            preview_workbook(output.getvalue(), {})

    def test_api_keeps_database_bytes_and_content_unchanged_across_preview(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "synthetic.db"
            with TestClient(create_app(database)) as client:
                client.post(
                    "/projects",
                    json={
                        "job_number": "SYN-001",
                        "site_id": "0001",
                        "site_name": "Existing yard",
                        "work_items": [
                            {
                                "type": "Tower",
                                "required_crew_count": 1,
                                "estimated_half_days": 3,
                            }
                        ],
                    },
                ).raise_for_status()
                with closing(sqlite3.connect(database)) as connection:
                    connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    before = tuple(connection.iterdump())
                digest = hashlib.sha256(database.read_bytes()).digest()
                content = workbook_bytes(
                    [
                        ["SYN-001", "0002", "Changed yard"],
                        ["SYN-002", "0002", "New yard"],
                        ["SYN-003", None, "Missing ID"],
                    ]
                )
                encoded = base64.b64encode(content).decode("ascii")
                for _ in range(2):
                    response = client.post("/import-preview", json={"content": encoded})
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json()["rows"][0]["action"], "Update")
                    self.assertEqual(
                        hashlib.sha256(database.read_bytes()).digest(), digest
                    )
                with closing(sqlite3.connect(database)) as connection:
                    self.assertEqual(tuple(connection.iterdump()), before)
                self.assertEqual(
                    client.post("/import-preview/commit", json={}).status_code, 404
                )
                self.assertEqual(read_existing_projects(database)["syn-001"].id, 1)
            with TestClient(create_app(database)) as client:
                self.assertEqual(
                    client.get("/projects").json()[0]["site_name"], "Existing yard"
                )
                self.assertEqual(len(client.get("/projects").json()), 1)

    def test_invalid_workbook_errors_do_not_expose_content(self):
        with (
            tempfile.TemporaryDirectory() as folder,
            TestClient(create_app(Path(folder) / "synthetic.db")) as client,
        ):
            for content in (
                "not base64!",
                base64.b64encode(b"synthetic invalid workbook").decode(),
            ):
                response = client.post("/import-preview", json={"content": content})
                self.assertEqual(response.status_code, 422)
                self.assertNotIn("synthetic invalid workbook", response.text)
