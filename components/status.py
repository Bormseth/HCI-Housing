"""Reusable, persistent status messages for portal actions."""

from nicegui import ui


def render_status_region():
    """Render an initially empty status region and return its label element."""
    return (
        ui.label("")
        .classes("portal-status w-full")
        .props('role="status" aria-live="polite" aria-atomic="true"')
    )


def set_status(status, message: str, *, error: bool = False):
    """Update a persistent status region with text a user can review."""
    status.set_text(message)
    status.classes(
        add="text-red-700" if error else "text-green-800",
        remove="text-red-700" if not error else "text-green-800",
    )
