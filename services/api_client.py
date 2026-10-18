"""Shared API requests for the Housing Portal and RA application."""

import asyncio
import os

import requests
from nicegui import ui

API_BASE = os.getenv("HOUSING_API_BASE", "http://127.0.0.1:8006").rstrip("/")


class APIError(Exception):
    def __init__(self, message: str, errors: dict | None = None):
        super().__init__(message)
        self.errors = errors or {}


def _request(method: str, path: str, json=None, session: str | None = None):
    try:
        with requests.Session() as client:
            client.trust_env = False
            response = client.request(method, f"{API_BASE}{path}", json=json, timeout=5,
                                      headers={"X-RA-Session": session} if session else {})
    except requests.RequestException:
        raise APIError("The application service is unavailable. Your current edits are still on this page. Try again when the service is running.") from None

    try:
        result = response.json()
    except ValueError:
        raise APIError("The application service returned an unexpected response. Please try again.") from None
    if response.status_code >= 400:
        detail = result.get("detail") if isinstance(result, dict) else None
        detail = detail or "The request could not be completed. Please try again."
        if isinstance(detail, dict):
            raise APIError(detail.get("message", "Check your information and try again."), detail.get("errors"))
        if not isinstance(detail, str):
            detail = "Some information could not be saved. Check the field lengths and try again."
        raise APIError(detail)
    return result


async def api_request(method: str, path: str, json=None, *, session: str | None = None):
    """Run requests off the UI thread and return the API's data or field errors."""
    return await asyncio.to_thread(_request, method, path, json, session)


def api_get(path: str):
    """Preserve the original housing client's return value on failure."""
    try:
        return _request("GET", path)
    except APIError as error:
        ui.notify(str(error), type="negative")
        return []


def api_post(path: str, json: dict = None):
    try:
        _request("POST", path, json)
        return True
    except APIError as error:
        ui.notify(str(error), type="negative")
        return False
