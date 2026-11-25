import concurrent.futures
import base64
import hashlib
import http.client
import json
import os
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from test_import_preview import workbook_bytes
from migration_fixture import remove_staffing_schema
from rigarus_backend.storage import DRAFT_ASSIGNMENTS, initialize_database


class SidecarTests(unittest.TestCase):
    def test_daily_inputs_authenticated_slotless_and_default_write_gate_closed(self):
        token = secrets.token_hex(32)
        process = self.launch(token)
        port = self.read_port(process)
        status, crew = self.request(
            port,
            "POST",
            "/crews",
            token,
            payload=dict(name="Synthetic daily Crew", type="Civil"),
        )
        self.assertEqual(status, 201)
        route = f"/daily-calendars/Crew/{crew['id']}"
        query = "?start_date=2026-12-31&end_date=2026-12-31"
        self.assertEqual(self.request(port, "GET", route + query)[0], 401)
        status, observed = self.request(port, "GET", route + query, token)
        self.assertEqual(status, 200)
        self.assertEqual(observed["entries"][0]["state"], "Unknown")
        body = dict(
            start_date="2026-12-31",
            end_date="2026-12-31",
            state="Working",
            confirmed_by_operator=True,
            expected_revision=0,
            expected_review_token=observed["review_token"],
        )
        self.assertEqual(self.request(port, "PUT", route, payload=body)[0], 401)
        self.assertEqual(self.request(port, "PUT", route, token, payload=body)[0], 409)
        self.assertEqual(
            self.request(port, "PUT", route, token, payload=body | dict(slot="AM"))[0],
            422,
        )
        self.assertEqual(
            self.request(port, "GET", route + "/history", token), (200, [])
        )
        self.assertEqual(self.request(port, "GET", route + query, token)[1], observed)
        process.stdin.close()
        self.assertEqual(process.wait(timeout=10), 0)

    def test_day_contract_is_authenticated_and_default_writes_are_closed(self):
        token = secrets.token_hex(32)
        process = self.launch(token)
        port = self.read_port(process)
        route = "/day-draft-assignments?start_date=2026-12-31&end_date=2027-01-01"
        self.assertEqual(self.request(port, "GET", route)[0], 401)
        self.assertEqual(self.request(port, "GET", route, token), (200, []))
        body = dict(work_item_id=1, crew_id=1, local_date="2026-12-31")
        self.assertEqual(
            self.request(port, "POST", "/day-draft-assignments", token, payload=body)[
                0
            ],
            409,
        )
        self.assertEqual(
            self.request(
                port,
                "POST",
                "/day-draft-assignments",
                token,
                payload=body | dict(slot="AM"),
            )[0],
            422,
        )
        status, report = self.request(
            port,
            "GET",
            "/day-draft-assignments/legacy-compatibility?start_date=2026-12-31&end_date=2027-01-01",
            token,
        )
        self.assertEqual(status, 200)
        self.assertFalse(report["applyable"] or report["publishable"])
        self.assertEqual(report["converted_records"], 0)
        process.stdin.close()
        self.assertEqual(process.wait(timeout=10), 0)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / "data" / "rigarus.db"

    def launch(self, token):
        packaged = os.environ.get("RIGARUS_SIDECAR_TEST_EXE")
        command = (
            [packaged]
            if packaged
            else [sys.executable, "-m", "rigarus_backend.sidecar"]
        )
        process = subprocess.Popen(
            [*command, "--database", str(self.database)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        self.addCleanup(self.cleanup_process, process)
        process.stdin.write(token + "\n")
        process.stdin.flush()
        return process

    @staticmethod
    def cleanup_process(process):
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=10)

    @staticmethod
    def read_port(process):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            output = executor.submit(process.stdout.readline)
            try:
                line = output.result(timeout=20)
            except TimeoutError:
                process.kill()
                raise
        message = json.loads(line)
        if message["event"] != "ready":
            raise AssertionError("The sidecar did not report readiness.")
        return message["port"]

    @staticmethod
    def request(port, method, route, token=None, note=None, headers=None, payload=None):
        request_headers = dict(headers or {})
        if token is not None:
            request_headers["Authorization"] = "Bearer " + token
        body = None
        if note is not None:
            payload = {"note": note}
        if payload is not None:
            body = json.dumps(payload)
            request_headers["Content-Type"] = "application/json"
        with closing(
            http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        ) as connection:
            connection.request(method, route, body=body, headers=request_headers)
            response = connection.getresponse()
            return response.status, json.loads(response.read())

    def test_project_working_calendar_authentication_inheritance_and_restart(self):
        token = secrets.token_hex(32)
        process = self.launch(token)
        port = self.read_port(process)
        project = self.request(
            port,
            "POST",
            "/projects",
            token,
            payload={
                "job_number": "SYN-CALENDAR",
                "site_id": "0007",
                "site_name": "Synthetic calendar site",
                "work_items": [
                    {
                        "type": "Civil",
                        "required_crew_count": 1,
                        "estimated_half_days": 1,
                    },
                    {
                        "type": "Tower",
                        "required_crew_count": 1,
                        "estimated_half_days": 2,
                    },
                ],
            },
        )[1]
        crew = self.request(
            port,
            "POST",
            "/crews",
            token,
            payload={"name": "Synthetic calendar Crew", "type": "Civil"},
        )[1]
        route = f"/working-calendars/Project/{project['id']}"
        query = "?start_date=2026-12-31&end_date=2027-01-01"
        self.assertEqual(self.request(port, "GET", route + query)[0], 401)
        payload = {
            "start_date": "2026-12-31",
            "end_date": "2027-01-01",
            "slot": "FullDay",
            "state": "NotWorking",
            "expected_revision": 0,
        }
        self.assertEqual(
            self.request(port, "PUT", route, "wrong", payload=payload)[0], 401
        )
        saved = self.request(port, "PUT", route, token, payload=payload)
        self.assertEqual(saved[0], 200)
        for item in project["work_items"]:
            result = self.request(
                port,
                "GET",
                f"/working-calendars/assessment?work_item_id={item['id']}&crew_id={crew['id']}&local_date=2026-12-31&slot=AM",
                token,
            )[1]
            self.assertEqual(result["project_id"], project["id"])
            self.assertEqual(result["status"], "Blocked")
            self.assertFalse(result["publishable"])
        process.stdin.close()
        process.stdin = None
        process.wait(timeout=10)
        self.assertEqual(process.returncode, 0)
        reopened = self.launch(token)
        port = self.read_port(reopened)
        self.assertEqual(self.request(port, "GET", route + query, token), saved)
        self.assertEqual(
            len(self.request(port, "GET", route + "/history", token)[1]), 1
        )

    def test_authenticated_demo_roundtrip_across_parent_pipe_shutdown(self):
        token = secrets.token_hex(32)
        process = self.launch(token)
        port = self.read_port(process)

        self.assertEqual(
            self.request(port, "GET", "/health", token), (200, {"status": "ready"})
        )
        self.assertEqual(self.request(port, "GET", "/demo")[0], 401)
        self.assertEqual(
            self.request(port, "PUT", "/demo/note", "incorrect", "Forbidden")[0], 401
        )
        self.assertEqual(
            self.request(
                port, "GET", "/demo", token, headers={"Host": "outside.invalid"}
            )[0],
            401,
        )
        self.assertEqual(
            self.request(port, "GET", "/demo", token)[1]["note"],
            "Synthetic sample for M0.",
        )
        self.assertEqual(
            self.request(port, "PUT", "/demo/note", token, "Synthetic sidecar note")[0],
            200,
        )

        process.stdin.close()
        self.assertEqual(process.wait(timeout=10), 0)
        with self.assertRaises(OSError):
            self.request(port, "GET", "/health", token)

        next_token = secrets.token_hex(32)
        restarted = self.launch(next_token)
        next_port = self.read_port(restarted)
        self.assertEqual(self.request(next_port, "GET", "/demo", token)[0], 401)
        self.assertEqual(
            self.request(next_port, "GET", "/demo", next_token)[1]["note"],
            "Synthetic sidecar note",
        )
        restarted.stdin.close()
        self.assertEqual(restarted.wait(timeout=10), 0)

    def test_foreman_api_is_authenticated_and_history_survives_sidecar_restart(self):
        token = secrets.token_hex(32)
        process = self.launch(token)
        port = self.read_port(process)
        _, crew = self.request(
            port,
            "POST",
            "/crews",
            token,
            payload={"name": "Synthetic Foreman crew", "type": "Civil"},
        )
        _, person = self.request(
            port,
            "POST",
            "/employees",
            token,
            payload={
                "name": "Synthetic Foreman candidate",
                "home_crew_id": crew["id"],
                "skill_level": 1,
                "foreman_eligible": True,
            },
        )
        route = f"/crews/{crew['id']}/foreman"
        change = {"employee_id": person["id"], "expected_revision": 0}
        self.assertEqual(self.request(port, "GET", route)[0], 401)
        self.assertEqual(
            self.request(port, "PUT", route, "incorrect", payload=change)[0], 401
        )
        status, saved = self.request(port, "PUT", route, token, payload=change)
        self.assertEqual(status, 200)
        self.assertEqual(saved["employee_id"], person["id"])
        process.stdin.close()
        self.assertEqual(process.wait(timeout=10), 0)
        restarted = self.launch(token)
        next_port = self.read_port(restarted)
        self.assertEqual(self.request(next_port, "GET", route, token), (200, saved))
        self.assertEqual(
            self.request(next_port, "PUT", route, token, payload=change)[0], 409
        )
        status, cleared = self.request(
            next_port,
            "PUT",
            route,
            token,
            payload={"employee_id": None, "expected_revision": saved["revision"]},
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(cleared["history"]), 2)
        self.assertIsNone(cleared["employee_id"])
        restarted.stdin.close()
        self.assertEqual(restarted.wait(timeout=10), 0)

    def test_assignment_api_is_authenticated_persistent_and_not_publishable(self):
        token = secrets.token_hex(32)
        process = self.launch(token)
        port = self.read_port(process)
        _, project = self.request(
            port,
            "POST",
            "/projects",
            token,
            payload={
                "job_number": "SYN-14",
                "site_id": "0014",
                "site_name": "Synthetic assignment site",
                "work_items": [
                    {
                        "type": "Civil",
                        "required_crew_count": 1,
                        "estimated_half_days": 1,
                    }
                ],
            },
        )
        _, crew = self.request(
            port,
            "POST",
            "/crews",
            token,
            payload={"name": "Synthetic assignment crew", "type": "Civil"},
        )
        draft = {
            "work_item_id": project["work_items"][0]["id"],
            "crew_id": crew["id"],
            "local_date": "2026-12-31",
            "slot": "AM",
            "notes": "Synthetic sidecar visit",
        }
        self.assertEqual(
            self.request(port, "POST", "/draft-assignments", payload=draft)[0], 401
        )
        status, saved = self.request(
            port, "POST", "/draft-assignments", token, payload=draft
        )
        self.assertEqual(status, 201)
        self.assertFalse(saved["publishable"])
        self.assertEqual(saved["validation_status"], "Pending")
        self.assertEqual(
            self.request(port, "POST", "/draft-assignments", token, payload=draft)[0],
            409,
        )
        self.assertEqual(
            self.request(
                port,
                "POST",
                "/draft-assignments",
                token,
                payload={**draft, "slot": "PM"},
            )[0],
            201,
        )
        process.stdin.close()
        self.assertEqual(process.wait(timeout=10), 0)
        restarted = self.launch(token)
        next_port = self.read_port(restarted)
        route = f"/draft-assignments/{saved['id']}"
        self.assertEqual(self.request(next_port, "GET", route, token), (200, saved))
        self.assertEqual(
            len(
                self.request(
                    next_port,
                    "GET",
                    "/draft-assignments?start_date=2026-12-31&end_date=2027-01-01",
                    token,
                )[1]
            ),
            2,
        )
        status, cancelled = self.request(
            next_port,
            "POST",
            route + "/cancel",
            token,
            payload={"expected_revision": 1},
        )
        self.assertEqual(status, 200)
        self.assertEqual(cancelled["status"], "Cancelled")
        self.assertEqual(
            self.request(next_port, "POST", route + "/publish", token)[0], 404
        )
        restarted.stdin.close()
        self.assertEqual(restarted.wait(timeout=10), 0)

    def test_assignment_upgrade_from_six_migrations_preserves_existing_records(self):
        initialize_database(self.database)
        with closing(sqlite3.connect(self.database)) as connection, connection:
            remove_staffing_schema(connection)
            connection.execute("DROP TABLE DraftAssignments")
            connection.execute(
                "DELETE FROM __EFMigrationsHistory WHERE MigrationId=?",
                (DRAFT_ASSIGNMENTS,),
            )
            connection.execute(
                "UPDATE DemoProjects SET Note='Synthetic six-schema note'"
            )
            connection.execute(
                "INSERT INTO Projects VALUES (90,'SYN-OLD14','0090','Synthetic old site')"
            )
            connection.execute("INSERT INTO WorkItems VALUES (91,90,'Tower',1,3)")
            connection.execute(
                "INSERT INTO Crews VALUES (92,'Synthetic old Crew','Tower',1)"
            )
            connection.execute(
                "INSERT INTO Employees VALUES (93,'Synthetic old employee',92,2,1,1,'Unverified')"
            )
            connection.execute(
                "INSERT INTO Rigs VALUES (94,'0094','Synthetic rig','Retained synthetic rig note',92,1)"
            )
            connection.execute(
                "INSERT INTO ForemanChanges VALUES (95,92,93,'Synthetic old Crew','Synthetic old employee','2026-11-21T00:00:00+00:00')"
            )
            tables = (
                "DemoProjects",
                "Projects",
                "WorkItems",
                "Crews",
                "Employees",
                "Rigs",
                "ForemanChanges",
            )
            before = {
                table: connection.execute(f"SELECT * FROM {table}").fetchall()
                for table in tables
            }
        token = secrets.token_hex(32)
        process = self.launch(token)
        port = self.read_port(process)
        self.assertEqual(
            self.request(port, "GET", "/demo", token)[1]["note"],
            "Synthetic six-schema note",
        )
        status, saved = self.request(
            port,
            "POST",
            "/draft-assignments",
            token,
            payload={
                "work_item_id": 91,
                "crew_id": 92,
                "local_date": "2026-12-31",
                "slot": "AM",
            },
        )
        self.assertEqual(status, 201)
        self.assertEqual(saved["project_id"], 90)
        process.stdin.close()
        self.assertEqual(process.wait(timeout=10), 0)
        with closing(sqlite3.connect(self.database)) as connection:
            for table, rows in before.items():
                self.assertEqual(
                    connection.execute(f"SELECT * FROM {table}").fetchall(), rows
                )
            self.assertEqual(
                connection.execute(
                    "SELECT count(*) FROM __EFMigrationsHistory"
                ).fetchone(),
                (18,),
            )
            self.assertEqual(
                connection.execute("PRAGMA integrity_check").fetchone(), ("ok",)
            )
            self.assertEqual(
                connection.execute("PRAGMA foreign_key_check").fetchall(), []
            )

    def test_explicit_workers_authenticated_restart_and_home_crew_retention(self):
        token = secrets.token_hex(32)
        process = self.launch(token)
        port = self.read_port(process)

        def request(method, route, payload=None):
            status, value = self.request(port, method, route, token, payload=payload)
            self.assertIn(status, (200, 201), value)
            return value

        home = request("POST", "/crews", {"name": "Synthetic home", "type": "Civil"})
        crew = request(
            "POST", "/crews", {"name": "Synthetic borrowed Crew", "type": "Tower"}
        )
        person = request(
            "POST",
            "/employees",
            {
                "name": "Synthetic worker",
                "home_crew_id": home["id"],
                "skill_level": 1,
                "foreman_eligible": False,
            },
        )
        project = request(
            "POST",
            "/projects",
            {
                "job_number": "SYN-0022",
                "site_id": "0022",
                "site_name": "Synthetic staffing site",
                "work_items": [
                    {
                        "type": "Tower",
                        "required_crew_count": 1,
                        "estimated_half_days": 1,
                    }
                ],
            },
        )
        assignment = request(
            "POST",
            "/draft-assignments",
            {
                "work_item_id": project["work_items"][0]["id"],
                "crew_id": crew["id"],
                "local_date": "2026-12-31",
                "slot": "AM",
            },
        )
        route = f"/draft-assignments/{assignment['id']}/staffing"
        self.assertEqual(
            self.request(
                port,
                "PUT",
                route,
                "incorrect",
                payload={"employee_ids": [person["id"]], "expected_revision": 1},
            )[0],
            401,
        )
        saved = request(
            "PUT", route, {"employee_ids": [person["id"]], "expected_revision": 1}
        )
        self.assertEqual(saved["staffing"]["workers"][0]["home_crew_id"], home["id"])
        self.assertFalse(saved["publishable"])
        process.stdin.close()
        self.assertEqual(process.wait(timeout=10), 0)
        process = self.launch(token)
        port = self.read_port(process)
        self.assertEqual(
            request("GET", f"/draft-assignments?employee_id={person['id']}"), [saved]
        )
        self.assertEqual(
            request("GET", f"/draft-assignments/{assignment['id']}/staffing-history")[
                0
            ]["members"][0]["employee_id"],
            person["id"],
        )
        self.assertEqual(request("GET", "/employees"), [person])
        process.stdin.close()
        self.assertEqual(process.wait(timeout=10), 0)

    def test_availability_is_authenticated_and_survives_pipe_restart(self):
        token = secrets.token_hex(32)
        process = self.launch(token)
        port = self.read_port(process)

        def request(method, route, payload=None):
            status, value = self.request(port, method, route, token, payload=payload)
            self.assertIn(status, (200, 201), value)
            return value

        crew = request(
            "POST", "/crews", {"name": "Synthetic availability Crew", "type": "Civil"}
        )
        person = request(
            "POST",
            "/employees",
            {
                "name": "Synthetic availability employee",
                "home_crew_id": crew["id"],
                "skill_level": 1,
                "foreman_eligible": False,
            },
        )
        route = f"/employees/{person['id']}/availability"
        payload = {
            "start_date": "2026-12-31",
            "end_date": "2027-01-01",
            "slot": "FullDay",
            "state": "Unavailable",
            "expected_revision": 0,
        }
        self.assertEqual(
            self.request(port, "PUT", route, "incorrect", payload=payload)[0], 401
        )
        saved = request("PUT", route, payload)
        self.assertEqual(len(saved["entries"]), 4)
        process.stdin.close()
        self.assertEqual(process.wait(timeout=10), 0)
        process = self.launch(token)
        port = self.read_port(process)
        self.assertEqual(
            request("GET", route + "?start_date=2026-12-31&end_date=2027-01-01"), saved
        )
        self.assertEqual(
            request("GET", "/employee-availability?local_date=2026-12-31&slot=AM")[
                "employees"
            ],
            [{"employee_id": person["id"], "state": "Unavailable"}],
        )
        self.assertEqual(request("GET", route + "/history")[0]["revision"], 1)
        self.assertEqual(request("GET", "/employees"), [person])
        process.stdin.close()
        self.assertEqual(process.wait(timeout=10), 0)

    def test_rig_api_is_authenticated_and_persists_across_sidecar_restart(self):
        token = secrets.token_hex(32)
        process = self.launch(token)
        port = self.read_port(process)
        draft = {"number": "SYN-RIG-009", "type": "Synthetic truck"}
        self.assertEqual(self.request(port, "POST", "/rigs", payload=draft)[0], 401)
        code, rig = self.request(port, "POST", "/rigs", token, payload=draft)
        self.assertEqual(code, 201)
        process.stdin.close()
        self.assertEqual(process.wait(timeout=10), 0)
        restarted = self.launch(token)
        port = self.read_port(restarted)
        self.assertEqual(self.request(port, "GET", "/rigs", token), (200, [rig]))
        restarted.stdin.close()
        self.assertEqual(restarted.wait(timeout=10), 0)

    def test_workbook_preview_is_authenticated_read_only_and_packaged(self):
        token = secrets.token_hex(32)
        process = self.launch(token)
        port = self.read_port(process)
        content = workbook_bytes(
            [["SYN-011", "0011", "Synthetic import yard"]],
            headers=("Job #", "Site ID", "Site Name"),
        )
        payload = {"content": base64.b64encode(content).decode("ascii")}
        digest = hashlib.sha256(self.database.read_bytes()).digest()
        self.assertEqual(
            self.request(port, "POST", "/import-preview", payload=payload)[0], 401
        )
        code, preview = self.request(
            port, "POST", "/import-preview", token, payload=payload
        )
        self.assertEqual(code, 200)
        self.assertEqual(preview["rows"][0]["status"], "Ready")
        self.assertEqual(preview["rows"][0]["source"], "'Synthetic Plan'!A2:C2")
        self.assertEqual(hashlib.sha256(self.database.read_bytes()).digest(), digest)
        process.stdin.close()
        self.assertEqual(process.wait(timeout=10), 0)

    def test_startup_rejects_unknown_database_with_recovery_hint(self):
        self.database.parent.mkdir()
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("CREATE TABLE Unrelated (Id INTEGER)")
        process = self.launch(secrets.token_hex(32))
        stdout, stderr = process.communicate(timeout=20)
        self.assertEqual(process.returncode, 1)
        self.assertEqual(stdout, "")
        self.assertIn("compatible version of Rigarus", stderr)
        self.assertNotIn(str(self.database), stderr)

    def test_bulk_projects_template_preview_confirm_are_authenticated_and_packaged(
        self,
    ):
        token = secrets.token_hex(32)
        process = self.launch(token)
        port = self.read_port(process)
        content = base64.b64encode(
            workbook_bytes(
                [["000045", "0002", "Packaged bulk yard"]],
                headers=("Project Number", "Site ID", "Site Name"),
            )
        ).decode("ascii")
        payload = {"kind": "xlsx", "content": content}
        for route in ("/bulk-projects/preview", "/bulk-projects/confirm"):
            self.assertEqual(self.request(port, "POST", route, payload=payload)[0], 401)
        self.assertEqual(self.request(port, "GET", "/bulk-projects/template")[0], 401)
        self.assertEqual(
            self.request(port, "GET", "/bulk-projects/template", token)[0], 200
        )
        digest = hashlib.sha256(self.database.read_bytes()).digest()
        code, checked = self.request(
            port, "POST", "/bulk-projects/preview", token, payload=payload
        )
        self.assertEqual(code, 200)
        self.assertEqual(checked["ready_count"], 1)
        self.assertEqual(hashlib.sha256(self.database.read_bytes()).digest(), digest)
        payload["preview_id"] = checked["preview_id"]
        code, result = self.request(
            port, "POST", "/bulk-projects/confirm", token, payload=payload
        )
        self.assertEqual(code, 200)
        self.assertEqual(result["created_count"], 1)
        self.assertEqual(
            self.request(
                port, "POST", "/bulk-projects/confirm", token, payload=payload
            )[0],
            409,
        )
        process.stdin.close()
        self.assertEqual(process.wait(timeout=10), 0)
        restarted = self.launch(token)
        port = self.read_port(restarted)
        projects = self.request(port, "GET", "/projects", token)[1]
        self.assertEqual(projects[0]["job_number"], "000045")
        self.assertEqual(projects[0]["site_id"], "0002")
        tsv = {
            "kind": "text",
            "content": "Project Number\tSite ID\tSite Name\r\n000046\t0003\tTSV, yard\r\n",
        }
        code, checked_tsv = self.request(
            port, "POST", "/bulk-projects/preview", token, payload=tsv
        )
        self.assertEqual(code, 200)
        self.assertEqual(checked_tsv["ready_count"], 1)
        tsv["preview_id"] = checked_tsv["preview_id"]
        code, saved_tsv = self.request(
            port, "POST", "/bulk-projects/confirm", token, payload=tsv
        )
        self.assertEqual(code, 200)
        self.assertEqual(saved_tsv["created_count"], 1)
        self.assertEqual(len(self.request(port, "GET", "/projects", token)[1]), 2)
        restarted.stdin.close()
        self.assertEqual(restarted.wait(timeout=10), 0)
