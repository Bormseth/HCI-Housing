"""
pages/housing_selection.py

Housing selection pages (a later stage than the housing application):

    /housing-applications/room-select        browse all buildings
    /housing-applications/room-select/{id}   pick a room type in one building,
                                             then Continue -> Confirm Booking
"""

from nicegui import ui
from components.header import render_site_header
from components.housing_card import render_building_card
from services.api_client import api_get, api_post


@ui.page("/housing-applications/room-select")
def housing_selection_page():
    render_site_header()
    with ui.column().classes("site-shell w-full"):
        render_housing_select()
        
@ui.page("/housing-applications/room-select/{building_id}")
def building_page(building_id: int):
    render_site_header()
    with ui.column().classes("site-shell w-full"):
        render_building_detail(building_id)


@ui.refreshable
def render_housing_select():
    buildings = api_get("/housing-options")
    my_housing = api_get("/my-housing")
    with ui.row():
        ui.button(icon="arrow_back", on_click= lambda: ui.navigate.to("/housing-applications")).props('flat round color=black')
        ui.label("Housing Selection").classes("text-2xl")
    if my_housing: my_housing_card(my_housing)
    with ui.tabs().classes("w-full") as tabs: 
        res_hall = ui.tab('Residence Hall')
        apartment = ui.tab('Apartments')
        graduate = ui.tab('Graduate')
    with ui.tab_panels(tabs, value=res_hall):
        with ui.tab_panel(res_hall):
            with ui.grid(columns=3):
                for building in filter(lambda b: b["type"] == "Residence Hall", buildings):
                    render_building_card(building)
        with ui.tab_panel(apartment):
            with ui.grid(columns=3):
                for building in filter(lambda b: b["type"] == "Apartment", buildings):
                    render_building_card(building)
        with ui.tab_panel(graduate):
            with ui.grid(columns=3):
                for building in filter(lambda b: b["type"] == "Graduate", buildings):
                    render_building_card(building)
        
# def render_buildings(buildings):
#     for building in buildings: 
#         render_building_card(building)
            
STYLE_HEADINGS = {
    "traditional": "Traditional Rooms",
    "suite": "Suites",
    "apartment": "Apartments",
}


def format_room_type(slug: str) -> str:
    """'super_single' -> 'Super Single', '2_doubles_1_single' -> '2 Doubles + 1 Single'"""
    parts = slug.split("_")
    if not parts[0].isdigit():
        return " ".join(parts).title()
    return " + ".join(f"{parts[i]} {parts[i + 1].title()}" for i in range(0, len(parts), 2))

def refresh_views():
    """The selection card shows on both pages, so refresh both views.
    Refreshing a view that isn't on the current page does nothing."""
    render_housing_select.refresh()
    render_building_detail.refresh()


def select_room(building_id: int, style: str, room_type: str):
    body = {"building_id": building_id, "style": style, "room_type": room_type}
    if api_post("/housing/select", body):
        ui.notify("Room type selected", type="positive")
        render_building_detail.refresh()
        refresh_views()


def confirm_booking(dialog):
    if api_post("/housing/confirm"):
        dialog.close()
        ui.notify("Booking confirmed", type="positive")
        render_building_detail.refresh()
        refresh_views()


def cancel_room_selection():
    if api_post("/housing/cancel"):
        ui.notify("Selection cancelled", type="warning")
        render_building_detail.refresh()
        refresh_views()

def render_room_card(building, room, my_housing):
    is_selected = bool(my_housing) and (
        my_housing["building_id"] == building["id"]
        and my_housing["style"] == room["style"]
        and my_housing["room_type"] == room["room_type"]
    )
    with ui.card():
        ui.label(format_room_type(room["room_type"])).classes("text-lg")
        ui.label(f'Sleeps {room["capacity"]}')
        ui.label(f'{room["count"]} room{"s" if room["count"] != 1 else ""}')
        if is_selected:
            ui.button("Selected", icon="check").props("disable")
        else:
            ui.button(
                "Select",
                on_click=lambda b=building["id"], r=room: select_room(b, r["style"], r["room_type"]),
            )

@ui.refreshable
def render_building_detail(building_id: int):
    building = api_get(f"/housing-options/{building_id}")
    my_housing = api_get("/my-housing")

    with ui.row().classes("items-center"):
        ui.button(
            icon="arrow_back",
            on_click=lambda: ui.navigate.to("/housing-applications/room-select"),
        ).props("flat round color=black")
        ui.label(building["name"] if building else "Building not found").classes("text-2xl")
    if not building:
        return

    with ui.row().classes("items-center"):
        ui.label(building["type"])
        ui.button(
            "More Info", on_click=lambda: ui.navigate.to(building["url"], new_tab=True)
        ).props("flat")

    if my_housing: my_housing_card(my_housing)

    if not building["rooms"]:
        ui.label("Room details aren't published for this building. Use More Info to learn more.")
        return

    for style, heading in STYLE_HEADINGS.items():
        rooms = [r for r in building["rooms"] if r["style"] == style]
        if not rooms:
            continue
        ui.label(heading).classes("text-lg mt-4")
        with ui.grid(columns=3).classes("w-full"):
            for room in rooms:
                render_room_card(building, room, my_housing)

def my_housing_card(my_housing):
    confirmed = my_housing.get("confirmed", False)
    summary = f'{my_housing["building_name"]} - {format_room_type(my_housing["room_type"])}'
    
    # Built here but hidden until the Continue button opens it.
    with ui.dialog() as confirm_dialog, ui.card():
        ui.label("Confirm Booking").classes("text-xl")
        ui.label(my_housing["building_name"]).classes("text-lg")
        ui.label(format_room_type(my_housing["room_type"]))
        ui.label(f'Sleeps {my_housing["capacity"]}')
        with ui.row().classes("w-full justify-end"):
            ui.button("Go Back", on_click=confirm_dialog.close).props("flat")
            ui.button("Confirm Booking", on_click=lambda: confirm_booking(confirm_dialog))
    
    with ui.card().classes("w-full"):
        ui.label(("Booking confirmed: " if confirmed else "Current selection: ") + summary).classes("font-bold")
        with ui.row():
            if not confirmed:
                ui.button("Continue", on_click=confirm_dialog.open)
            ui.button(
                "Cancel Booking" if confirmed else "Cancel Selection",
                on_click=cancel_room_selection,
                ).props("flat color=negative")
