"""Maintenence Page"""

from datetime import datetime

from nicegui import app, ui

from components.header import render_site_header
from services.api_client import APIError, api_get, api_post, api_request

maintence_form_data = {
    "room_category": "My Room",
    "selected_room": None,
    "general_category": "Furniture",
    "item": "(Please Select Item)",
    "description": "",
    "comments": "",
}

test_room_options = [
    {
        "description": "Test Room",
        "space": "Test 100",
        "type": "Double",
    }]

refresh_requests = None

@ui.page("/maintenance")
def maintenance_page():
    render_site_header()
    with ui.column().classes(
        "site-shell w-full max-w-6xl mx-auto p-6 gap-6"
    ):
        ui.label("Maintenence").classes(
            "text-3xl font-bold"
        )

        ui.label(
            "You can submit a maintenance request for your room, suite, or apartment, as well as for public areas of your building. "
            "If you see an issue, please report it as soon as possible! Do not wait to report issues."
        ).classes("text-gray-600")
        
        render_maintenance_page()

def render_maintenance_page():
    global refresh_requests

    with ui.card().classes("welcome-card w-full p-6 mb-4"):
        ui.label("Existing Requests").classes("text-xl font-bold mb-2")

        ui.label(
            "Here you can see existing requests. Public requests are ones for public spaces like building lounges and public bathrooms. Private "
            "requests are those inside your living space such as your room, suite common area/bathroom."
        ).classes("text-gray-700 font-medium mb-4")
    
        @ui.refreshable
        def show_requests():
            requests = api_get("/maintenance-requests")
            selected_filter = filter_radio.value
            
            if selected_filter != "All":
                requests = [r for r in requests if r.get("type") == selected_filter]
                
            if not requests:
                ui.label("No maintenance requests found.").classes("text-gray-500 italic")
                return
                
            for req in requests:
                with ui.card().classes("w-full p-4 mb-2 bg-gray-50"):
                    ui.label(f"Room: {req['room']} ({req['room_type']})").classes("font-bold")
                    ui.label(f"Item: {req.get('item', 'N/A')}")
                    ui.label(f"Status: {req['status']}")
                    ui.label(f"Description: {req['description']}")

        refresh_requests = show_requests

        filter_radio = ui.radio(
            ["All", "Public", "Private"], 
            value="All",
            on_change=lambda: show_requests.refresh()
        ).props("inline").classes("mb-4")
        
        show_requests()

    with ui.card().classes("welcome-card w-full p-6"):
        ui.label("Submit a New Request").classes("text-xl font-bold mb-4")

        ui.label(
            "Submit a request for your room or a public space. Do not submit a maintenance request if your issue falls under one of the categories below:"
        ).classes("text-gray-700 font-medium mb-4")
        
        with ui.card().classes("w-full bg-red-50 border-l-4 border-red-500 p-4 mb-4 shadow-sm"):
            with ui.row().classes("items-center gap-1"):
                ui.label("Do not submit a request — Emergencies:").classes("font-bold text-red-700")
                ui.label("Smoke, fire and other life-threatening emergencies should be reported to 911 immediately.").classes("text-red-900")

        with ui.card().classes("w-full bg-amber-50 border-l-4 border-amber-500 p-4 mb-6 shadow-sm"):
            with ui.column().classes("gap-2"):
                with ui.row().classes("items-center gap-1"):
                    ui.label("Do not submit a request — Urgent issues:").classes("font-bold text-amber-800")
                    ui.label(
                        "Urgent issues should be reported directly to the UNH Facilities Control Center at 603-862-1437. "
                        "Urgent issues include leaking water, hot or cold water outages, heat outages, electrical outages, and broken/plugged toilets in single-use bathroom."
                    ).classes("text-amber-900")

        ui.button("Add Maintenance Request", on_click=lambda: open_add_request()).classes("mt-2")

