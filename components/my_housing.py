from nicegui import ui


def render_no_housing_message():
    ui.label("You haven't selected housing yet.")
    with ui.link(target="/housing-applications/room-select"): ui.button("Select Room")
