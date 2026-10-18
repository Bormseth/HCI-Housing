"""
housing_api.py

A  mock backend for a campus housing portal: browse residence
halls and room types with live availability, select/cancel a housing
assignment, and read housing announcements.

Run with:
    pip install fastapi uvicorn
    python housing_api.py

API is available at http://localhost:8006

Endpoints:
    GET  /housing-options                 all buildings (with their room types)
    GET  /housing-options/{building_id}   one building
    GET  /my-housing                      current selection, or null
    POST /housing/select   body: {"building_id": int, "style": str, "room_type": str}
    POST /housing/confirm
    POST /housing/cancel
    GET  /announcements
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)