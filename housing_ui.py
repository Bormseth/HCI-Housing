import os

from nicegui import ui

from pages import housing_application, meal_plan, become_an_ra, housing_selection

from components.header import render_site_header


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


def render_placeholder_page(title: str):
    render_site_header()
    with ui.column().classes("home-content w-full"):
        with ui.card().classes("welcome-card w-full"):
            ui.label(title).classes("welcome-title")
            ui.label(
                "This section is not available in the current portal prototype."
            ).classes("welcome-copy")

@ui.page("/my-profile")
def my_profile_page():
    render_placeholder_page("My Profile")


@ui.page("/messages")
def messages_page():
    render_placeholder_page("Messages")



ui.run(host=os.getenv("HOUSING_UI_HOST", "127.0.0.1"), port=8085, title="Mock Housing Portal", reload=False, show=False,
       storage_secret=os.getenv("STORAGE_SECRET", "local-housing-prototype-only"))
