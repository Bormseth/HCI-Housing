
from nicegui import ui

from components.header import render_site_header


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
def housing_application_2026_page():
    render_site_header()

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

        with ui.stepper().classes("w-full") as stepper:
            with ui.step("Student Information"):
                ui.label(
                    "Enter your student information."
                ).classes("text-lg font-semibold")

                student_name = ui.input(
                    "Full Name",
                    placeholder="Enter your full name",
                ).classes("w-full")

                student_email = ui.input(
                    "University Email",
                    placeholder="you@unh.edu",
                ).classes("w-full")

                student_id = ui.input(
                    "Student ID",
                    placeholder="Enter your student ID",
                ).classes("w-full")

                class_year = ui.select(
                    ["First-year", "Sophomore", "Junior", "Senior"],
                    label="Class Year",
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
                    [
                        "Traditional Residence Hall",
                        "Suite-Style Housing",
                        "Apartment-Style Housing",
                        "No Preference",
                    ],
                    label="Preferred Housing Style",
                    value="No Preference",
                ).classes("w-full")

                room_preference = ui.select(
                    [
                        "Single",
                        "Double",
                        "Triple",
                        "No Preference",
                    ],
                    label="Preferred Room Type",
                    value="No Preference",
                ).classes("w-full")

                accessibility = ui.textarea(
                    "Additional Housing Considerations",
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
                    [
                        "I have a preferred roommate",
                        "I would like a roommate assigned",
                        "I prefer a single room",
                    ],
                    value="I would like a roommate assigned",
                ).props("inline")

                roommate_name = ui.input(
                    "Preferred Roommate Name (Optional)",
                    placeholder="Enter roommate name",
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

                ui.button(
                    "Refresh Review",
                    on_click=update_review,
                ).props("outline")

                with ui.stepper_navigation():
                    ui.button(
                        "Submit Application",
                        icon="check",
                        on_click=lambda: submit_application(
                            student_name.value,
                            student_email.value,
                            student_id.value,
                            class_year.value,
                            housing_style.value,
                            room_preference.value,
                            accessibility.value,
                            roommate_preference.value,
                            roommate_name.value,
                        ),
                    )
                    ui.button(
                        "Back",
                        on_click=lambda: stepper.previous(),
                    ).props("flat")


def submit_application(
    name,
    email,
    student_id,
    class_year,
    housing_style,
    room_preference,
    accessibility,
    roommate_preference,
    roommate_name,
):
    if not name or not email or not student_id or not class_year:
        ui.notify(
            "Please complete all student information fields.",
            type="warning",
        )
        return

    ui.notify(
        "Form validated, but submission is not connected "
        "to the backend yet.",
        type="info",
    )
