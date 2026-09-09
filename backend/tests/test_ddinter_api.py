import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from ddinter.repository import Repository, connect, initialize
from main import app
from tests.support import populate_mock_catalog


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "mock.sqlite"
        connection = connect(self.path)
        initialize(connection)
        self.a, self.b, self.c, self.d = populate_mock_catalog(Repository(connection))
        connection.close()
        env = patch.dict(os.environ, {"DDINTER_DB_PATH": str(self.path), "MOCK_EXTRACT": "1"})
        env.start()
        self.addCleanup(env.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_pair_multi_search_details_alternatives(self):
        pair = self.client.get("/interactions/check", params={"drug_a": "mock brand a", "drug_b": "Drug B"})
        self.assertEqual(pair.status_code, 200)
        self.assertEqual(pair.json()["comparisons"], 1)
        interaction_id = pair.json()["interactions"][0]["interaction"]["id"]
        details = self.client.get(f"/interactions/{interaction_id}")
        self.assertEqual(details.status_code, 200)
        self.assertEqual(details.json()["severity"], "minor")
        multi = self.client.post("/interactions/check-multiple", json={"drugs": ["Drug A", "Drug B", "Drug C"]})
        self.assertEqual(multi.status_code, 200)
        self.assertEqual(multi.json()["comparisons"], 3)
        search = self.client.get("/drugs/search", params={"q": "brand"})
        self.assertEqual(search.status_code, 200)
        self.assertEqual(search.json()[0]["id"], self.a.id)
        alternatives = self.client.get(f"/drugs/{self.a.id}/alternatives")
        self.assertEqual(alternatives.status_code, 422)
        alternatives = self.client.get(f"/drugs/{self.a.id}/alternatives", params={"pair_id": 1})
        self.assertEqual(alternatives.status_code, 200)
        self.assertEqual(alternatives.json()["alternatives"], [])

    def test_contextual_alternatives_include_drug_identity(self):
        repository = Repository(connect(self.path))
        try:
            repository.add_contract_interaction(
                pair_id=9001, definition_id="42", first=self.a.id, second=self.b.id,
                severity="Major", mechanism="Synergy", pair_key="MOCK-A|MOCK-B", detail_url="test",
            )
            repository.add_contextual_alternative(
                pair_id=9001, original_drug_id=self.a.id, side="A", atc_code="N06A",
                alternative_drug_id=self.d.id, source_url="test", scraped_at="now",
            )
            repository.connection.commit()
        finally:
            repository.connection.close()

        response = self.client.get(f"/drugs/{self.a.id}/alternatives", params={"pair_id": 9001})
        self.assertEqual(response.status_code, 200)
        alternative = response.json()["alternatives"][0]
        self.assertEqual(alternative["alternative_drug"], {
            "id": self.d.id,
            "canonical_name": "Drug D",
            "ddinter_id": "MOCK-D",
            "drugbank_id": None,
        })
        self.assertEqual(alternative["pair_id"], 9001)
        self.assertEqual(alternative["side"], "A")
        self.assertEqual(alternative["atc_code"], "N06A")

    def test_malformed_bodies(self):
        for body in ({}, {"drugs": "Drug A"}, {"drugs": []}, {"drugs": ["Drug A"]}, {"drugs": ["Drug A", " "]}, {"drugs": ["Drug A", 123]}, {"drugs": ["Drug A", None]}, {"drugs": ["Drug A"] * 51}, {"drugs": ["x" * 301, "Drug A"]}, {"drugs": ["Drug A", "Drug B"], "extra": True}):
            with self.subTest(body=body):
                self.assertEqual(self.client.post("/interactions/check-multiple", json=body).status_code, 422)
        self.assertEqual(self.client.post("/interactions/check-multiple", content="{", headers={"Content-Type": "application/json"}).status_code, 422)

    def test_malformed_queries_and_ids(self):
        for url in ("/drugs/search", "/drugs/search?q=", "/drugs/search?q=%20", "/drugs/search?q=a&limit=101", "/interactions/check?drug_a=Drug+A", "/interactions/check?drug_a=%20&drug_b=Drug+B", "/interactions/0", "/interactions/not-an-id", "/drugs/-1/alternatives"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 422)

    def test_unknown_missing_and_duplicate_drugs(self):
        for names, status, count in ((["Drug A", "Missing"], "unresolved_drugs", 0), (["Drug A", "Drug D"], "complete", 1), (["Drug A", "Mock Brand A"], "insufficient_distinct_drugs", 0)):
            response = self.client.post("/interactions/check-multiple", json={"drugs": names})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], status)
            self.assertEqual(response.json()["comparisons"], count)
        self.assertEqual(self.client.get("/interactions/99999").status_code, 404)
        self.assertEqual(self.client.get("/drugs/99999/alternatives", params={"pair_id": 1}).status_code, 404)
        self.assertEqual(self.client.get(f"/drugs/{self.d.id}/alternatives", params={"pair_id": 1}).json()["alternatives"], [])

    def test_unavailable_catalog_is_not_no_interaction(self):
        missing = Path(self.temp.name) / "absent.sqlite"
        with patch.dict(os.environ, {"DDINTER_DB_PATH": str(missing)}):
            response = self.client.get("/drugs/search?q=Drug")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"]["code"], "CATALOG_UNAVAILABLE")
        self.assertFalse(missing.exists())

    def test_existing_health_and_mock_extract(self):
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
        response = self.client.post("/extract", files={"images": ("mock.jpg", b"test bytes", "image/jpeg")})
        self.assertEqual(response.status_code, 200)
        self.assertIn("items", response.json())

    def test_empty_and_uninitialized_catalogs_are_distinct(self):
        path = Path(self.temp.name) / "empty.sqlite"
        connection = connect(path)
        connection.close()
        with patch.dict(os.environ, {"DDINTER_DB_PATH": str(path)}):
            self.assertEqual(self.client.get("/drugs/search?q=Drug").status_code, 503)
            connection = connect(path)
            initialize(connection)
            connection.close()
            response = self.client.post("/interactions/check-multiple", json={"drugs": ["Drug A", "Drug B"]})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "unresolved_drugs")
