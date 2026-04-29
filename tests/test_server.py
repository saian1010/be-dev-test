from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from wsgiref.util import setup_testing_defaults

from customer_directory.config import DEFAULT_CSV_PATH
from customer_directory.database import import_customers
from customer_directory.server import create_app


class ServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "customers.db"
        import_customers(DEFAULT_CSV_PATH, self.db_path)
        self.app = create_app(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_customers_endpoint_returns_paginated_results(self) -> None:
        status, headers, body = self.call_app("/api/customers?page=2&page_size=15")

        payload = json.loads(body.decode("utf-8"))

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
        self.assertEqual(len(payload["data"]), 15)
        self.assertEqual(payload["pagination"]["page"], 2)
        self.assertEqual(payload["pagination"]["page_size"], 15)
        self.assertEqual(payload["pagination"]["total"], 1000)
        self.assertEqual(payload["data"][0]["id"], 16)

    def test_customers_endpoint_rejects_invalid_page_size(self) -> None:
        status, _, body = self.call_app("/api/customers?page=1&page_size=101")

        payload = json.loads(body.decode("utf-8"))

        self.assertEqual(status, "400 Bad Request")
        self.assertIn("page_size", payload["error"])

    def test_customers_endpoint_filters_by_search_across_fields(self) -> None:
        status, headers, body = self.call_app("/api/customers?page=1&page_size=20&search=Meezzy")

        payload = json.loads(body.decode("utf-8"))

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
        self.assertEqual(payload["pagination"]["search"], "Meezzy")
        self.assertGreaterEqual(payload["pagination"]["total"], 1)
        self.assertTrue(any(row["company"] == "Meezzy" for row in payload["data"]))

    def test_customer_detail_endpoint_returns_full_customer(self) -> None:
        status, headers, body = self.call_app("/api/customers/1")

        payload = json.loads(body.decode("utf-8"))

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
        self.assertEqual(payload["data"]["id"], 1)
        self.assertEqual(payload["data"]["first_name"], "Laura")
        self.assertIn("gender", payload["data"])
        self.assertIn("website", payload["data"])

    def test_customer_detail_endpoint_returns_404_when_missing(self) -> None:
        status, _, body = self.call_app("/api/customers/9999")

        payload = json.loads(body.decode("utf-8"))

        self.assertEqual(status, "404 Not Found")
        self.assertEqual(payload["error"], "Customer not found.")

    def test_root_serves_html(self) -> None:
        status, headers, body = self.call_app("/")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn(b"Customer Directory", body)

    def test_customer_detail_page_serves_html(self) -> None:
        status, headers, body = self.call_app("/customers/1")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn(b"Customer Details", body)

    def call_app(self, path: str) -> tuple[str, dict[str, str], bytes]:
        environ: dict[str, object] = {}
        setup_testing_defaults(environ)
        environ["REQUEST_METHOD"] = "GET"

        if "?" in path:
            path_info, query_string = path.split("?", 1)
        else:
            path_info, query_string = path, ""

        environ["PATH_INFO"] = path_info
        environ["QUERY_STRING"] = query_string
        environ["wsgi.input"] = io.BytesIO(b"")

        captured: dict[str, object] = {}

        def start_response(status: str, headers: list[tuple[str, str]]) -> None:
            captured["status"] = status
            captured["headers"] = dict(headers)

        chunks = self.app(environ, start_response)
        try:
            body = b"".join(chunks)
        finally:
            close = getattr(chunks, "close", None)
            if callable(close):
                close()

        return captured["status"], captured["headers"], body


if __name__ == "__main__":
    unittest.main()
