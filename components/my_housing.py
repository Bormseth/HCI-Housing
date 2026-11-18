from nicegui import ui


def render_no_housing_message():
    ui.label("You haven't selected housing yet.")
    ui.button(
        "Select Room",
        on_click=lambda: ui.navigate.to("/housing-applications/room-select"),
    )
