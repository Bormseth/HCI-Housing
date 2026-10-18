"""
Endpoints:
    GET  /buildings
    GET  /room-types
    GET  /room-types/{room_type_id}
    GET  /my-housing
    POST /housing/select   body: {"room_type_id": int}
    POST /housing/cancel
    GET  /announcements
    GET  /ra/cycle
    GET, PUT, DELETE /ra/application
    POST /ra/application/submit
"""

import json
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="Mock Housing API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------
# In-memory "database"
# ---------------------------------------------------------------------

BUILDINGS = [
    {"id": 1, "name": "Harborview Hall", "class_years": "First-year", "amenities": "dining hall, laundry, study lounge"},
    {"id": 2, "name": "Elm Residence", "class_years": "Sophomore+", "amenities": "kitchenette, laundry"},
    {"id": 3, "name": "Ridgeline Suites", "class_years": "Junior/Senior", "amenities": "kitchen, private bath, laundry"},
]

ROOM_TYPES = [
    {"id": 1, "building_id": 1, "name": "Double", "price_per_term": 3200, "capacity": 2, "total_spaces": 120},
    {"id": 2, "building_id": 1, "name": "Triple", "price_per_term": 2800, "capacity": 3, "total_spaces": 45},
    {"id": 3, "building_id": 2, "name": "Single", "price_per_term": 4100, "capacity": 1, "total_spaces": 40},
    {"id": 4, "building_id": 2, "name": "Double", "price_per_term": 3400, "capacity": 2, "total_spaces": 80},
    {"id": 5, "building_id": 3, "name": "4-Person Suite", "price_per_term": 3900, "capacity": 4, "total_spaces": 32},
]

SELECTIONS = [
    {"id": 1, "room_type_id": 1, "student": "Dolly Parton"},
    {"id": 2, "room_type_id": 1, "student": "Elvis Presley"},
    {"id": 3, "room_type_id": 3, "student": "Johnny Cash"},
]
_next_selection_id = 4

ANNOUNCEMENTS = [
    {
        "id": 1,
        "title": "Housing selection opens Monday",
        "posted": "2026-08-19T09:00:00",
        "body": "Returning student housing selection opens Monday at 8am. Popular room types in Ridgeline Suites have historically filled within the first day.",
    },
    {
        "id": 2,
        "title": "Elm Residence laundry room closed this week",
        "posted": "2026-08-21T09:00:00",
        "body": "The main-floor laundry room in Elm Residence is closed for repairs. Residents can use the basement laundry room in the meantime.",
    },
]

# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------

class SelectRequest(BaseModel):
    room_type_id: int

def _get_building_or_404(building_id: int) -> dict:
    for b in BUILDINGS:
        if b["id"] == building_id:
            return b
    raise HTTPException(status_code=404, detail="Building not found")

def _get_room_type_or_404(room_type_id: int) -> dict:
    for rt in ROOM_TYPES:
        if rt["id"] == room_type_id:
            return rt
    raise HTTPException(status_code=404, detail="Room type not found")

def _taken_count(room_type_id: int) -> int:
    return sum(1 for s in SELECTIONS if s["room_type_id"] == room_type_id)

def _my_selection():
    for s in SELECTIONS:
        if s["student"] == "you":
            return s
    return None

def _summarize_room_type(rt: dict) -> dict:
    taken = _taken_count(rt["id"])
    building = _get_building_or_404(rt["building_id"])
    summary = dict(rt)
    summary["building_name"] = building["name"]
    summary["taken"] = taken
    summary["spaces_open"] = rt["total_spaces"] - taken
    return summary

@app.get("/buildings")
def list_buildings():
    return BUILDINGS

@app.get("/room-types")
def list_room_types():
    return [_summarize_room_type(rt) for rt in ROOM_TYPES]

@app.get("/room-types/{room_type_id}")
def get_room_type(room_type_id: int):
    return _summarize_room_type(_get_room_type_or_404(room_type_id))

@app.get("/my-housing")
def get_my_housing():
    selection = _my_selection()
    if not selection:
        return None
    rt = _get_room_type_or_404(selection["room_type_id"])
    return {**selection, **_summarize_room_type(rt)}

@app.get("/announcements")
def list_announcements():
    return ANNOUNCEMENTS

@app.post("/housing/select")
def select_housing(req: SelectRequest):
    global _next_selection_id
    room_type = _get_room_type_or_404(req.room_type_id)
    if _my_selection():
        raise HTTPException(
            status_code=400,
            detail="You already have a housing selection. Cancel it before choosing a new one.",
        )
    if _taken_count(room_type["id"]) >= room_type["total_spaces"]:
        raise HTTPException(status_code=400, detail=f'{room_type["name"]} is full')

    new_selection = {"id": _next_selection_id, "room_type_id": room_type["id"], "student": "you"}
    SELECTIONS.append(new_selection)
    _next_selection_id += 1
    return new_selection

