from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from nicegui import app, ui

from components.header import render_site_header
from components.housing_card import (
    render_current_housing_card,
    render_housing_card,
)
from components.my_housing import render_no_housing_message
from services.api_client import APIError, api_request


# Where the "Housing Selection" button sends students (pages/housing_selection.py)
SELECTION_ROUTE = "/housing-applications/room-select"

YEAR_SLUG = "2026-2027"

# Keep these in sync with the option lists in housing_api.py.
CLASS_YEARS = ["First-year", "Sophomore", "Junior", "Senior"]
HOUSING_STYLES = [
    "Traditional Residence Hall",
    "Suite-Style Housing",
    "Apartment-Style Housing",
    "No Preference",
]
ROOM_PREFERENCES = ["Single", "Double", "Triple", "No Preference"]
ROOMMATE_PREFERENCES = [
    "I have a preferred roommate",
    "I would like a roommate assigned",
    "I prefer a single room",
]


HOUSING_YEARS = [
    {
        "year": "2026–2027",
        "route": "/housing-applications/2026-2027",
        "available": True,
        "description": "Apply for campus housing for the 2026–2027 academic year.",
    },
    {
        "year": "2025–2026",
        "route": None,
        "available": False,
        "description": "Applications are closed.",
    },
    {
        "year": "2027–2028",
        "route": None,
        "available": False,
        "description": "Applications are not yet available.",
    },
    {
        "year": "2028–2029",
        "route": None,
        "available": False,
        "description": "Applications are not yet available.",
    },
]


@ui.page("/housing-applications")
def housing_applications_page():
    render_site_header()

    with ui.column().classes(
        "site-shell w-full max-w-6xl mx-auto p-6 gap-6"
    ):
        ui.label("Housing Applications").classes(
            "text-3xl font-bold"
        )

        ui.label(
            "Choose an academic year to view its housing application."
        ).classes("text-gray-600")

        with ui.grid(columns=2).classes("w-full gap-6"):
            for application in HOUSING_YEARS:
                render_year_card(application)


def render_year_card(application: dict):
    with ui.card().classes(
        "w-full p-6 rounded-xl shadow-sm"
    ):
        with ui.row().classes(
            "w-full items-center justify-between"
        ):
            ui.label(application["year"]).classes(
                "text-xl font-bold"
            )

            if application["available"]:
                ui.badge("Available", color="positive")
            else:
                ui.badge("Unavailable", color="grey")

        ui.label(application["description"]).classes(
            "text-gray-600"
        )

        if application["available"]:
            ui.button(
                "Start Application",
                icon="arrow_forward",
                on_click=lambda route=application["route"]:
                    ui.navigate.to(route),
            ).classes("mt-4")
        else:
            ui.button(
                "Unavailable",
            ).classes("mt-4")


