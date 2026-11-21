import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from fastapi.testclient import TestClient

from rigarus_backend.api import create_app


def project(
    job_number="DEMO-26001", site_id="0042", site_name="Synthetic site", items=()
):
    return dict(
        job_number=job_number,
        site_id=site_id,
        site_name=site_name,
        work_items=list(items),
    )


def work_item(kind, crews, half_days, item_id=None):
    return dict(
        id=item_id, type=kind, required_crew_count=crews, estimated_half_days=half_days
    )


class ProjectApiTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / "rigarus.db"

    def test_editor_text_contract_preserves_open_formats_and_valid_counts(self):
        with TestClient(create_app(self.database)) as client:
            for field, label in (
                ("job_number", "Job #"),
                ("site_id", "Site ID"),
                ("site_name", "site name"),
            ):
                for value in ("", " \t", "\u001c", "\u0085", "A\0B"):
                    with self.subTest(field=field, value=repr(value)):
                        draft = project()
                        draft[field] = value
                        response = client.post("/projects", json=draft)
                        self.assertEqual(response.status_code, 422)
                        self.assertEqual(
                            response.json()["detail"], f"Enter a valid {label}."
                        )
            self.assertEqual(client.get("/projects").json(), [])
            for job, site in (("项目 Ω/?", "S-104"), ("\ufeff", "1")):
                response = client.post(
                    "/projects",
                    json=project(job, site, items=[work_item("Small", 2, 4)]),
                )
                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.json()["job_number"], job)
                self.assertEqual(response.json()["site_id"], site)
                self.assertEqual(
                    response.json()["work_items"][0]["estimated_half_days"], 4
                )

    def test_create_search_edit_and_reopen_existing_project(self):
        with TestClient(create_app(self.database)) as client:
            self.assertEqual(client.get("/projects").json(), [])
            created = client.post("/projects", json=project(job_number=" DEMO-26001 "))
            self.assertEqual(created.status_code, 201)
            project_id = created.json()["id"]
            self.assertEqual(created.json()["work_items"], [])
            url = f"/projects/{project_id}"
            changed = client.put(
                url,
                json=project(
                    site_name="Synthetic 100% site",
                    items=[work_item("Civil", 1, 2), work_item("Tower", 2, 3)],
                ),
            ).json()
            civil, tower = changed["work_items"]
            self.assertEqual(
                client.put(
                    url,
                    json=project(
                        site_name=changed["site_name"],
                        items=[work_item("Civil", 3, 5, civil["id"])],
                    ),
                ).status_code,
                200,
            )
            for term in ("demo-26001", "0042", "100%", " synthetic "):
                rows = client.get("/projects", params={"term": term}).json()
                self.assertEqual(
                    [(row["id"], row["work_item_count"]) for row in rows],
                    [(project_id, 2)],
                )
            self.assertEqual(client.get("/projects", params={"term": "_"}).json(), [])

        with TestClient(create_app(self.database)) as reopened:
            saved = reopened.get(url).json()
            self.assertEqual(saved["job_number"], "DEMO-26001")
            self.assertEqual(
                saved["work_items"], [work_item("Civil", 3, 5, civil["id"]), tower]
            )
            self.assertEqual(reopened.get("/demo").json()["job_number"], "DEMO-001")

    def test_duplicate_and_invalid_work_item_edits_are_atomic(self):
        with TestClient(create_app(self.database)) as client:
            first = client.post(
                "/projects", json=project(items=[work_item("Small", 1, 1)])
            ).json()
            other = client.post(
                "/projects",
                json=project("DEMO-26002", items=[work_item("Other", 1, 1)]),
            ).json()
            url = f"/projects/{first['id']}"
            self.assertEqual(
                client.post("/projects", json=project("demo-26001")).status_code, 409
            )
            self.assertEqual(
                client.put(url, json=project("demo-26002")).status_code, 409
            )
            for invalid in (1.5, True, 0, 2147483648):
                self.assertEqual(
                    client.put(
                        url, json=project(items=[work_item("Civil", 1, invalid)])
                    ).status_code,
                    422,
                )
            own_id = first["work_items"][0]["id"]
            for wrong_id in (other["work_items"][0]["id"], own_id):
                self.assertEqual(
                    client.put(
                        url,
                        json=project(
                            site_name="Should roll back",
                            items=[
                                work_item("Civil", 2, 3, own_id),
                                work_item("Tower", 1, 2, wrong_id),
                            ],
                        ),
                    ).status_code,
                    422,
                )
                self.assertEqual(client.get(url).json(), first)
            self.assertEqual(
                client.put(url, json=project(site_id=" ")).status_code, 422
            )
            self.assertEqual(client.get("/projects/2147483647").status_code, 404)

    def test_legacy_fixture_and_large_backlog(self):
        fixture = Path(__file__).with_name("fixtures") / "legacy_ef_schema.sql"
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.executescript(fixture.read_text(encoding="utf-8"))
            connection.execute("UPDATE DemoProjects SET Note = 'Legacy synthetic note'")
            connection.execute(
                "INSERT INTO Projects VALUES (42, 'LEGACY-42', '0042', 'Legacy site')"
            )
            connection.execute("INSERT INTO WorkItems VALUES (75, 42, 'Tower', 1, 2)")
            connection.executemany(
                "INSERT INTO Projects (JobNumber, SiteId, SiteName) VALUES (?, '0001', 'Synthetic yard')",
                [(f"DEMO-{number:03d}",) for number in range(121)],
            )
        with TestClient(create_app(self.database)) as client:
            self.assertEqual(len(client.get("/projects").json()), 122)
            self.assertEqual(
                len(client.get("/projects", params={"term": "DEMO-120"}).json()), 1
            )
            self.assertEqual(
                client.get("/projects/42").json()["work_items"],
                [work_item("Tower", 1, 2, 75)],
            )
            self.assertEqual(
                client.get("/demo").json()["note"], "Legacy synthetic note"
            )
