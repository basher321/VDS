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

    # Object storage for uploaded/generated files (issuer seal/logo/signature images,
    # certificate PDFs). If unset, files are read/written on local disk under data_dir --
    # fine for a normal server but WRONG on serverless hosts (e.g. Vercel) where local disk
    # doesn't persist between requests. Set these three to use Supabase Storage instead.
    supabase_url: str | None = os.getenv("SUPABASE_URL")
    supabase_service_key: str | None = os.getenv("SUPABASE_SERVICE_KEY")
    supabase_bucket: str = os.getenv("SUPABASE_STORAGE_BUCKET", "vds-files")

    @property
    def using_object_storage(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_key)


@lru_cache
def get_settings() -> "Settings":
    return Settings()
