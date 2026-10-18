
from nicegui import ui

from components.header import render_site_header


# Sample prototype data. Replace with official UNH meal plan details.
DINING_HALLS = [
    {
        "name": "Holloway Commons",
        "description": (
            "A residential dining location with a variety "
            "of meals and dining options."
        ),
    },
    {
        "name": "Philbrook Dining",
        "description": (
            "A campus dining location offering meals and "
            "options for students."
        ),
    },
    {
        "name": "Stillings Dining Hall",
        "description": (
            "A residential dining location for everyday "
            "campus dining."
        ),
    },
]

MEAL_PLANS = [
    {
        "name": "Unlimited",
        "price": 3200.00,
        "swipes": "Unlimited meal swipes",
        "description": (
            "For students who want frequent access "
            "to residential dining."
        ),
    },
    {
        "name": "14 Meals Per Week",
        "price": 2800.00,
        "swipes": "14 meal swipes per week",
        "description": (
            "A flexible option for students who eat "
            "most meals on campus."
        ),
    },
    {
        "name": "10 Meals Per Week",
        "price": 2400.00,
        "swipes": "10 meal swipes per week",
        "description": (
            "For students who want a smaller weekly "
            "meal allowance."
        ),
    },
    {
        "name": "7 Meals Per Week",
        "price": 2000.00,
        "swipes": "7 meal swipes per week",
        "description": (
            "For students who plan to eat on campus "
            "once a day on average."
        ),
    },
]

DINING_DOLLAR_OPTIONS = [
    {
        "amount": 0,
        "price": 0.00,
        "description": "No additional Dining Dollars.",
    },
    {
        "amount": 100,
        "price": 100.00,
        "description": "$100 to spend at eligible campus dining locations.",
    },
    {
        "amount": 250,
        "price": 250.00,
        "description": "$250 for additional dining flexibility.",
    },
    {
        "amount": 500,
        "price": 500.00,
        "description": "$500 for frequent purchases at eligible locations.",
    },
]