@ui.page("/housing-applications/2026-2027")
async def housing_application_2026_page():
    render_site_header()

    # Load any previously submitted application so the student can see and change it.
    existing = None
    try:
        existing = await housing_request("GET")
    except APIError as error:
        ui.notify(str(error), type="negative", close_button=True)
    saved = existing["data"] if existing else {}

    with ui.column().classes(
        "site-shell w-full max-w-4xl mx-auto p-6 gap-6"
    ):
        with ui.row().classes("items-center gap-2"):
            ui.button(
                icon="arrow_back",
                on_click=lambda: ui.navigate.to(
                    "/housing-applications"
                ),
            ).props("flat round")

            ui.label("Housing Applications").classes(
                "text-gray-500"
            )

        ui.label(
            "2026–2027 Housing Application"
        ).classes("text-3xl font-bold")

        ui.label(
            "Complete the following information to begin your "
            "on-campus housing application."
        ).classes("text-gray-600")

        if existing:
            existing_application_banner(existing)

        with ui.stepper().classes("w-full") as stepper:
            with ui.step("Student Information"):
                ui.label(
                    "Enter your student information."
                ).classes("text-lg font-semibold")

                student_name = ui.input(
                    "Full Name",
                    value=saved.get("full_name", ""),
                    placeholder="Enter your full name",
                ).classes("w-full")

                student_email = ui.input(
                    "University Email",
                    value=saved.get("email", ""),
                    placeholder="you@unh.edu",
                ).classes("w-full")

                student_id = ui.input(
                    "Student ID",
                    value=saved.get("student_id", ""),
                    placeholder="Enter your student ID",
                ).classes("w-full")

                class_year = ui.select(
                    CLASS_YEARS,
                    label="Class Year",
                    value=saved.get("class_year") or None,
                ).classes("w-full")

                with ui.stepper_navigation():
                    ui.button(
                        "Next",
                        on_click=lambda: stepper.next(),
                    )

            with ui.step("Housing Preferences"):
                ui.label(
                    "Tell us about your housing preferences."
                ).classes("text-lg font-semibold")

                housing_style = ui.select(
                    HOUSING_STYLES,
                    label="Preferred Housing Style",
                    value=saved.get("housing_style") or "No Preference",
                ).classes("w-full")

                room_preference = ui.select(
                    ROOM_PREFERENCES,
                    label="Preferred Room Type",
                    value=saved.get("room_preference") or "No Preference",
                ).classes("w-full")

                accessibility = ui.textarea(
                    "Additional Housing Considerations",
                    value=saved.get("additional_considerations", ""),
                    placeholder=(
                        "Enter any additional information "
                        "you would like considered."
                    ),
                ).classes("w-full")

                with ui.stepper_navigation():
                    ui.button(
                        "Next",
                        on_click=lambda: stepper.next(),
                    )
                    ui.button(
                        "Back",
                        on_click=lambda: stepper.previous(),
                    ).props("flat")

            with ui.step("Roommate Preferences"):
                ui.label(
                    "Provide your roommate preferences."
                ).classes("text-lg font-semibold")

                roommate_preference = ui.radio(
                    ROOMMATE_PREFERENCES,
                    value=saved.get("roommate_preference")
                    or "I would like a roommate assigned",
                ).props("inline")

                roommate_name = ui.input(
                    "Preferred Roommate Name (Optional)",
                    value=saved.get("roommate_name", ""),
                    placeholder="Enter roommate name",
                ).classes("w-full")

                with ui.stepper_navigation():
                    ui.button(
                        "Next",
                        on_click=lambda: (update_review(), stepper.next()),
                    )
                    ui.button(
                        "Back",
                        on_click=lambda: stepper.previous(),
                    ).props("flat")

            with ui.step("Review and Submit"):
                ui.label(
                    "Review Your Application"
                ).classes("text-lg font-semibold")

                ui.label(
                    "Review your information before submitting."
                )

                review = ui.column().classes("w-full gap-2")

                def update_review():
                    review.clear()

                    with review:
                        ui.label(
                            f"Name: {student_name.value or 'Not entered'}"
                        )
                        ui.label(
                            f"Email: {student_email.value or 'Not entered'}"
                        )
                        ui.label(
                            f"Student ID: {student_id.value or 'Not entered'}"
                        )
                        ui.label(
                            f"Class Year: {class_year.value or 'Not selected'}"
                        )
                        ui.label(
                            f"Housing: {housing_style.value}"
                        )
                        ui.label(
                            f"Room: {room_preference.value}"
                        )
                        ui.label(
                            f"Roommate Preference: {roommate_preference.value}"
                        )
                        ui.label(
                            f"Preferred Roommate: "
                            f"{roommate_name.value or 'None specified'}"
                        )

                def collect():
                    return {
                        "full_name": student_name.value or "",
                        "email": student_email.value or "",
                        "student_id": student_id.value or "",
                        "class_year": class_year.value or "",
                        "housing_style": housing_style.value or "",
                        "room_preference": room_preference.value or "",
                        "additional_considerations": accessibility.value or "",
                        "roommate_preference": roommate_preference.value or "",
                        "roommate_name": roommate_name.value or "",
                    }

                with ui.stepper_navigation():
                    submit_button = ui.button(
                        "Submit Application",
                        icon="check",
                        on_click=lambda: submit_application(
                            collect(),
                            submit_button,
                            stepper,
                            confirmation_content,
                        ),
                    )
                    ui.button(
                        "Back",
                        on_click=lambda: stepper.previous(),
                    ).props("flat")

            with ui.step("Confirmation"):
                confirmation_content = ui.column().classes("w-full")


