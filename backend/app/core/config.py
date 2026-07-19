"""Runtime configuration loaded from .env (local, single-PC deployment)."""
import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/vds_db",
    )
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    data_dir: str = os.getenv("DATA_DIR", "./data")
    cors_origins: list[str] = [
        o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()
    ]

    @property
    def upload_dir(self) -> str:
        return os.path.join(self.data_dir, "uploads")

    @property
    def certificate_dir(self) -> str:
        return os.path.join(self.data_dir, "certificates")


@lru_cache
def get_settings() -> "Settings":
    s = Settings()
    os.makedirs(s.upload_dir, exist_ok=True)
    os.makedirs(s.certificate_dir, exist_ok=True)
    return s
