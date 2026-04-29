from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STATIC_DIR = PACKAGE_DIR.parent / "static"
DB_DIR = PROJECT_ROOT / "var"

DEFAULT_CSV_PATH = DATA_DIR / "customers.csv"
DEFAULT_DB_PATH = DB_DIR / "customers.db"
