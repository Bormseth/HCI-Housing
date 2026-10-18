"""Run with: python -m unittest discover -s tests -v"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from housing_api import app


class RAApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.environment = patch.dict(os.environ, {
            "RA_DB_PATH": str(Path(self.temp.name) / "applications.sqlite3"),
            "RA_APPLICATIONS_OPEN": "true",
        })
        self.environment.start()
        self.client = TestClient(app)
        self.headers = {"X-RA-Session": str(uuid4())}

    def tearDown(self):
        self.client.close()
        self.environment.stop()
        self.temp.cleanup()

    def load(self, headers=None):
        return self.client.get("/ra/application", headers=headers or self.headers).json()

    def save(self, data, version=0):
        return self.client.put("/ra/application", headers=self.headers,
                               json={"data": data, "step": 2, "expected_version": version})

    def valid_data(self):
        return {
            "full_name": "Alex Student", "email": "alex@example.edu", "class_year": "Junior",
            "enrolled": True, "expectations": True, "certify": True,
            "motivation": "I want to help residents connect with their community. Through my club leadership experience, I have learned to listen carefully, include different perspectives, and organize welcoming events that help new students feel comfortable.",
            "scenario": "I would listen privately and ask what would help the resident feel more comfortable. Together we could find a small activity that fits their interests, connect with campus resources if needed, and arrange a follow-up conversation.",
        }

    def test_partial_draft_is_saved_and_available_to_a_new_client(self):
        self.assertEqual(self.save({"full_name": "Alex"}).status_code, 200)
        with TestClient(app) as fresh:
            saved = fresh.get("/ra/application", headers=self.headers).json()
        self.assertEqual(saved["data"]["full_name"], "Alex")
        self.assertEqual(saved["status"], "draft")
        self.assertEqual(saved["step"], 2)

    def test_browser_sessions_are_isolated(self):
        self.save(self.valid_data())
        other = self.load({"X-RA-Session": str(uuid4())})
        self.assertEqual(other["status"], "not_started")
        self.assertEqual(other["data"]["full_name"], "")

    def test_incomplete_application_cannot_be_submitted_through_api(self):
        self.save({"full_name": "Alex"})
        response = self.client.post("/ra/application/submit", headers=self.headers, json={"expected_version": 1})
        self.assertEqual(response.status_code, 422)
        self.assertIn("email", response.json()["detail"]["errors"])
        self.assertEqual(self.load()["status"], "draft")

    def test_stale_tab_cannot_overwrite_a_newer_draft(self):
        self.save({"full_name": "Newest answer"})
        response = self.save({"full_name": "Stale answer"}, version=0)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.load()["data"]["full_name"], "Newest answer")

    def test_successful_submission_is_idempotent(self):
        self.save(self.valid_data())
        first = self.client.post("/ra/application/submit", headers=self.headers, json={"expected_version": 1})
        second = self.client.post("/ra/application/submit", headers=self.headers, json={"expected_version": 1})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["status"], "submitted")
        self.assertTrue(first.json()["confirmation"].startswith("RA-DEMO-"))
        self.assertEqual(first.json()["confirmation"], second.json()["confirmation"])
        self.assertEqual(first.json()["submitted_at"], second.json()["submitted_at"])

    def test_submitted_application_cannot_be_overwritten(self):
        self.save(self.valid_data())
        self.client.post("/ra/application/submit", headers=self.headers, json={"expected_version": 1})
        self.assertEqual(self.save({"full_name": "Changed"}, version=2).status_code, 409)
        self.assertEqual(self.load()["data"]["full_name"], "Alex Student")

    def test_closed_cycle_preserves_draft_and_blocks_submission(self):
        self.save(self.valid_data())
        with patch.dict(os.environ, {"RA_APPLICATIONS_OPEN": "false"}):
            self.assertFalse(self.client.get("/ra/cycle").json()["open"])
            response = self.client.post("/ra/application/submit", headers=self.headers, json={"expected_version": 1})
            self.assertEqual(response.status_code, 409)
        self.assertEqual(self.load()["status"], "draft")

    def test_reset_only_clears_the_current_browser_record(self):
        self.save(self.valid_data())
        other = {"X-RA-Session": str(uuid4())}
        self.client.put("/ra/application", headers=other, json={"data": {"full_name": "Other student"}, "expected_version": 0})
        self.client.delete("/ra/application", headers=self.headers)
        self.assertEqual(self.load()["status"], "not_started")
        self.assertEqual(self.load(other)["data"]["full_name"], "Other student")

    def test_invalid_session_and_unexpected_fields_are_rejected(self):
        response = self.client.get("/ra/application", headers={"X-RA-Session": "invalid"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.save({"status": "submitted"}).status_code, 422)

    def test_existing_housing_api_still_responds(self):
        self.assertEqual(self.client.get("/buildings").status_code, 200)
        self.assertEqual(self.client.get("/room-types").status_code, 200)


if __name__ == "__main__":
    unittest.main()
