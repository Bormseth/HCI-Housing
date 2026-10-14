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


def render_current_housing_card(housing: dict, on_cancel):
    """Render the user's current housing selection with a Cancel action."""
    with ui.card().classes("w-full"):
        ui.label(
            f'{housing["building_name"]} - {housing["name"]}'
        ).classes("font-bold")
        ui.label(f'${housing["price_per_term"]}/term')
        ui.button("Cancel", on_click=on_cancel).props("color=negative outline")
