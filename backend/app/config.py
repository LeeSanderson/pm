import os
import warnings
from pathlib import Path

DEFAULT_FRONTEND_DIST_DIR = Path(__file__).resolve().parents[2] / "frontend" / "out"
DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "db.sqlite3"
DEFAULT_SESSION_SECRET = "pm-mvp-dev-session-secret"

AUTH_USERNAME = "user"
AUTH_PASSWORD = "password"
SESSION_COOKIE_NAME = "pm_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 30
CHAT_SESSION_KEY = "chat_session_id"


def resolve_frontend_dist_dir(frontend_dist_dir: Path | None = None) -> Path:
  if frontend_dist_dir is not None:
    return frontend_dist_dir
  configured_dir = os.environ.get("FRONTEND_DIST_DIR")
  if configured_dir:
    return Path(configured_dir)
  return DEFAULT_FRONTEND_DIST_DIR


def resolve_session_secret() -> str:
  secret = os.environ.get("SESSION_SECRET")
  if not secret:
    warnings.warn(
      "SESSION_SECRET is not set — using the default dev secret. Set SESSION_SECRET before deploying.",
      stacklevel=2,
    )
    return DEFAULT_SESSION_SECRET
  return secret


def resolve_db_path(db_path: Path | None = None) -> Path:
  if db_path is not None:
    return db_path
  configured_path = os.environ.get("DB_PATH")
  if configured_path:
    return Path(configured_path)
  return DEFAULT_DB_PATH


def is_test_api_enabled() -> bool:
  return os.environ.get("ENABLE_TEST_API") == "1"
