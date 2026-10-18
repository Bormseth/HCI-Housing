"""SQLite-backed, browser-scoped mock applications. No university connection or login."""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from services.ra_rules import ApplicationData, CYCLE, validate_application

router = APIRouter(prefix="/ra", tags=["RA prototype"])


def cycle_info():
    # Explicit demo state: the sample deadline is content, not a real recruitment schedule.
    return {**CYCLE, "open": os.getenv("RA_APPLICATIONS_OPEN", "true").lower() == "true"}


def session_key(x_ra_session: str) -> str:
    try:
        return str(UUID(x_ra_session))
    except ValueError:
        raise HTTPException(400, "This demo session is invalid. Reload the RA page.") from None


@contextmanager
def database():
    path = Path(os.getenv("RA_DB_PATH", str(Path(__file__).resolve().parents[1] / "data" / "ra_applications.sqlite3")))
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("""CREATE TABLE IF NOT EXISTS ra_applications (
            session TEXT PRIMARY KEY, data TEXT NOT NULL, step INTEGER NOT NULL,
            status TEXT NOT NULL, version INTEGER NOT NULL,
            saved_at TEXT NOT NULL, submitted_at TEXT, confirmation TEXT
        )""")
        with connection:
            yield connection
    finally:
        connection.close()


def empty_application():
    return {"data": ApplicationData().model_dump(), "step": 1, "status": "not_started",
            "version": 0, "saved_at": None, "submitted_at": None, "confirmation": None}


def snapshot(row):
    if row is None:
        return empty_application()
    return {key: (json.loads(row[key]) if key == "data" else row[key])
            for key in row.keys() if key != "session"}


class SaveDraft(BaseModel):
    data: ApplicationData
    step: int = Field(default=1, ge=1, le=3)
    expected_version: int = Field(ge=0)


class SubmitApplication(BaseModel):
    expected_version: int = Field(ge=0)


@router.get("/cycle")
def get_cycle():
    return cycle_info()


@router.get("/application")
def get_application(x_ra_session: str = Header()):
    key = session_key(x_ra_session)
    with database() as db:
        return snapshot(db.execute("SELECT * FROM ra_applications WHERE session=?", (key,)).fetchone())


@router.put("/application")
def save_application(request: SaveDraft, x_ra_session: str = Header()):
    key = session_key(x_ra_session)
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        current = snapshot(db.execute("SELECT * FROM ra_applications WHERE session=?", (key,)).fetchone())
        if current["status"] == "submitted":
            raise HTTPException(409, "This application is already submitted. Reload to view your confirmation.")
        if current["version"] != request.expected_version:
            raise HTTPException(409, "A newer version was saved in another tab. Keep a copy of your changes, then reload.")
        now = datetime.now(timezone.utc).isoformat()
        db.execute("""INSERT INTO ra_applications VALUES (?, ?, ?, 'draft', ?, ?, NULL, NULL)
            ON CONFLICT(session) DO UPDATE SET data=excluded.data, step=excluded.step,
            version=excluded.version, saved_at=excluded.saved_at""",
                   (key, request.data.model_dump_json(), request.step, current["version"] + 1, now))
        return snapshot(db.execute("SELECT * FROM ra_applications WHERE session=?", (key,)).fetchone())


@router.post("/application/submit")
def submit_application(request: SubmitApplication, x_ra_session: str = Header()):
    key = session_key(x_ra_session)
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        current = snapshot(db.execute("SELECT * FROM ra_applications WHERE session=?", (key,)).fetchone())
        # Retrying after a connection interruption returns the same receipt.
        if current["status"] == "submitted":
            return current
        if not cycle_info()["open"]:
            raise HTTPException(409, "Applications are closed. Your saved draft is still available.")
        if current["version"] != request.expected_version:
            raise HTTPException(409, "Your draft changed in another tab. Reload and review the latest version.")
        errors = validate_application(current["data"])
        if errors:
            raise HTTPException(422, {"message": "Complete the required fields before submitting.", "errors": errors})
        now = datetime.now(timezone.utc).isoformat()
        confirmation = "RA-DEMO-" + uuid4().hex[:8].upper()
        db.execute("""UPDATE ra_applications SET status='submitted', submitted_at=?,
            confirmation=?, version=version+1 WHERE session=?""", (now, confirmation, key))
        return snapshot(db.execute("SELECT * FROM ra_applications WHERE session=?", (key,)).fetchone())


@router.delete("/application")
def reset_application(x_ra_session: str = Header()):
    """Reset only this browser's sample record for another usability-test run."""
    key = session_key(x_ra_session)
    with database() as db:
        db.execute("DELETE FROM ra_applications WHERE session=?", (key,))
    return empty_application()
