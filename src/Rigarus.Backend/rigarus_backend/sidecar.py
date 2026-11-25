"""Windows desktop sidecar entry point. Standard input belongs to its parent."""

import argparse
import asyncio
import hmac
import json
import os
import re
import socket
import sqlite3
import sys
from pathlib import Path
from threading import Thread

import uvicorn
from starlette.responses import JSONResponse
from uvicorn.protocols.http.h11_impl import H11Protocol

from rigarus_backend.api import create_app
from rigarus_backend.storage import UnsupportedDatabaseError, initialize_database


def private_api(app, token: bytes):
    async def authenticated(scope, receive, send):
        if scope["type"] == "http":
            headers = scope["headers"]
            authorization = [
                value for name, value in headers if name == b"authorization"
            ]
            host = [value for name, value in headers if name == b"host"]
            expected_host = f"127.0.0.1:{scope['server'][1]}".encode("ascii")
            if (
                host != [expected_host]
                or len(authorization) != 1
                or not hmac.compare_digest(authorization[0], b"Bearer " + token)
            ):
                await JSONResponse({"detail": "Unauthorized."}, status_code=401)(
                    scope, receive, send
                )
                return
        await app(scope, receive, send)

    return authenticated


async def serve(
    listener: socket.socket, database: Path, token: bytes, *, editor_test=False
) -> bool:
    app = private_api(
        create_app(
            database,
            database_initialized=True,
            enable_day_editor_test_writes=editor_test,
        ),
        token,
    )
    config = uvicorn.Config(
        app,
        loop="asyncio",
        http=H11Protocol,
        ws="none",
        lifespan="on",
        interface="asgi3",
        workers=1,
        access_log=False,
        log_level="critical",
        proxy_headers=False,
        timeout_graceful_shutdown=5,
    )
    server = uvicorn.Server(config)
    loop = asyncio.get_running_loop()

    def stop_on_parent_exit():
        # The parent owns the write end. Its close or exit delivers EOF.
        try:
            while sys.stdin.buffer.read(1):
                pass
        except OSError:
            pass
        try:
            loop.call_soon_threadsafe(setattr, server, "should_exit", True)
        except RuntimeError:
            pass  # The event loop already shut down.

    Thread(target=stop_on_parent_exit, daemon=True).start()
    task = asyncio.create_task(server.serve(sockets=[listener]))
    while not server.started and not task.done():
        await asyncio.sleep(0.02)
    if server.started and not server.should_exit:
        print(
            json.dumps({"event": "ready", "port": listener.getsockname()[1]}),
            flush=True,
        )
    await task
    return server.started or server.should_exit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--synthetic-day-editor", action="store_true")
    arguments = parser.parse_args()
    if arguments.synthetic_day_editor:
        root = os.environ.get("RIGARUS_SMOKE_DATA_ROOT", "")
        if (
            not root
            or arguments.database.resolve()
            != (Path(root) / "data" / "rigarus.db").resolve()
        ):
            parser.error(
                "Synthetic day editor requires its separate smoke-root database."
            )

    # Pass the per-launch secret over the pipe, not via command line or logs.
    token = sys.stdin.buffer.readline(66).rstrip(b"\r\n")
    if not re.fullmatch(rb"[a-f0-9]{64}", token):
        print("Start the local service from the Rigarus desktop app.", file=sys.stderr)
        return 2

    try:
        initialize_database(arguments.database)
    except UnsupportedDatabaseError:
        print(
            "This database needs a compatible version of Rigarus. Verify the selected database.",
            file=sys.stderr,
        )
        return 1
    except (OSError, sqlite3.Error):
        print(
            "Unable to open the local database. Check folder permissions and close other Rigarus windows.",
            file=sys.stderr,
        )
        return 1

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            if sys.platform == "win32":
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            listener.bind(("127.0.0.1", 0))
            if asyncio.run(
                serve(
                    listener,
                    arguments.database,
                    token,
                    editor_test=arguments.synthetic_day_editor,
                )
            ):
                return 0
    except OSError:
        pass
    print(
        "Unable to start the local service. Reopen Rigarus to retry.", file=sys.stderr
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
