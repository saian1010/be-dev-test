from __future__ import annotations

import argparse
from pathlib import Path

from customer_directory.config.config import DEFAULT_CSV_PATH, DEFAULT_DB_PATH
from customer_directory.db.database import import_customers


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import customers from CSV into SQLite.")
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=DEFAULT_CSV_PATH,
        help=f"Path to the source CSV file. Default: {DEFAULT_CSV_PATH}",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to the SQLite database file. Default: {DEFAULT_DB_PATH}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    imported = import_customers(args.csv_path, args.db_path)
    print(f"Imported {imported} customers into {args.db_path}")


if __name__ == "__main__":
    main()
