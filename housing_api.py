"""
Endpoints:
    GET  /housing-options                 all buildings (with their room types)
    GET  /housing-options/{building_id}   one building
    GET  /my-housing                      current selection, or null
    POST /housing/select   body: {"building_id": int, "style": str, "room_type": str}
    POST /housing/confirm
    POST /housing/cancel
    GET  /announcements
    GET  /ra/cycle
    GET, PUT, DELETE /ra/application
    POST /ra/application/submit
    GET, POST, DELETE /meal-plans/{year}/selection
    GET, POST, DELETE /housing-applications/{year}
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
from data.unh_housing_data import HOUSING

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
    building_id: int
    style: str
    room_type: str

# The student's current selection (None until they pick something).
_selection: dict | None = None

def _get_building_or_404(building_id: int) -> dict:
    for b in HOUSING:
        if b["id"] == building_id:
            return b
    raise HTTPException(status_code=404, detail="Building not found")


@app.get("/housing-options")
def list_buildings():
    return HOUSING

@app.get("/housing-options/{building_id}")
def get_building(building_id: int):
    return _get_building_or_404(building_id)

@app.get("/my-housing")
def get_my_housing():
    return _selection

@app.get("/announcements")
def list_announcements():
    return ANNOUNCEMENTS

@app.post("/housing/select")
def select_housing(req: SelectRequest):
    global _selection
    building = _get_building_or_404(req.building_id)
    room = next(
        (r for r in building["rooms"]
         if r["style"] == req.style and r["room_type"] == req.room_type),
        None,
    )
    if room is None:
        raise HTTPException(status_code=404, detail="Room type not found in this building")
    # Selecting again simply replaces the previous selection.
    _selection = {
        "building_id": building["id"],
        "building_name": building["name"],
        "style": room["style"],
        "room_type": room["room_type"],
        "capacity": room["capacity"],
        "confirmed": False,
    }
    return _selection

@app.post("/housing/confirm")
def confirm_housing():
    if _selection is None:
        raise HTTPException(status_code=400, detail="No housing selection to confirm")
    _selection["confirmed"] = True
    return _selection

@app.post("/housing/cancel")
def cancel_housing():
    global _selection
    if _selection is None:
        raise HTTPException(status_code=400, detail="No housing selection to cancel")
    _selection = None
    return {"cancelled": True}

# ---------------------------------------------------------------------
# RA application: sample content, validation, and persistent drafts
# ---------------------------------------------------------------------

CLASS_YEARS = ["First-year", "Sophomore", "Junior", "Senior", "Graduate student"]
EMAIL_PATTERN = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+")
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
        if not EMAIL_PATTERN.fullmatch(data.get("email", "").strip()):
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
        connection.execute("""CREATE TABLE IF NOT EXISTS meal_plan_selections (
            session TEXT NOT NULL, year TEXT NOT NULL, meal_plan TEXT NOT NULL,
            dining_dollars INTEGER NOT NULL, total REAL NOT NULL,
            confirmation TEXT NOT NULL, confirmed_at TEXT NOT NULL,
            PRIMARY KEY (session, year)
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS housing_applications (
            session TEXT NOT NULL, year TEXT NOT NULL, data TEXT NOT NULL,
            confirmation TEXT NOT NULL, submitted_at TEXT NOT NULL,
            PRIMARY KEY (session, year)
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


def load_application(db, key):
    return snapshot(db.execute("SELECT * FROM ra_applications WHERE session=?", (key,)).fetchone())


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
        return load_application(db, key)


@app.put("/ra/application")
def save_application(request: SaveDraft, x_ra_session: str = Header()):
    key = session_key(x_ra_session)
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        current = load_application(db, key)
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
        return load_application(db, key)


@app.post("/ra/application/submit")
def submit_application(request: SubmitApplication, x_ra_session: str = Header()):
    key = session_key(x_ra_session)
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        current = load_application(db, key)
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
        return load_application(db, key)


@app.delete("/ra/application")
def reset_application(x_ra_session: str = Header()):
    """Reset only this browser's sample record for another usability-test run."""
    key = session_key(x_ra_session)
    with database() as db:
        db.execute("DELETE FROM ra_applications WHERE session=?", (key,))
    return empty_application()


# ---------------------------------------------------------------------
# Meal plans: server-side catalog (authoritative prices) and saved selections
# ---------------------------------------------------------------------

MEAL_PLAN_YEARS = {"2026-2027"}
MEAL_PLAN_PRICES = {
    "Unlimited": 3200.00,
    "14 Meals Per Week": 2800.00,
    "10 Meals Per Week": 2400.00,
    "7 Meals Per Week": 2000.00,
}
DINING_DOLLAR_AMOUNTS = {0, 100, 250, 500}  # each dollar costs one dollar


class MealPlanSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    meal_plan: str = Field(max_length=60)
    dining_dollars: int
    terms_accepted: bool


def meal_plan_record(row) -> dict | None:
    if row is None:
        return None
    record = {key: row[key] for key in row.keys() if key != "session"}
    record["meal_plan_price"] = MEAL_PLAN_PRICES.get(record["meal_plan"])
    return record


def check_year(year: str, allowed: set[str], message: str):
    if year not in allowed:
        raise HTTPException(404, message)


def check_meal_year(year: str):
    check_year(year, MEAL_PLAN_YEARS, "Meal plan selection is not available for that academic year.")


def load_meal_selection(db, key, year):
    return meal_plan_record(db.execute(
        "SELECT * FROM meal_plan_selections WHERE session=? AND year=?", (key, year)).fetchone())


def validate_meal_selection(selection: MealPlanSelection) -> dict[str, str]:
    errors = {}
    if not selection.terms_accepted:
        errors["terms_accepted"] = "Agree to the meal plan terms before confirming."
    if selection.meal_plan not in MEAL_PLAN_PRICES:
        errors["meal_plan"] = "Choose one of the available meal plans."
    if selection.dining_dollars not in DINING_DOLLAR_AMOUNTS:
        errors["dining_dollars"] = "Choose one of the available Dining Dollar amounts."
    return errors


@app.get("/meal-plans/{year}/selection")
def get_meal_selection(year: str, x_ra_session: str = Header()):
    check_meal_year(year)
    key = session_key(x_ra_session)
    with database() as db:
        return load_meal_selection(db, key, year)


@app.post("/meal-plans/{year}/selection")
def confirm_meal_selection(year: str, request: MealPlanSelection, x_ra_session: str = Header()):
    """Create or replace this session's selection. The total is computed here, not by the client."""
    check_meal_year(year)
    key = session_key(x_ra_session)
    errors = validate_meal_selection(request)
    if errors:
        raise HTTPException(422, {"message": "Check your meal plan selection.", "errors": errors})
    total = MEAL_PLAN_PRICES[request.meal_plan] + request.dining_dollars
    now = datetime.now(timezone.utc).isoformat()
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        existing = db.execute(
            "SELECT confirmation FROM meal_plan_selections WHERE session=? AND year=?", (key, year)).fetchone()
        confirmation = existing["confirmation"] if existing else "MP-DEMO-" + uuid4().hex[:8].upper()
        db.execute("""INSERT INTO meal_plan_selections VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session, year) DO UPDATE SET meal_plan=excluded.meal_plan,
            dining_dollars=excluded.dining_dollars, total=excluded.total,
            confirmed_at=excluded.confirmed_at""",
                   (key, year, request.meal_plan, request.dining_dollars, total, confirmation, now))
        return load_meal_selection(db, key, year)


@app.delete("/meal-plans/{year}/selection")
def cancel_meal_selection(year: str, x_ra_session: str = Header()):
    check_meal_year(year)
    key = session_key(x_ra_session)
    with database() as db:
        deleted = db.execute(
            "DELETE FROM meal_plan_selections WHERE session=? AND year=?", (key, year)).rowcount
    return {"cancelled": bool(deleted)}


# ---------------------------------------------------------------------
# Housing applications: saved per browser session and academic year
# ---------------------------------------------------------------------

HOUSING_APPLICATION_YEARS = {"2026-2027"}
HOUSING_CLASS_YEARS = ["First-year", "Sophomore", "Junior", "Senior"]
HOUSING_STYLES = [
    "Traditional Residence Hall",
    "Suite-Style Housing",
    "Apartment-Style Housing",
    "No Preference",
]
ROOM_PREFERENCES = ["Single", "Double", "Triple", "No Preference"]
PREFERRED_ROOMMATE = "I have a preferred roommate"
ROOMMATE_PREFERENCES = [
    PREFERRED_ROOMMATE,
    "I would like a roommate assigned",
    "I prefer a single room",
]


class HousingApplication(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    full_name: str = Field(default="", max_length=120)
    email: str = Field(default="", max_length=200)
    student_id: str = Field(default="", max_length=40)
    class_year: str = Field(default="", max_length=40)
    housing_style: str = Field(default="", max_length=60)
    room_preference: str = Field(default="", max_length=40)
    additional_considerations: str = Field(default="", max_length=2000)
    roommate_preference: str = Field(default="", max_length=60)
    roommate_name: str = Field(default="", max_length=120)


def check_housing_year(year: str):
    check_year(year, HOUSING_APPLICATION_YEARS, "Housing applications are not available for that academic year.")


def validate_housing_application(application: HousingApplication) -> dict[str, str]:
    errors = {}
    if len(application.full_name) < 2:
        errors["full_name"] = "Enter your full name (at least 2 characters)."
    if not EMAIL_PATTERN.fullmatch(application.email):
        errors["email"] = "Enter a valid email, such as name@unh.edu."
    if not application.student_id:
        errors["student_id"] = "Enter your student ID."
    if application.class_year not in HOUSING_CLASS_YEARS:
        errors["class_year"] = "Choose your class year."
    if application.housing_style not in HOUSING_STYLES:
        errors["housing_style"] = "Choose a housing style."
    if application.room_preference not in ROOM_PREFERENCES:
        errors["room_preference"] = "Choose a room type."
    if application.roommate_preference not in ROOMMATE_PREFERENCES:
        errors["roommate_preference"] = "Choose a roommate preference."
    return errors


def housing_application_record(row) -> dict | None:
    if row is None:
        return None
    return {"data": json.loads(row["data"]), "confirmation": row["confirmation"],
            "submitted_at": row["submitted_at"]}


def load_housing_application(db, key, year):
    return housing_application_record(db.execute(
        "SELECT * FROM housing_applications WHERE session=? AND year=?", (key, year)).fetchone())


@app.get("/housing-applications/{year}")
def get_housing_application(year: str, x_ra_session: str = Header()):
    check_housing_year(year)
    key = session_key(x_ra_session)
    with database() as db:
        return load_housing_application(db, key, year)


@app.post("/housing-applications/{year}")
def submit_housing_application(year: str, request: HousingApplication, x_ra_session: str = Header()):
    """Create or replace this session's application. Resubmitting keeps the confirmation number."""
    check_housing_year(year)
    key = session_key(x_ra_session)
    errors = validate_housing_application(request)
    if errors:
        raise HTTPException(422, {"message": "Check your housing application.", "errors": errors})
    data = request.model_dump()
    if data["roommate_preference"] != PREFERRED_ROOMMATE:
        data["roommate_name"] = ""  # a name only applies when a roommate was requested
    now = datetime.now(timezone.utc).isoformat()
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        existing = db.execute(
            "SELECT confirmation FROM housing_applications WHERE session=? AND year=?", (key, year)).fetchone()
        confirmation = existing["confirmation"] if existing else "HA-DEMO-" + uuid4().hex[:8].upper()
        db.execute("""INSERT INTO housing_applications VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(session, year) DO UPDATE SET data=excluded.data,
            submitted_at=excluded.submitted_at""",
                   (key, year, json.dumps(data), confirmation, now))
        return load_housing_application(db, key, year)


@app.delete("/housing-applications/{year}")
def cancel_housing_application(year: str, x_ra_session: str = Header()):
    check_housing_year(year)
    key = session_key(x_ra_session)
    with database() as db:
        deleted = db.execute(
            "DELETE FROM housing_applications WHERE session=? AND year=?", (key, year)).rowcount
    return {"cancelled": bool(deleted)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)