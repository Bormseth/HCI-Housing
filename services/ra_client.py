"""Async RA requests; keep network failures from freezing the NiceGUI page."""

import os

import httpx


class RARequestError(Exception):
    pass


class RAClient:
    def __init__(self, session: str):
        self.session = session
        self.base = os.getenv("HOUSING_API_BASE", "http://127.0.0.1:8006").rstrip("/")

    async def request(self, method: str, path: str, payload=None):
        try:
            async with httpx.AsyncClient(timeout=5, trust_env=False) as client:
                response = await client.request(method, f"{self.base}/ra{path}", json=payload,
                                                headers={"X-RA-Session": self.session})
        except httpx.RequestError:
            raise RARequestError("We couldn't reach the application service. Your edits are still on this page. Try again when the service is available.") from None
        if response.is_error:
            try:
                detail = response.json().get("detail", "We couldn't save your application. Please try again.")
            except ValueError:
                raise RARequestError("The application service had a problem. Your edits are still on this page. Please try again.") from None
            if isinstance(detail, dict):
                detail = detail.get("message", "Check the required fields and try again.")
            elif not isinstance(detail, str):
                detail = "Some information could not be saved. Check the field lengths and try again."
            raise RARequestError(detail)
        return response.json()

    async def load(self):
        return await self.request("GET", "/application")

    async def cycle(self):
        return await self.request("GET", "/cycle")

    async def save(self, data, step, version):
        return await self.request("PUT", "/application", {"data": data, "step": step, "expected_version": version})

    async def submit(self, version):
        return await self.request("POST", "/application/submit", {"expected_version": version})
