from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import parse_qs

from customer_directory.api.common import respond_json
from customer_directory.db.database import fetch_customer_by_id, fetch_customers


def handle_customers_api(environ: dict, start_response: Callable, db_path: Path) -> Iterable[bytes]:
    """Return a paginated customer list with optional free-text search."""

    params = parse_qs(environ.get("QUERY_STRING", ""), keep_blank_values=False)
    search = params.get("search", [""])[0].strip()

    try:
        page = parse_positive_int(params.get("page", ["1"])[0], "page")
        page_size = parse_positive_int(params.get("page_size", ["20"])[0], "page_size")
    except ValueError as error:
        return respond_json(start_response, "400 Bad Request", {"error": str(error)})

    if page_size > 100:
        return respond_json(
            start_response,
            "400 Bad Request",
            {"error": "page_size must be less than or equal to 100."},
        )

    customers, total = fetch_customers(db_path, page, page_size, search=search)
    total_pages = (total + page_size - 1) // page_size if total else 0

    return respond_json(
        start_response,
        "200 OK",
        {
            "data": customers,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "search": search,
                "total": total,
                "total_pages": total_pages,
            },
        },
    )


def handle_customer_detail_api(path: str, start_response: Callable, db_path: Path) -> Iterable[bytes]:
    """Return a single customer record looked up by id from the request path."""

    raw_customer_id = path.removeprefix("/api/customers/")

    try:
        customer_id = parse_positive_int(raw_customer_id, "customer_id")
    except ValueError as error:
        return respond_json(start_response, "400 Bad Request", {"error": str(error)})

    customer = fetch_customer_by_id(db_path, customer_id)
    if customer is None:
        return respond_json(start_response, "404 Not Found", {"error": "Customer not found."})

    return respond_json(start_response, "200 OK", {"data": customer})


def parse_positive_int(raw_value: str, field_name: str) -> int:
    """Parse and validate positive integer query/path parameters."""

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an integer.") from exc

    if value < 1:
        raise ValueError(f"{field_name} must be greater than or equal to 1.")

    return value