async def housing_request(method, data=None):
    # Same per-browser session id the RA application and meal plans use.
    session = app.storage.user.get("ra_session")
    if not session:
        session = str(uuid4())
        app.storage.user["ra_session"] = session
    return await api_request(
        method, f"/housing-applications/{YEAR_SLUG}", data, session=session
    )


def format_time(value):
    return (
        datetime.fromisoformat(value)
        .astimezone(ZoneInfo("America/New_York"))
        .strftime("%b %d, %Y at %I:%M %p ET")
    )


def existing_application_banner(existing):
    async def cancel():
        try:
            await housing_request("DELETE")
            ui.navigate.reload()
        except APIError as error:
            ui.notify(str(error), type="negative", close_button=True)

    with ui.card().classes("w-full p-4 rounded-xl shadow-sm"):
        ui.label(
            f"You submitted this application on "
            f"{format_time(existing['submitted_at'])}."
        ).classes("font-semibold")
        ui.label(
            f"Confirmation {existing['confirmation']}. Submitting again "
            "below replaces your saved application."
        ).classes("text-sm text-gray-600")
        ui.button(
            "Cancel application", icon="close", on_click=cancel
        ).props("flat dense")


def show_confirmation(record, confirmation_content):
    data = record["data"]
    confirmation_content.clear()

    with confirmation_content:
        with ui.card().classes("w-full p-6 rounded-xl shadow-sm gap-2"):
            with ui.row().classes("items-center"):
                ui.icon("check_circle", color="positive")
                ui.label("Application submitted").classes(
                    "text-2xl font-bold"
                )

            ui.label(f"Confirmation: {record['confirmation']}").classes(
                "font-semibold"
            )
            ui.label(
                f"Submitted {format_time(record['submitted_at'])}"
            ).classes("text-gray-600")
            ui.label(
                f"{data['full_name']} · {data['class_year']} · "
                f"{data['housing_style']} · {data['room_preference']}"
            )
            ui.label(
                "This is a prototype. Nothing is sent to UNH."
            ).classes("text-sm text-gray-500")

            ui.separator()

            ui.label("Next Step: Housing Selection").classes(
                "text-lg font-semibold"
            )
            ui.label(
                "Browse the residence halls and apartments and choose "
                "a room type."
            ).classes("text-gray-600")

            with ui.row().classes("gap-2 mt-2"):
                ui.button(
                    "Go to Housing Selection",
                    icon="arrow_forward",
                    on_click=lambda: ui.navigate.to(SELECTION_ROUTE),
                )
                ui.button(
                    "Back to Housing Applications",
                    icon="arrow_back",
                    on_click=lambda: ui.navigate.to("/housing-applications"),
                ).props("flat")


async def submit_application(payload, button, stepper, confirmation_content):
    if not (
        payload["full_name"]
        and payload["email"]
        and payload["student_id"]
        and payload["class_year"]
    ):
        ui.notify(
            "Please complete all student information fields.",
            type="warning",
        )
        return

    button.disable()  # prevent double submits while the request is in flight
    try:
        record = await housing_request("POST", payload)
    except APIError as error:
        details = " ".join(error.errors.values())
        ui.notify(
            f"{error} {details}".strip(),
            type="negative",
            close_button=True,
        )
        return
    finally:
        button.enable()

    show_confirmation(record, confirmation_content)
    stepper.next()