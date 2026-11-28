"""Explicit synthetic-only native transport faults. Never changes sealed SQL receipts.

No HTTP control endpoint. Fixed local manifest, bounded delay and durable one-shot
claim survive sidecar restarts. This is fault injection, not simulated packet loss.
"""

import asyncio
import hashlib
import json
import os
from pathlib import Path
from uuid import UUID

from starlette.responses import JSONResponse

from .draft_apply import read_status

FORMAT = "rigarus-restore-fault-v1"
MODES = {
    "none",
    "after_commit_timeout",
    "before_commit_timeout",
    "refresh_once",
    "wrong_profile_once",
}
DELAY_SECONDS = 65
LIMIT = 8_000_000


def bounded_json(path, limit=4096):
    with Path(path).open("rb") as file:
        data = file.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Synthetic fault state is too large.")
    return json.loads(data)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def manifest(database, root, *, restore_enabled):
    if not restore_enabled or not root:
        raise ValueError("Fault injection requires the independent Restore test gate.")
    root = Path(root).resolve()
    if Path(database).resolve() != root / "data" / "rigarus.db":
        raise ValueError("Fault injection requires the exact synthetic database.")
    value = bounded_json(root / "data" / "restore-fault.json")
    if (
        not isinstance(value, dict)
        or set(value)
        != {
            "format",
            "synthetic_only",
            "profile_id",
            "source_version_id",
            "transport",
            "archive",
        }
        or value["format"] != FORMAT
        or value["synthetic_only"] is not True
        or type(value["source_version_id"]) is not int
        or not 0 < value["source_version_id"] <= 2_147_483_647
        or value["transport"] not in MODES
        or value["archive"] not in {"none", "write_once", "flush_once"}
        or str(UUID(value["profile_id"])) != value["profile_id"]
        or read_status(database)["database_identity"] != value["profile_id"]
    ):
        raise ValueError("Invalid synthetic fault identity or manifest.")
    return value


class RestoreFaults:
    def __init__(self, app, database, root, *, restore_enabled, sleep=asyncio.sleep):
        self.plan = manifest(database, root, restore_enabled=restore_enabled)
        self.app = app
        self.folder = Path(root).resolve() / "data" / "restore-fault-state"
        self.folder.mkdir(exist_ok=True)
        self.sleep = sleep

    def event(self, phase, request_id=None):
        # Bounded local phases only: no bearer token, headers or business payload.
        path = self.folder / "events.jsonl"
        if path.exists() and path.stat().st_size > 64_000:
            raise ValueError("Synthetic event budget exhausted.")
        import time

        with path.open("a", encoding="utf-8") as file:
            file.write(
                canonical(dict(phase=phase, request_id=request_id, utc=time.time()))
                + "\n"
            )
            file.flush()
            os.fsync(file.fileno())

    def claim(self, name, body):
        identity = dict(
            profile_id=body["profile_id"],
            source_version_id=body["source_version_id"],
            request_id=str(UUID(body["request_id"])),
            payload_sha256=hashlib.sha256(canonical(body).encode()).hexdigest(),
        )
        path = self.folder / (name + ".json")
        try:
            with path.open("x", encoding="utf-8") as file:
                file.write(canonical(identity))
                file.flush()
                os.fsync(file.fileno())
        except FileExistsError:
            if bounded_json(path) != identity:
                raise ValueError("Fault already bound to another original request.")
            return False
        return True

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        mode = self.plan["transport"]
        path = scope["path"]
        if (
            mode == "refresh_once"
            and scope["method"] == "GET"
            and path == "/schedule-workbench/week"
            and (self.folder / "committed.json").is_file()
        ):
            body = bounded_json(self.folder / "committed.json")
            if self.claim("read-failed", body):
                self.event("post_commit_read_failed", body["request_id"])
                return await JSONResponse(
                    {"detail": "Synthetic one-shot post-commit read failure."},
                    status_code=503,
                )(scope, receive, send)
        if (
            mode == "none"
            or scope["method"] != "POST"
            or path != "/draft-restores/submit"
        ):
            return await self.app(scope, receive, send)
        data = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            data.extend(message.get("body", b""))
            if len(data) > 2_000_000:
                return await JSONResponse({"detail": "Too large."}, 413)(
                    scope, receive, send
                )
            if not message.get("more_body", False):
                break
        try:
            body = json.loads(data)
            if (
                body["profile_id"] != self.plan["profile_id"]
                or body["source_version_id"] != self.plan["source_version_id"]
            ):
                raise ValueError("Fault target mismatch.")
            first = self.claim("transport", body)
        except (ValueError, KeyError, TypeError, OSError):
            return await JSONResponse(
                {"detail": "Synthetic fault state unavailable."}, 503
            )(scope, receive, send)
        used = False

        async def replay_receive():
            nonlocal used
            if not used:
                used = True
                return {"type": "http.request", "body": bytes(data), "more_body": False}
            return await receive()

        if not first:
            return await self.app(scope, replay_receive, send)
        key = body["request_id"]
        self.event("request_received", key)
        if mode == "before_commit_timeout":
            self.event("before_handler_delay", key)
            await self.sleep(DELAY_SECONDS)
            self.event("handler_not_invoked", key)
            return await JSONResponse(
                {"detail": "Synthetic request not delivered."}, 503
            )(scope, replay_receive, send)
        messages = []
        total = 0

        async def capture(message):
            nonlocal total
            total += len(message.get("body", b""))
            if total > LIMIT:
                raise ValueError(
                    "Synthetic response budget exhausted; reconcile original key."
                )
            messages.append(message)

        await self.app(scope, replay_receive, capture)
        result = json.loads(b"".join(m.get("body", b"") for m in messages))
        if result.get("outcome") == "Committed":
            self.event("real_transaction_committed", key)
            if mode == "after_commit_timeout":
                await self.sleep(DELAY_SECONDS)
                self.event("committed_response_released", key)
            if mode == "refresh_once":
                # Persist only the claim identity, not a mutable business payload.
                identity = bounded_json(self.folder / "transport.json")
                with (self.folder / "committed.json").open(
                    "x", encoding="utf-8"
                ) as file:
                    file.write(canonical(identity))
                    file.flush()
                    os.fsync(file.fileno())
            if mode == "wrong_profile_once":
                result["database_identity"] = "00000000-0000-4000-8000-000000000001"
                self.event("outgoing_profile_corrupted", key)
                return await JSONResponse(result)(scope, replay_receive, send)
        for message in messages:
            await send(message)