@app.post("/housing/cancel")
def cancel_housing():
    selection = _my_selection()
    if not selection:
        raise HTTPException(status_code=404, detail="You don't have a housing selection to cancel")
    SELECTIONS.remove(selection)
    return {"cancelled": selection["id"]}

# ---------------------------------------------------------------------
# RA application: sample content, validation, and persistent drafts
# ---------------------------------------------------------------------

CLASS_YEARS = ["First-year", "Sophomore", "Junior", "Senior", "Graduate student"]
MIN_WORDS = 25
MAX_WORDS = 200
CYCLE = {
    "term": "2027–2028",
    "deadline": "November 30, 2026 at 11:59 PM ET",
    "estimate": "15–20 minutes",
    "sample": True,
}
PROMPTS = {
    "motivation": "Why do you want to be an RA?",
    "scenario": "A resident feels left out. How would you help?",
}


class ApplicationData(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    full_name: str = Field(default="", max_length=120)
    email: str = Field(default="", max_length=200)
    class_year: str = Field(default="", max_length=40)
    major: str = Field(default="", max_length=160)
    enrolled: bool = False
    expectations: bool = False
    motivation: str = Field(default="", max_length=8000)
    scenario: str = Field(default="", max_length=8000)
    experience: str = Field(default="", max_length=2000)
    certify: bool = False


def word_count(text: str) -> int:
    return len(text.split())


def validate_step(data: dict, step: int) -> dict[str, str]:
    """Return actionable field errors; drafts may remain incomplete."""
    errors = {}
    if step == 1:
        if len(data.get("full_name", "").strip()) < 2:
            errors["full_name"] = "Enter your full name (at least 2 characters)."
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", data.get("email", "").strip()):
            errors["email"] = "Enter a valid email, such as name@unh.edu."
        if data.get("class_year") not in CLASS_YEARS:
            errors["class_year"] = "Choose your class year."
        if not data.get("enrolled"):
            errors["enrolled"] = "Confirm that you expect to be enrolled during the appointment."
        if not data.get("expectations"):
            errors["expectations"] = "Review and acknowledge the sample role expectations."
    if step == 2:
        for key, prompt in PROMPTS.items():
            count = word_count(data.get(key, ""))
            if not MIN_WORDS <= count <= MAX_WORDS:
                errors[key] = f'{prompt} Write {MIN_WORDS}–{MAX_WORDS} words; you have {count}.'
    if step == 3 and not data.get("certify"):
        errors["certify"] = "Confirm that you have reviewed your application before submitting."
    return errors


def validate_application(data: dict) -> dict[str, str]:
    return {key: message for step in (1, 2, 3) for key, message in validate_step(data, step).items()}


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
    path = Path(os.getenv("RA_DB_PATH", str(Path(__file__).resolve().parent / "data" / "ra_applications.sqlite3")))
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
    validate_step: int | None = Field(default=None, ge=1, le=3)


class SubmitApplication(BaseModel):
    expected_version: int = Field(ge=0)


@app.get("/ra/cycle")
def get_cycle():
    return {**cycle_info(), "class_years": CLASS_YEARS, "prompts": PROMPTS,
            "min_words": MIN_WORDS, "max_words": MAX_WORDS}


@app.get("/ra/application")
def get_application(x_ra_session: str = Header()):
    key = session_key(x_ra_session)
    with database() as db:
        return snapshot(db.execute("SELECT * FROM ra_applications WHERE session=?", (key,)).fetchone())


@app.put("/ra/application")
def save_application(request: SaveDraft, x_ra_session: str = Header()):
    key = session_key(x_ra_session)
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        current = snapshot(db.execute("SELECT * FROM ra_applications WHERE session=?", (key,)).fetchone())
        if current["status"] == "submitted":
            raise HTTPException(409, "This application is already submitted. Reload to view your confirmation.")
        if current["version"] != request.expected_version:
            raise HTTPException(409, "A newer version was saved in another tab. Keep a copy of your changes, then reload.")
        if request.validate_step is not None:
            errors = validate_step(request.data.model_dump(), request.validate_step)
            if errors:
                raise HTTPException(422, {"message": "Check the required fields before continuing.", "errors": errors})
        now = datetime.now(timezone.utc).isoformat()
        db.execute("""INSERT INTO ra_applications VALUES (?, ?, ?, 'draft', ?, ?, NULL, NULL)
            ON CONFLICT(session) DO UPDATE SET data=excluded.data, step=excluded.step,
            version=excluded.version, saved_at=excluded.saved_at""",
                   (key, request.data.model_dump_json(), request.step, current["version"] + 1, now))
        return snapshot(db.execute("SELECT * FROM ra_applications WHERE session=?", (key,)).fetchone())


@app.post("/ra/application/submit")
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


@app.delete("/ra/application")
def reset_application(x_ra_session: str = Header()):
    """Reset only this browser's sample record for another usability-test run."""
    key = session_key(x_ra_session)
    with database() as db:
        db.execute("DELETE FROM ra_applications WHERE session=?", (key,))
    return empty_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
