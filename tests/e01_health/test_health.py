import json
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from main import app  # noqa: E402


class HealthEndpointTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_health_returns_expected_status_payload(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "service": "mindvox-api",
                "version": "v1.0.0",
            },
        )

    def test_health_response_exposes_only_public_fields(self):
        response = self.client.get("/health")
        payload = response.json()
        serialized_payload = json.dumps(payload).lower()
        forbidden_terms = [
            "authorization",
            "token",
            "secret",
            "password",
            ".env",
            "audio",
            "transcription",
            "model",
            "path",
            "/users/",
        ]

        self.assertEqual(set(payload), {"status", "service", "version"})
        for term in forbidden_terms:
            self.assertNotIn(term, serialized_payload)

    def test_post_health_is_not_allowed(self):
        response = self.client.post("/health")

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json(), {"detail": "Method Not Allowed"})

    def test_openapi_documents_health_endpoint(self):
        response = self.client.get("/openapi.json")
        openapi = response.json()
        health_get = openapi["paths"]["/health"]["get"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(health_get["summary"], "Health Check")
        self.assertEqual(
            health_get["description"],
            "Returns a minimal health status for the Mindvox API.",
        )

    def test_openapi_declares_no_url_parameters_and_no_body(self):
        response = self.client.get("/openapi.json")
        openapi = response.json()
        health_get = openapi["paths"]["/health"]["get"]

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("parameters", health_get)
        self.assertNotIn("requestBody", health_get)


if __name__ == "__main__":
    unittest.main()
