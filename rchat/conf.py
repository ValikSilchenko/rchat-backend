import os

ENVIRONMENT = os.environ["RCHAT_ENVIRONMENT"]

SECRET_KEY = os.environ["RCHAT_SECRET_KEY"]
BASE_BACKEND_URL = os.environ["RCHAT_BASE_BACKEND_URL"]

DB_USERNAME = os.environ["RCHAT_DB_USERNAME"]
DB_PASSWORD = os.environ["RCHAT_DB_PASSWORD"]
DB_NAME = os.environ["RCHAT_DB_NAME"]
DB_HOST = os.environ["RCHAT_DB_HOST"]

DATABASE_DSN = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
MIGRATIONS_PATH = os.path.join("rchat", "migrations")

SESSION_LIFETIME_MIN = int(os.environ.get("RCHAT_SESSION_LIFETIME_MIN"))
REFRESH_LIFETIME_DAYS = int(os.environ.get("RCHAT_REFRESH_LIFETIME_DAYS"))

STORAGE_DIR = os.environ.get("RCHAT_STORAGE_DIR")
STORAGE_FOLDERS = ["files", "temp"]

RELOAD_ENABLED = bool(os.environ.get("RCHAT_RELOAD_ENABLED"))
