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

from pathlib import Path

import requests
from nicegui import app, ui

API_BASE = "http://localhost:8006"
app.add_static_file(
    local_file=Path(__file__).parent / "Media" / "UNH-CREST.png",
    url_path="/unh-crest.png",
)
NAV_LEFT_LINKS = [
    ("Home", "/"),
    ("Housing Applications", "/housing-applications"),
    ("Meal Plans", "/meal-plans"),
    ("Become an RA", "/become-an-ra"),
]
NAV_RIGHT_LINKS = [
    ("My Profile", "/my-profile"),
    ("Messages", "/messages"),
    ("Log out", "/"),
]


def render_site_header():
    # this add_head_html block was AI Generated with GPT-6 Luna
    ui.add_head_html("""
        <style>
            body { background: #f4f7fb; color: #182536; }
            .site-shell { max-width: 1180px; margin: auto; padding: 22px 28px; }
            .brand-row { min-height: 170px; }
            .brand-logo { display: block; width: 480px; max-width: 100%; height: auto; }
            .site-nav { gap: 8px; margin: 18px 0 34px; padding: 10px 14px; background: white; border-radius: 14px; }
            .site-nav a { padding: 10px 12px; color: #34495e; font-weight: 600; white-space: nowrap; }
            .home-content { max-width: 920px; margin: 58px auto 0; }
            .welcome-card { padding: 40px; border-radius: 24px; }
            .welcome-title { margin-top: 14px; color: #17324d; font-size: clamp(32px, 5vw, 48px); font-weight: 800; }
            .welcome-copy { max-width: 650px; color: #536579; font-size: 17px; line-height: 1.7; }
            .welcome-list { color: #536579; font-size: 16px; line-height: 1.7; }
            @media (max-width: 760px) { .site-nav { overflow-x: auto; flex-wrap: nowrap; } }
        </style>
    """)

    with ui.column().classes("site-shell w-full"):
        with ui.row().classes("brand-row w-full items-center"):
            ui.image("/unh-crest.png").classes("brand-logo")
        with ui.row().classes("site-nav w-full items-center justify-between no-wrap"):
            with ui.row().classes("items-center no-wrap"):
                for label, target in NAV_LEFT_LINKS:
                    ui.link(label, target)
            with ui.row().classes("items-center no-wrap"):
                for label, target in NAV_RIGHT_LINKS:
                    ui.link(label, target)

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
    render_site_header()
    with ui.column().classes("home-content w-full"):
        with ui.card().classes("welcome-card w-full"):
            ui.label("Welcome!").classes("welcome-title")
            ui.label(
                "Through the Housing Portal, you can access information and resources "
                "for your on-campus housing and dining needs. From the navigation menu, "
                "you can do the following:"
            ).classes("welcome-copy")
            ui.markdown("""
                - **Housing Applications**: Access the online applications for on-campus housing in our residence halls and apartments
                - **Meal Plans**: Select or change your campus meal plan options
                - **My Housing**: View and manage your current and future housing assignments, including room and roommate information, room combination (if applicable), and important housing forms.
                - **Maintenance**: Submit a maintenance request
                - **Join Our Team**: Apply for leadership opportunities (such as RA) with Housing and Residential Life.
                - **My Profile**: Update any relevant contact information
            """).classes("welcome-list")


@ui.page("/housing-applications")
def housing_applications_page():
    render_site_header()
    with ui.column().classes("site-shell w-full"):
        render_content()


def render_placeholder_page(title: str):
    render_site_header()
    with ui.column().classes("home-content w-full"):
        with ui.card().classes("welcome-card w-full"):
            ui.label(title).classes("welcome-title")
            ui.label("This section is not available in the current portal prototype.").classes(
                "welcome-copy"
            )


@ui.page("/meal-plans")
def meal_plans_page():
    render_placeholder_page("Meal Plans")


@ui.page("/become-an-ra")
def become_an_ra_page():
    render_placeholder_page("Become an RA")


@ui.page("/my-profile")
def my_profile_page():
    render_placeholder_page("My Profile")


@ui.page("/messages")
def messages_page():
    render_placeholder_page("Messages")


@ui.refreshable
def render_content():
    ui.label("Housing Applications").classes("text-2xl")

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