from nicegui import ui


def render_announcement_card(announcement: dict):
    with ui.card().classes("w-full"):
        ui.label(announcement["title"]).classes("font-bold")
        ui.label(announcement["body"])
