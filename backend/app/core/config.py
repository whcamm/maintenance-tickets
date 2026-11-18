import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote, urlparse

BACKEND_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    user: str
    password: str
    name: str


@dataclass(frozen=True)
class Settings:
    database: DatabaseSettings
    cors_origins: list[str]
    db_scripts_dir: Path
    frontend_dist_dir: Path
    maintenance_team_email: str


def parse_database_url(url: str) -> DatabaseSettings:
    parsed = urlparse(url)
    if parsed.scheme not in {"mysql", "mysql+pymysql"}:
        raise ValueError("DATABASE_URL must use the mysql:// scheme.")
    if not parsed.hostname or not parsed.path.strip("/"):
        raise ValueError("DATABASE_URL must include a host and a database name.")
    return DatabaseSettings(
        host=parsed.hostname,
        port=parsed.port or 3306,
        user=unquote(parsed.username or ""),
        password=unquote(parsed.password or ""),
        name=parsed.path.strip("/"),
    )


@lru_cache
def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL") or os.getenv("MYSQL_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set.")

    cors_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]

    return Settings(
        database=parse_database_url(database_url),
        cors_origins=cors_origins,
        db_scripts_dir=Path(os.getenv("DB_SCRIPTS_DIR", BACKEND_DIR.parent / "db")),
        frontend_dist_dir=Path(os.getenv("FRONTEND_DIST_DIR", BACKEND_DIR.parent / "frontend" / "dist")),
        maintenance_team_email=os.getenv("MAINTENANCE_TEAM_EMAIL", "maintenance-team@maintenance.local"),
    )
