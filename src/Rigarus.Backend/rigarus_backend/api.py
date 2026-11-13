import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .domain import DemoProject
from .project_api import project_router
from .storage import DemoStore, UnsupportedDatabaseError, initialize_database


class DemoNote(BaseModel):
    note: str


def create_app(database_path: Path, *, database_initialized: bool = False) -> FastAPI:
    store = DemoStore(database_path)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if not database_initialized:
            initialize_database(database_path)
        yield

    app = FastAPI(lifespan=lifespan, openapi_url=None)
    app.include_router(project_router(database_path))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ready"}

    @app.get("/demo")
    def read_demo() -> DemoProject:
        try:
            return store.read()
        except (sqlite3.Error, UnsupportedDatabaseError) as error:
            raise HTTPException(
                503, "Unable to read the local demo project."
            ) from error

    @app.put("/demo/note")
    def save_note(request: DemoNote) -> DemoProject:
        try:
            return store.save_note(request.note)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except (sqlite3.Error, UnsupportedDatabaseError) as error:
            raise HTTPException(503, "Unable to save the local demo note.") from error

    return app
