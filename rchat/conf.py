import os


SECRET_KEY = os.environ.get("RCHAT_SECRET_KEY")
BASE_BACKEND_URL = os.environ.get("RCHAT_BASE_BACKEND_URL")

DB_USERNAME = os.environ.get("RCHAT_DB_USERNAME")
DB_PASSWORD = os.environ.get("RCHAT_DB_PASSWORD")
DB_NAME = os.environ.get("RCHAT_DB_NAME")
DB_HOST = os.environ.get("RCHAT_DB_HOST")

DATABASE_DSN = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
MIGRATIONS_DATABASE_DSN = (
    f"postgresql+asyncpg://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
)
SESSION_LIFETIME_MIN = os.environ.get("RCHAT_SESSION_LIFETIME_MIN")
