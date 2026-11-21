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


class SidecarTests(unittest.TestCase):
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
        restarted.stdin.close()
        self.assertEqual(restarted.wait(timeout=10), 0)