MEAL_PLAN_YEARS = [
    {
        "year": "2026–2027",
        "route": "/meal-plans/2026-2027",
        "available": True,
        "description": "Choose your meal plan for 2026–2027.",
    },
    {
        "year": "2025–2026",
        "route": None,
        "available": False,
        "description": "Meal plan selection is closed.",
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


@ui.page("/meal-plans")
def meal_plans_page():
    render_site_header()

    with ui.column().classes(
        "site-shell w-full max-w-6xl mx-auto p-6 gap-6"
    ):
        ui.label("Meal Plans").classes("text-3xl font-bold")

        ui.label(
            "Choose an academic year to view its available meal plans."
        ).classes("text-gray-600")

        with ui.grid(columns=2).classes("w-full gap-6"):
            for year in MEAL_PLAN_YEARS:
                with ui.card().classes(
                    "w-full p-6 rounded-xl shadow-sm"
                ):
                    with ui.row().classes(
                        "w-full items-center justify-between"
                    ):
                        ui.label(year["year"]).classes(
                            "text-xl font-bold"
                        )

                        if year["available"]:
                            ui.badge("Available", color="positive")
                        else:
                            ui.badge("Unavailable", color="grey")

                    ui.label(year["description"]).classes(
                        "text-gray-600"
                    )

                    if year["available"]:
                        ui.button(
                            "Choose Meal Plan",
                            icon="arrow_forward",
                            on_click=lambda route=year["route"]:
                                ui.navigate.to(route),
                        ).classes("mt-4")
                    else:
                        ui.button("Unavailable").props(
                            "disable"
                        ).classes("mt-4")

@ui.page("/meal-plans/2026-2027")
def meal_plan_application_2026():
    render_site_header()

    application = {
        "terms_accepted": False,
        "meal_plan": None,
        "dining_dollars": DINING_DOLLAR_OPTIONS[0],
    }

    with ui.column().classes(
        "site-shell w-full max-w-6xl mx-auto p-6 gap-6"
    ):
        with ui.row().classes("w-full items-center"):
            ui.button(
                "Back to Academic Years",
                icon="arrow_back",
                on_click=lambda: ui.navigate.to("/meal-plans"),
            ).props("flat")

        ui.label("2026–2027 Meal Plan Application").classes(
            "text-3xl font-bold"
        )

        ui.label(
            "Review the dining information, select your meal plan, "
            "choose any additional Dining Dollars, and review your choices."
        ).classes("text-gray-600")

        with ui.stepper().props("contractable=false").classes("w-full") as stepper:

            with ui.step("Introduction"):
                ui.label("Explore Campus Dining").classes(
                    "text-2xl font-bold"
                )

                with ui.grid(columns=3).classes("w-full gap-4"):
                    for hall in DINING_HALLS:
                        with ui.card().classes("w-full"):
                            ui.label(hall["name"]).classes(
                                "text-lg font-semibold"
                            )
                            ui.label(hall["description"])

                ui.separator()

                ui.label("Meal Plan Terms").classes(
                    "text-xl font-bold"
                )

                ui.label(
                    "This is a prototype application. Meal plan prices "
                    "and options are examples and are not official UNH "
                    "pricing. Review your selection before submitting."
                ).classes("text-gray-600")

                terms_checkbox = ui.checkbox(
                    "I have read and agree to the meal plan terms."
                )

                ui.button(
                    "Continue",
                    on_click=lambda: continue_from_intro(
                        stepper, application, terms_checkbox.value
                    ),
                )

            with ui.step("Select Meal Plan"):
                ui.label("Choose Your Meal Plan").classes(
                    "text-2xl font-bold"
                )

                plan_status = ui.label(
                    "No meal plan selected."
                ).classes("text-gray-600")

                with ui.grid(columns=2).classes("w-full gap-4"):
                    for plan in MEAL_PLANS:
                        with ui.card().classes("w-full p-4"):
                            ui.label(plan["name"]).classes(
                                "text-xl font-bold"
                            )

                            ui.label(
                                f"${plan['price']:,.2f} (sample price)"
                            ).classes("text-lg")

                            ui.label(plan["swipes"]).classes(
                                "font-semibold"
                            )

                            ui.label(plan["description"])

                            ui.button(
                                "Select Plan",
                                on_click=lambda p=plan: select_meal_plan(
                                    p, application, plan_status
                                ),
                            ).classes("mt-2")

                with ui.row().classes("w-full justify-between"):
                    ui.button(
                        "Back",
                        on_click=stepper.previous,
                    ).props("flat")

                    ui.button(
                        "Continue",
                        on_click=lambda: continue_to_dining_dollars(
                            stepper, application
                        ),
                    )

            with ui.step("Dining Dollars"):
                ui.label("Add Dining Dollars").classes(
                    "text-2xl font-bold"
                )

                ui.label(
                    "Choose an optional amount to add to your account."
                ).classes("text-gray-600")

                dollars_status = ui.label(
                    "Selected amount: $0.00"
                ).classes("text-gray-600")

                with ui.grid(columns=2).classes("w-full gap-4"):
                    for option in DINING_DOLLAR_OPTIONS:
                        with ui.card().classes("w-full p-4"):
                            ui.label(
                                f"${option['amount']:,.0f} Dining Dollars"
                            ).classes("text-lg font-bold")

                            ui.label(
                                f"Cost: ${option['price']:,.2f}"
                            )

                            ui.label(option["description"])

                            ui.button(
                                "Select",
                                on_click=lambda o=option: select_dining_dollars(
                                    o, application, dollars_status
                                ),
                            )

                with ui.row().classes("w-full justify-between"):
                    ui.button(
                        "Back",
                        on_click=stepper.previous,
                    ).props("flat")

                    ui.button(
                        "Review Summary",
                        on_click=lambda: show_summary(
                            stepper, application, summary_content
                        ),
                    )

            with ui.step("Summary"):
                ui.label("Review Your Selections").classes(
                    "text-2xl font-bold"
                )

                summary_content = ui.column().classes("w-full")

                with ui.row().classes("w-full justify-between"):
                    ui.button(
                        "Back",
                        on_click=stepper.previous,
                    ).props("flat")

                    ui.button(
                        "Confirm Selection",
                        on_click=lambda: confirm_meal_plan(application),
                    )


def continue_from_intro(stepper, application, accepted):
    if not accepted:
        ui.notify(
            "Please agree to the meal plan terms before continuing.",
            type="warning",
        )
        return

    application["terms_accepted"] = True
    stepper.next()


def select_meal_plan(plan, application, status_label):
    application["meal_plan"] = plan

    status_label.set_text(
        f"Selected: {plan['name']} — ${plan['price']:,.2f}"
    )

    ui.notify(f"{plan['name']} selected.", type="positive")


def continue_to_dining_dollars(stepper, application):
    if application["meal_plan"] is None:
        ui.notify(
            "Please select a meal plan before continuing.",
            type="warning",
        )
        return

    stepper.next()


def select_dining_dollars(option, application, status_label):
    application["dining_dollars"] = option

    status_label.set_text(
        f"Selected amount: ${option['amount']:,.2f}"
    )

    ui.notify(
        f"${option['amount']} in Dining Dollars selected.",
        type="positive",
    )


def show_summary(stepper, application, summary_content):
    if application["meal_plan"] is None:
        ui.notify(
            "Please select a meal plan first.",
            type="warning",
        )
        return

    plan = application["meal_plan"]
    dollars = application["dining_dollars"]

    total = plan["price"] + dollars["price"]

    summary_content.clear()

    with summary_content:
        with ui.card().classes(
            "w-full p-6 rounded-xl shadow-sm"
        ):
            ui.label("Selected Meal Plan").classes(
                "text-lg font-semibold"
            )

            ui.label(plan["name"]).classes(
                "text-2xl font-bold"
            )

            ui.label(plan["swipes"]).classes(
                "text-gray-600"
            )

            ui.separator()

            ui.label("Additional Dining Dollars").classes(
                "text-lg font-semibold"
            )

            ui.label(
                f"${dollars['amount']:,.2f}"
            ).classes("text-xl font-bold")

            ui.separator()

            ui.label("Cost Breakdown").classes(
                "text-lg font-semibold"
            )

            with ui.row().classes(
                "w-full justify-between"
            ):
                ui.label("Meal Plan")

                ui.label(
                    f"${plan['price']:,.2f}"
                )

            with ui.row().classes(
                "w-full justify-between"
            ):
                ui.label("Dining Dollars")

                ui.label(
                    f"${dollars['price']:,.2f}"
                )

            ui.separator()

            with ui.row().classes(
                "w-full justify-between items-center"
            ):
                ui.label("Total Sample Cost").classes(
                    "text-xl font-bold"
                )

                ui.label(
                    f"${total:,.2f}"
                ).classes("text-2xl font-bold")

            ui.label(
                "This is a prototype estimate, not an official "
                "university bill."
            ).classes("text-sm text-gray-500")

    stepper.next()


def confirm_meal_plan(application):
    if not application["terms_accepted"]:
        ui.notify(
            "Please accept the meal plan terms.",
            type="warning",
        )
        return

    if application["meal_plan"] is None:
        ui.notify(
            "Please select a meal plan.",
            type="warning",
        )
        return

    ui.notify(
        "Your selections have been validated. "
        "Submission is not connected to a backend yet.",
        type="positive",
        timeout=5000,
    )
