from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from customer_directory.config import DEFAULT_CSV_PATH
from customer_directory.database import import_customers


class ImportCustomersTests(unittest.TestCase):
    def test_imports_expected_number_of_rows_and_nulls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "customers.db"

            imported = import_customers(DEFAULT_CSV_PATH, db_path)

            self.assertEqual(imported, 1000)

            with closing(sqlite3.connect(db_path)) as connection:
                count = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
                row = connection.execute(
                    "SELECT title, website FROM customers WHERE id = ?",
                    (6,),
                ).fetchone()

            self.assertEqual(count, 1000)
            self.assertEqual(row[0], None)
            self.assertEqual(row[1], None)


if __name__ == "__main__":
    unittest.main()
