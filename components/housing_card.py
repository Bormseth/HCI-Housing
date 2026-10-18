from nicegui import ui


def render_housing_card(room_type: dict, on_select):
    """Render an available room type with a Select action."""
    with ui.card().classes("w-full"):
        ui.label(
            f'{room_type["building_name"]} - {room_type["name"]}'
        ).classes("font-bold")

        ui.label(f'${room_type["price_per_term"]}/term')
        ui.label(
            f'{room_type["spaces_open"]}/{room_type["total_spaces"]} open'
        )

        ui.button(
            "Select",
            on_click=lambda room_type_id=room_type["id"]: on_select(room_type_id),
        )


def render_current_housing_card(housing: dict):
    """Render the user's current housing selection with a Cancel action."""
    with ui.card().classes("w-full"):
        ui.label(
            f'{housing["building_name"]} - {housing["style"].capitalize()} {format_room_type(housing["room_type"])}'
            ).classes("font-bold")
        with ui.link(target="/housing-applications/room-select"): ui.button("Change")

def format_room_type(slug: str) -> str:
    """'super_single' -> 'Super Single', '2_doubles_1_single' -> '2 Doubles + 1 Single'"""
    parts = slug.split("_")
    if not parts[0].isdigit():
        return " ".join(parts).title()
    return " + ".join(f"{parts[i]} {parts[i + 1].title()}" for i in range(0, len(parts), 2))

def render_building_card(building):
    with ui.card():
        with ui.row():
            ui.label(text=building["name"])
        with ui.row():
            with ui.link(target=building["url"], new_tab=True): ui.button("More Info")
            with ui.link(target=f"/housing-applications/room-select/{building['id']}"): ui.button("Choose Room")