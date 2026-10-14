from nicegui import ui

from components.announcement_card import render_announcement_card
from components.header import render_site_header
from components.housing_card import (
    render_current_housing_card,
    render_housing_card,
)
from components.my_housing import render_no_housing_message
from services.api_client import api_get, api_post


def select_room_type(room_type_id: int):
    if api_post("/housing/select", {"room_type_id": room_type_id}):
        ui.notify("Housing selected", type="positive")
        render_content.refresh()


def cancel_housing():
    if api_post("/housing/cancel"):
        ui.notify("Housing selection cancelled", type="warning")
        render_content.refresh()


@ui.page("/housing-applications")
def housing_applications_page():
    render_site_header()
    with ui.column().classes("site-shell w-full"):
        render_content()


@ui.refreshable
def render_content():
    ui.label("Housing Applications").classes("text-2xl")

    with ui.row().classes("w-full no-wrap items-start"):
        with ui.column().classes("w-1/2 p-2"):
            render_room_types()

        with ui.column().classes("w-1/2 p-2"):
            render_my_housing()
            render_announcements()


def render_room_types():
    ui.label("Room Types").classes("text-lg font-bold")
    room_types = api_get("/room-types")

    if not room_types:
        ui.label("No room types are currently available.")
        return

    for room_type in room_types:
        render_housing_card(room_type, select_room_type)


def render_my_housing():
    ui.label("My Housing").classes("text-lg font-bold")
    my_housing = api_get("/my-housing")

    if not my_housing:
        render_no_housing_message()
        return

    render_current_housing_card(my_housing, cancel_housing)


def render_announcements():
    ui.label("Announcements").classes("text-lg font-bold")
    announcements = api_get("/announcements")

    if not announcements:
        ui.label("No announcements available.")
        return

    for announcement in announcements:
        render_announcement_card(announcement)
