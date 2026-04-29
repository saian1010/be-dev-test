from __future__ import annotations

import argparse
import mimetypes
from pathlib import Path
from typing import Callable, Iterable
from wsgiref.simple_server import make_server
from wsgiref.util import FileWrapper

from customer_directory.config.config import DEFAULT_CSV_PATH, DEFAULT_DB_PATH, STATIC_DIR
from customer_directory.api.common import respond_json
from customer_directory.api.customers import handle_customer_detail_api, handle_customers_api
from customer_directory.db.database import fetch_customers
from customer_directory.utils.import_csv import import_customers

WSGIApplication = Callable[[dict, Callable], Iterable[bytes]]


def create_app(db_path: Path = DEFAULT_DB_PATH, static_dir: Path = STATIC_DIR) -> WSGIApplication:
    """Build the WSGI application that serves both JSON APIs and static pages."""

    def app(environ: dict, start_response: Callable) -> Iterable[bytes]:
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")

        if method != "GET":
            return respond_json(start_response, "405 Method Not Allowed", {"error": "Only GET is supported."})

        if path == "/health":
            return respond_json(start_response, "200 OK", {"status": "ok"})

        if path == "/api/customers":
            return handle_customers_api(environ, start_response, db_path)

        if path.startswith("/api/customers/"):
            return handle_customer_detail_api(path, start_response, db_path)

        if path == "/":
            return respond_file(start_response, static_dir / "pages/index.html", static_dir)

        if path.startswith("/customers/"):
            return respond_file(start_response, static_dir / "pages/customer.html", static_dir)

        if path.startswith("/static/"):
            relative_path = path.removeprefix("/static/")
            return respond_file(start_response, static_dir / relative_path, static_dir)

        return respond_json(start_response, "404 Not Found", {"error": "Resource not found."})

    return app


def respond_file(start_response: Callable, path: Path, allowed_root: Path) -> Iterable[bytes]:
    """Serve a static file while keeping responses inside the configured static root."""

    resolved = path.resolve()
    static_root = allowed_root.resolve()

    # Resolve and compare against the allowed root so crafted paths cannot escape
    # the static directory via ../ segments or symlinks.
    if static_root not in resolved.parents and resolved != static_root / "pages/index.html":
        return respond_json(start_response, "403 Forbidden", {"error": "Forbidden."})

    if not path.is_file():
        return respond_json(start_response, "404 Not Found", {"error": "Resource not found."})

    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    headers = [
        ("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith("text/") else content_type),
        ("Content-Length", str(path.stat().st_size)),
    ]
    start_response("200 OK", headers)
    return FileWrapper(path.open("rb"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the customer directory web server.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to.")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on.")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to the SQLite database file. Default: {DEFAULT_DB_PATH}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_data_loaded(args.db_path)
    app = create_app(db_path=args.db_path)

    with make_server(args.host, args.port, app) as server:
        print(f"Serving on http://{args.host}:{args.port}")
        server.serve_forever()


def ensure_data_loaded(db_path: Path) -> None:
    """Import the CSV on first run so the app is usable without a manual setup step."""

    if db_path.exists() and db_path.stat().st_size > 0:
        try:
            _, total = fetch_customers(db_path, 1, 1)
        except Exception:
            total = 0
        if total > 0:
            return

    import_customers(DEFAULT_CSV_PATH, db_path)


if __name__ == "__main__":
    main()
