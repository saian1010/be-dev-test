from __future__ import annotations

import csv
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL,
    gender TEXT,
    ip_address TEXT,
    company TEXT,
    city TEXT,
    title TEXT,
    website TEXT
);

CREATE INDEX IF NOT EXISTS idx_customers_last_name
ON customers (last_name);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA_SQL)
    connection.commit()


def import_customers(csv_path: Path, db_path: Path) -> int:
    """Replace the current dataset with the contents of the source CSV file."""

    with closing(connect(db_path)) as connection:
        create_schema(connection)
        rows = list(_read_customers(csv_path))

        with connection:
            connection.execute("DELETE FROM customers")
            connection.executemany(
                """
                INSERT INTO customers (
                    id,
                    first_name,
                    last_name,
                    email,
                    gender,
                    ip_address,
                    company,
                    city,
                    title,
                    website
                )
                VALUES (
                    :id,
                    :first_name,
                    :last_name,
                    :email,
                    :gender,
                    :ip_address,
                    :company,
                    :city,
                    :title,
                    :website
                )
                """,
                rows,
            )

    return len(rows)


def fetch_customers(
    db_path: Path,
    page: int,
    page_size: int,
    search: str = "",
) -> tuple[list[dict[str, Any]], int]:
    """Fetch one page of customers plus the total count for pagination."""

    offset = (page - 1) * page_size
    where_clause = ""
    parameters: list[Any] = []

    if search:
        # Escape wildcard characters so user input is treated as plain text inside
        # LIKE expressions instead of broadening the search unexpectedly.
        search_pattern = f"%{_escape_like(search)}%"
        where_clause = """
            WHERE
                first_name LIKE ? ESCAPE '\\'
                OR last_name LIKE ? ESCAPE '\\'
                OR email LIKE ? ESCAPE '\\'
                OR gender LIKE ? ESCAPE '\\'
                OR company LIKE ? ESCAPE '\\'
                OR city LIKE ? ESCAPE '\\'
                OR title LIKE ? ESCAPE '\\'
        """
        parameters = [search_pattern] * 7

    with closing(connect(db_path)) as connection:
        create_schema(connection)
        total = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM customers
            {where_clause}
            """,
            parameters,
        ).fetchone()[0]
        results = connection.execute(
            f"""
            SELECT
                id,
                first_name,
                last_name,
                email,
                gender,
                ip_address,
                company,
                city,
                title,
                website
            FROM customers
            {where_clause}
            ORDER BY id
            LIMIT ? OFFSET ?
            """,
            [*parameters, page_size, offset],
        ).fetchall()

    return [dict(row) for row in results], int(total)


def fetch_customer_by_id(db_path: Path, customer_id: int) -> dict[str, Any] | None:
    """Fetch a single customer by primary key."""

    with closing(connect(db_path)) as connection:
        create_schema(connection)
        result = connection.execute(
            """
            SELECT
                id,
                first_name,
                last_name,
                email,
                gender,
                ip_address,
                company,
                city,
                title,
                website
            FROM customers
            WHERE id = ?
            """,
            (customer_id,),
        ).fetchone()

    return dict(result) if result is not None else None


def _read_customers(csv_path: Path) -> list[dict[str, Any]]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        customers: list[dict[str, Any]] = []

        for row in reader:
            customers.append(
                {
                    "id": int(row["id"]),
                    "first_name": row["first_name"].strip(),
                    "last_name": row["last_name"].strip(),
                    "email": row["email"].strip(),
                    "gender": _nullable_text(row["gender"]),
                    "ip_address": _nullable_text(row["ip_address"]),
                    "company": _nullable_text(row["company"]),
                    "city": _nullable_text(row["city"]),
                    "title": _nullable_text(row["title"]),
                    "website": _nullable_text(row["website"]),
                }
            )

    return customers


def _nullable_text(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None


def _escape_like(value: str) -> str:
    """Escape SQL LIKE wildcards while preserving parameterized queries."""

    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
