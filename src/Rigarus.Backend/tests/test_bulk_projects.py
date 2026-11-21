import base64
import concurrent.futures
import hashlib
import sqlite3
import tempfile
import unittest
from contextlib import closing
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from openpyxl import load_workbook

from rigarus_backend.api import create_app
from rigarus_backend.bulk_project_store import BulkProjectStore, StaleBulkPreview
from rigarus_backend.bulk_projects import TEMPLATE_HEADERS, preview_bulk
from rigarus_backend.import_preview import PreviewError
from test_import_preview import workbook_bytes


HEADER = "Project Number,Site ID,Site Name\n"
CSV = (
    HEADER
    + '0002,0002,"Synthetic, yard"\nSYN-REPEAT,03,A\nsyn-repeat,04,B\nSYN-BAD,,Missing site\n'
)


class BulkProjectTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / "rigarus.db"
        self.client = self.enterContext(TestClient(create_app(self.database)))
        self.store = BulkProjectStore(self.database)

    def post(self, action, content=CSV, kind="text", **extra):
        return self.client.post(
            "/bulk-projects/" + action, json={"kind": kind, "content": content, **extra}
        )

    def test_equivalent_csv_and_workbook_validation_preserves_zeroes(self):
        rows = [
            ["0002", "0002", "Synthetic, yard"],
            ["SYN-REPEAT", "03", "A"],
            ["syn-repeat", "04", "B"],
            ["SYN-BAD", None, "Missing site"],
        ]
        excel = base64.b64encode(
            workbook_bytes(rows, headers=TEMPLATE_HEADERS)
        ).decode()
        text = self.post("preview").json()
        sheet = self.post("preview", excel, "xlsx").json()
        self.assertEqual(text["ready_count"], 1)
        self.assertEqual(text["skipped_count"], 3)
        self.assertEqual(text["preview"]["counts"], sheet["preview"]["counts"])
        self.assertEqual(
            [r["values"] for r in text["preview"]["rows"]],
            [r["values"] for r in sheet["preview"]["rows"]],
        )
        self.assertEqual(text["preview"]["rows"][0]["source"], "Paste Text line 2")
        self.assertEqual(
            sheet["preview"]["rows"][0]["source"], "'Synthetic Plan'!A2:C2"
        )
        self.assertNotEqual(text["preview_id"], sheet["preview_id"])

    def test_preview_cancel_and_template_leave_database_bytes_unchanged(self):
        before = hashlib.sha256(self.database.read_bytes()).hexdigest()
        for _ in range(2):
            self.assertEqual(self.post("preview").status_code, 200)
            self.assertEqual(
                self.client.get("/bulk-projects/template").status_code, 200
            )
        self.assertEqual(before, hashlib.sha256(self.database.read_bytes()).hexdigest())
        self.assertEqual(self.client.get("/projects").json(), [])

    def test_excel_tsv_crlf_matches_csv_and_preserves_quoted_text_and_zeroes(self):
        csv_content = (
            HEADER
            + '000071,0007,"West Yard, ""Phase 2"""\n'
            + "SYN-TSV-DUP,01,A\nsyn-tsv-dup,02,B\nSYN-TSV-BAD,,Missing\n"
        )
        tsv_content = (
            "\ufeffProject Number\tSite ID\tSite Name\r\n"
            '000071\t0007\t"West Yard, ""Phase 2"""\r\n'
            "\r\nSYN-TSV-DUP\t01\tA\r\nsyn-tsv-dup\t02\tB\r\n"
            "SYN-TSV-BAD\t\tMissing\r\n"
        )
        before = hashlib.sha256(self.database.read_bytes()).hexdigest()
        csv_preview = self.post("preview", csv_content).json()
        tsv_preview = self.post("preview", tsv_content).json()
        self.assertEqual(tsv_preview["ready_count"], 1)
        self.assertEqual(tsv_preview["skipped_count"], 3)
        self.assertEqual(
            tsv_preview["preview"]["counts"], csv_preview["preview"]["counts"]
        )
        self.assertEqual(
            [r["values"] for r in tsv_preview["preview"]["rows"]],
            [r["values"] for r in csv_preview["preview"]["rows"]],
        )
        row = tsv_preview["preview"]["rows"][0]
        self.assertEqual(row["values"]["Job #"], "000071")
        self.assertEqual(row["values"]["Site ID"], "0007")
        self.assertEqual(row["values"]["Site Name"], 'West Yard, "Phase 2"')
        invalid = tsv_preview["preview"]["rows"][-1]
        self.assertEqual(invalid["source"], "Paste Text line 6")
        self.assertTrue(any("Site ID" in d["message"] for d in invalid["diagnostics"]))
        self.assertEqual(before, hashlib.sha256(self.database.read_bytes()).hexdigest())

    def test_tsv_confirm_revalidates_and_retry_preserves_existing_records(self):
        original = self.client.post(
            "/projects",
            json={
                "job_number": "SYN-KEEP",
                "site_id": "001",
                "site_name": "Keep original",
                "work_items": [
                    {
                        "type": "Tower",
                        "required_crew_count": 2,
                        "estimated_half_days": 4,
                    }
                ],
            },
        ).json()
        content = (
            "Project Number\tSite ID\tSite Name\r\n"
            "000071\t0007\tNorth Yard\r\n"
            "000072\t0008\tWest Yard, Phase 2\r\n"
            "syn-keep\t9999\tDo not overwrite\r\n"
            "SYN-BAD\t\tMissing ID\r\n"
        )
        before = self.database.read_bytes()
        checked = self.post("preview", content).json()
        self.assertEqual(self.database.read_bytes(), before)
        self.assertEqual((checked["ready_count"], checked["skipped_count"]), (2, 2))
        self.assertEqual(
            self.post(
                "confirm", content + "\r\n", preview_id=checked["preview_id"]
            ).status_code,
            409,
        )
        self.assertEqual(self.database.read_bytes(), before)
        result = self.post("confirm", content, preview_id=checked["preview_id"])
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["created_count"], 2)
        self.assertEqual(result.json()["skipped_count"], 2)
        self.assertEqual(
            self.client.get(f"/projects/{original['id']}").json(), original
        )
        self.assertEqual(
            self.post("confirm", content, preview_id=checked["preview_id"]).status_code,
            409,
        )
        with TestClient(create_app(self.database)) as reopened:
            stored = reopened.get("/projects").json()
            self.assertEqual(len(stored), 3)
            self.assertIn(
                ("000072", "0008", "West Yard, Phase 2"),
                [(r["job_number"], r["site_id"], r["site_name"]) for r in stored],
            )
        self.assertEqual(self.post("preview", content).json()["ready_count"], 0)

    def test_tsv_quoted_tabs_multiline_cells_and_physical_source_lines(self):
        content = (
            '"Project Number"\t"Site ID"\t"Site Name"\r\n'
            '000073\t0009\t"First\tphase\r\nSecond ""phase"""\r\n'
            "SYN-EXTRA\t01\tName\tExtra\r\n"
        )
        result = self.post("preview", content).json()
        self.assertEqual((result["ready_count"], result["skipped_count"]), (1, 1))
        first, extra = result["preview"]["rows"]
        self.assertEqual(first["source"], "Paste Text line 2-3")
        self.assertEqual(first["values"]["Site Name"], 'First\tphase\r\nSecond "phase"')
        self.assertEqual(extra["source"], "Paste Text line 4")
        self.assertIn("three fields", extra["diagnostics"][0]["message"])
        self.assertEqual(
            self.post(
                "preview", "Project Number\tSite ID\tSite Name\r\n" + '"unclosed'
            ).status_code,
            422,
        )
        self.assertEqual(
            self.post(
                "preview",
                "Project Number\tSite ID\tSite Name\r\n" + "A\tB\tC\r\n" * 2001,
            ).status_code,
            422,
        )

    def test_mixed_newlines_and_repeated_headers_are_not_projects(self):
        before = self.database.read_bytes()
        for delimiter in (",", "\t"):
            with self.subTest(delimiter=delimiter):
                header = delimiter.join(TEMPLATE_HEADERS)
                content = (
                    header
                    + "\r\n"
                    + delimiter.join(("000080", "0008", "North Yard"))
                    + "\n"
                    + header
                    + "\r\n"
                    + delimiter.join(("000081", "0009", "West Yard"))
                    + "\n"
                )
                response = self.post("preview", content)
                self.assertEqual(response.status_code, 200)
                result = response.json()
                self.assertEqual(
                    (result["ready_count"], result["skipped_count"]), (2, 1)
                )
                repeated = result["preview"]["rows"][1]
                self.assertEqual(repeated["status"], "Invalid")
                self.assertEqual(repeated["source"], "Paste Text line 3")
                self.assertIn("Repeated header", repeated["diagnostics"][0]["message"])
                self.assertEqual(self.database.read_bytes(), before)

    def test_csv_tab_inside_quoted_cell_does_not_change_delimiter(self):
        result = self.post("preview", HEADER + '000074,0010,"West\tYard, Phase 2"\n')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["ready_count"], 1)
        self.assertEqual(
            result.json()["preview"]["rows"][0]["values"]["Site Name"],
            "West\tYard, Phase 2",
        )

    def test_confirm_inserts_only_ready_rows_and_retry_cannot_duplicate(self):
        checked = self.post("preview").json()
        result = self.post("confirm", preview_id=checked["preview_id"])
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["created_count"], 1)
        self.assertEqual(result.json()["skipped_count"], 3)
        stored = self.client.get("/projects").json()
        self.assertEqual(stored[0]["job_number"], "0002")
        self.assertEqual(stored[0]["site_id"], "0002")
        self.assertEqual(stored[0]["site_name"], "Synthetic, yard")
        self.assertEqual(
            self.post("confirm", preview_id=checked["preview_id"]).status_code, 409
        )
        self.assertEqual(self.client.get("/projects").json(), stored)
        fresh = self.post("preview").json()
        self.assertEqual(fresh["ready_count"], 0)
        self.assertEqual(
            self.post("confirm", preview_id=fresh["preview_id"]).status_code, 422
        )
        with TestClient(create_app(self.database)) as reopened:
            self.assertEqual(reopened.get("/projects").json(), stored)

    def test_existing_project_and_work_item_are_never_overwritten(self):
        old = self.client.post(
            "/projects",
            json={
                "job_number": "SYN-EXIST",
                "site_id": "001",
                "site_name": "Keep",
                "work_items": [
                    {
                        "type": "Civil",
                        "required_crew_count": 2,
                        "estimated_half_days": 3,
                    }
                ],
            },
        ).json()
        content = HEADER + "syn-exist,999,Do not overwrite\nSYN-NEW,002,New\n"
        checked = self.post("preview", content).json()
        self.assertEqual(checked["preview"]["rows"][0]["status"], "Duplicate")
        self.assertEqual(checked["preview"]["rows"][0]["action"], "Skip")
        self.assertEqual(
            self.post("confirm", content, preview_id=checked["preview_id"]).json()[
                "created_count"
            ],
            1,
        )
        self.assertEqual(self.client.get(f"/projects/{old['id']}").json(), old)

    def test_input_edit_and_matching_insert_require_fresh_preview(self):
        checked = self.post("preview").json()
        changed = self.post(
            "confirm", CSV + "SYN-LATE,05,Late\n", preview_id=checked["preview_id"]
        )
        self.assertEqual(changed.status_code, 409)
        self.assertEqual(self.client.get("/projects").json(), [])
        self.client.post(
            "/projects",
            json={
                "job_number": "0002",
                "site_id": "02",
                "site_name": "Concurrent",
                "work_items": [],
            },
        )
        self.assertEqual(
            self.post("confirm", preview_id=checked["preview_id"]).status_code, 409
        )
        self.assertEqual(len(self.client.get("/projects").json()), 1)

    def test_concurrent_confirmation_serializes_and_preserves_unique_ids(self):
        checked = self.store.preview("text", CSV)

        def confirm():
            try:
                return self.store.confirm("text", CSV, checked.preview_id)[
                    "created_count"
                ]
            except StaleBulkPreview:
                return "stale"

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: confirm(), range(2)))
        self.assertCountEqual(results, [1, "stale"])
        self.assertEqual(len(self.client.get("/projects").json()), 1)

    def test_injected_second_insert_failure_rolls_back_whole_batch_then_retries(self):
        content = HEADER + "SYN-A,01,A\nSYN-B,02,B\n"
        checked = self.post("preview", content).json()
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute(
                "CREATE TRIGGER SyntheticBulkFailure BEFORE INSERT ON Projects WHEN NEW.JobNumber='SYN-B' BEGIN SELECT RAISE(ABORT, 'Synthetic failure'); END"
            )
        response = self.post("confirm", content, preview_id=checked["preview_id"])
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("Synthetic failure", response.text)
        self.assertEqual(self.client.get("/projects").json(), [])
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute("DROP TRIGGER SyntheticBulkFailure")
        retried = self.post("confirm", content, preview_id=checked["preview_id"])
        self.assertEqual(retried.json()["created_count"], 2)

    def test_formula_numeric_identifier_and_extra_payload_are_not_imported(self):
        raw = workbook_bytes(
            [
                ["=1+1", "02", "Formula"],
                [2, "02", "Numeric ID"],
                ["SYN-ZERO", "0003", "Zeroes"],
                ["SYN-ERROR", "04", "#REF!"],
            ],
            headers=TEMPLATE_HEADERS,
        )
        checked = self.post("preview", base64.b64encode(raw).decode(), "xlsx").json()
        self.assertEqual(checked["preview"]["counts"], {"Invalid": 3, "Ready": 1})
        self.assertTrue(
            any(
                d["source"].endswith("A2")
                for d in checked["preview"]["rows"][0]["diagnostics"]
            )
        )
        extra = workbook_bytes(
            [["SYN-WORK", "01", "Work", "Civil", 1, 3]],
            headers=(
                *TEMPLATE_HEADERS,
                "Crew Type",
                "Crew Count",
                "Estimated Half-days",
            ),
        )
        result = self.post("preview", base64.b64encode(extra).decode(), "xlsx").json()
        self.assertEqual(result["ready_count"], 0)
        self.assertEqual(result["preview"]["rows"][0]["status"], "Invalid")

    def test_template_has_exact_headers_text_format_and_offline_roundtrip(self):
        response = self.client.get("/bulk-projects/template").json()
        raw = base64.b64decode(response["content"])
        workbook = load_workbook(BytesIO(raw))
        sheet = workbook.active
        self.assertEqual(tuple(cell.value for cell in sheet[1]), TEMPLATE_HEADERS)
        self.assertEqual(sheet["A2"].number_format, "@")
        sheet["A2"] = "0000004"
        sheet["B2"] = "0005"
        sheet["C2"] = "Template yard"
        output = BytesIO()
        workbook.save(output)
        workbook.close()
        content = base64.b64encode(output.getvalue()).decode()
        checked = self.post("preview", content, "xlsx").json()
        self.assertEqual(checked["ready_count"], 1)
        self.assertEqual(
            self.post(
                "confirm", content, "xlsx", preview_id=checked["preview_id"]
            ).json()["created_count"],
            1,
        )
        self.assertEqual(
            self.client.get("/projects").json()[0]["job_number"], "0000004"
        )

    def test_malformed_csv_limits_headers_and_sanitized_workbook_failures(self):
        for content in [
            "Job #,Site ID,Site Name\nA,B,C",
            HEADER + '"unclosed',
            HEADER + ("A,B,C\n" * 2001),
        ]:
            self.assertEqual(self.post("preview", content).status_code, 422)
        invalid = self.post("preview", HEADER + "SYN-A,01,Name,Extra\n").json()
        self.assertEqual(invalid["preview"]["counts"], {"Invalid": 1})
        for content in [
            "bad base64",
            base64.b64encode(b"synthetic-not-a-workbook").decode(),
        ]:
            response = self.post("preview", content, "xlsx")
            self.assertEqual(response.status_code, 422)
            self.assertNotIn("synthetic-not", response.text)
        with self.assertRaises(PreviewError):
            preview_bulk("text", "x" * (5 * 1024 * 1024 + 1), {})

    def test_multiline_csv_has_traceable_lines_and_quoted_site_name(self):
        checked = self.post(
            "preview", HEADER + 'SYN-LINES,01,"First line\nSecond line"\n'
        ).json()
        self.assertEqual(checked["preview"]["rows"][0]["source"], "Paste Text line 2-3")
        self.assertEqual(checked["ready_count"], 1)
