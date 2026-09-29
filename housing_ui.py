"""
housing_ui.py

A simple NiceGUI frontend that pulls data from housing_api.py
and renders a campus housing portal: browse buildings and room types,
select/cancel a housing assignment, and read announcements.

Run with:
    pip install nicegui requests
    python housing_api.py     # in one terminal
    python housing_ui.py      # in another terminal

Then http://localhost:8085 will automatically open.
"""

import requests
from nicegui import ui

API_BASE = "http://localhost:8006"

def api_get(path: str):
    try:
        resp = requests.get(f"{API_BASE}{path}", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        ui.notify(f"Could not reach API: {e}", type="negative")
        return []

def api_post(path: str, json: dict | None = None):
    try:
        resp = requests.post(f"{API_BASE}{path}", json=json, timeout=5)
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        detail = ""
        try:
            detail = e.response.json().get("detail", "")
        except Exception:
            pass
        ui.notify(detail or f"Request failed: {e}", type="negative")
        return False

def select_room_type(room_type_id: int):
    if api_post("/housing/select", {"room_type_id": room_type_id}):
        ui.notify("Housing selected", type="positive")
        render_content.refresh()

def cancel_housing():
    if api_post("/housing/cancel"):
        ui.notify("Housing selection cancelled", type="warning")
        render_content.refresh()

@ui.page("/")
def main_page():
    render_content()

@ui.refreshable
def render_content():
    ui.label("Housing Portal").classes("text-2xl")

    with ui.row().classes("w-full no-wrap"):
        with ui.column().classes("w-1/2 p-2"):
            render_room_types()
        with ui.column().classes("w-1/2 p-2"):
            render_my_housing()
            render_announcements()

def render_room_types():
    ui.label("Room Types").classes("text-lg")
    room_types = api_get("/room-types")
    for rt in room_types:
        with ui.row().classes("items-center"):
            label = (
                f'{rt["building_name"]} - {rt["name"]} - ${rt["price_per_term"]}/term '
                f'- {rt["spaces_open"]}/{rt["total_spaces"]} open'
            )
            ui.label(label)
            ui.button("Select", on_click=lambda rtid=rt["id"]: select_room_type(rtid))

def render_my_housing():
    ui.label("My Housing").classes("text-lg")
    my_housing = api_get("/my-housing")
    if not my_housing:
        ui.label("You haven't selected housing yet.")
        return
    ui.label(
        f'{my_housing["building_name"]} - {my_housing["name"]} '
        f'- ${my_housing["price_per_term"]}/term'
    )
    ui.button("Cancel", on_click=cancel_housing)

def render_announcements():
    ui.label("Announcements").classes("text-lg")
    announcements = api_get("/announcements")
    for a in announcements:
        ui.label(a["title"])
        ui.label(a["body"])
        ui.separator()

ui.run(port=8085, title="Mock Housing Portal")