def open_add_request():
    with ui.dialog() as dialog, ui.card().classes("w-[1000px] max-w-none"):
 
        with ui.card():
            ui.label("Select a Room").classes("text-xl font-bold")

            ui.radio(
                ["My Room", "Public Rooms"],
                value=maintence_form_data["room_category"],
            ).props("inline").bind_value(maintence_form_data, "room_category")

            with ui.row():
                ui.label("Select").classes("font-bold w-32")
                ui.label("Room Description").classes("font-bold w-40")
                ui.label("Room Space").classes("font-bold w-40")
                ui.label("Room Type").classes("font-bold w-40")

            room_options = {room["space"]: "" for room in test_room_options}
            
            def select_room(space):
                maintence_form_data["selected_room"] = space
                ui.notify(f"Selected room space: {space}")

            for room in test_room_options:
                with ui.row().classes("items-center"):
                    ui.radio(
                        {room["space"]: ""},
                        value=maintence_form_data["selected_room"],
                        on_change=lambda e, s=room["space"]: select_room(s) if e.value == s else None
                    ).classes("w-32")
                    ui.label(room["description"]).classes("w-40")
                    ui.label(room["space"]).classes("w-40")
                    ui.label(room["type"]).classes("w-40")

        ui.separator()

        with ui.card():
            ui.label("General").classes("text-xl font-bold")

            with ui.row().classes("w-full items-start gap-4"):
                with ui.column().classes("w-1/3"):
                    ui.select(
                        options=["Furniture", "Plumbing", "Electrical", "HVAC"],
                        value=maintence_form_data["general_category"],
                        label="Category",
                    ).classes("w-full").bind_value(maintence_form_data, "general_category")

                    ui.select(
                        options=[
                            "(Please Select Item)",
                            "Desk Chair",
                            "Bed Frame",
                            "Bookshelf",
                            "Whiteboard",
                        ],
                        value=maintence_form_data["item"],
                        label="Item",
                    ).classes("w-full").bind_value(maintence_form_data, "item")

                with ui.column().classes("flex-1"):
                    ui.textarea(
                        label="Description:",
                        value=maintence_form_data["description"],
                    ).classes("w-full").bind_value(maintence_form_data, "description")

            ui.separator()

            with ui.row().classes("w-full items-start gap-4"):
                with ui.column().classes("flex-1"):
                    ui.textarea(
                        label="Comments (e.g. phone number, requested time):",
                        value=maintence_form_data["comments"],
                    ).classes("w-full").bind_value(maintence_form_data, "comments")
                 
                with ui.column().classes("flex-1"):
                    with ui.card().classes("bg-green-900/25"):
                        ui.label(
                            "Per the Room & Board Agreement, staff may enter your space without you being present to complete maintenance. "
                            "Staff will always knock, wait for a response, and announce themselves before entering a room. "
                            "If you have any concerns, please include them, along with a phone number to reach you at, in the comments section above. "
                            "Please note that we may not be able to accommodate requests for staff to come by at a specific day/time."
                        ).classes("text-sm text-gray-600 text-bold")

        ui.separator()

        def handle_submit():
            global refresh_requests
            req_type = "Private" if maintence_form_data["room_category"] == "My Room" else "Public"
            selected_space = maintence_form_data["selected_room"]
            matched_room = next((r for r in test_room_options if r["space"] == selected_space), {})
            
            desc = maintence_form_data["description"].strip()
            comments = maintence_form_data["comments"].strip()
            full_description = f"{desc}\nComments: {comments}" if comments else desc

            body = {
                "type": req_type,
                "item": maintence_form_data["item"],
                "room": selected_space or "Unspecified Room",
                "room_type": matched_room.get("type", "Standard"),
                "status": "Pending",
                "description": full_description
            }
            
            if api_post("/add-maintenance-request", body):
                ui.notify("Request Sent", type="positive")
                if refresh_requests:
                    refresh_requests.refresh()
                dialog.close()
            else:
                ui.notify("Failed to send request", type="negative")

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Submit Request", on_click=handle_submit).props("color=green")

    dialog.open()