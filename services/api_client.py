import requests
from nicegui import ui

API_BASE = "http://localhost:8006"


def api_get(path: str):
    try:
        response = requests.get(f"{API_BASE}{path}", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        ui.notify(f"Could not reach API: {error}", type="negative")
        return []


def api_post(path: str, json: dict = None):
    try:
        response = requests.post(f"{API_BASE}{path}", json=json, timeout=5)
        response.raise_for_status()
        return True
    except requests.RequestException as error:
        detail = ""
        try:
            detail = error.response.json().get("detail", "")
        except (AttributeError, ValueError):
            pass
        ui.notify(detail or f"Request failed: {error}", type="negative")
        return False
