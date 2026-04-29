"""App-level tests: frontend serving, health endpoints, and the test-only reset API."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


def _write_frontend_dist(dist_dir: Path) -> Path:
  dist_dir.mkdir(parents=True)
  (dist_dir / "index.html").write_text(
    """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Kanban Studio</title>
    <script src="/_next/static/chunks/app.js" defer></script>
  </head>
  <body>
    <h1>Kanban Studio</h1>
  </body>
</html>""",
    encoding="utf-8",
  )
  asset_dir = dist_dir / "_next" / "static" / "chunks"
  asset_dir.mkdir(parents=True)
  (asset_dir / "app.js").write_text("console.log('frontend asset');", encoding="utf-8")
  return dist_dir


def test_root_serves_exported_frontend(tmp_path: Path) -> None:
  client = TestClient(
    create_app(_write_frontend_dist(tmp_path / "out"), db_path=tmp_path / "db.sqlite3")
  )
  response = client.get("/")

  assert response.status_code == 200
  assert response.headers["content-type"].startswith("text/html")
  assert "Kanban Studio" in response.text
  assert "/_next/static/chunks/app.js" in response.text


def test_frontend_static_assets_are_served(tmp_path: Path) -> None:
  client = TestClient(
    create_app(_write_frontend_dist(tmp_path / "out"), db_path=tmp_path / "db.sqlite3")
  )
  response = client.get("/_next/static/chunks/app.js")

  assert response.status_code == 200
  assert response.text == "console.log('frontend asset');"


def test_missing_frontend_build_returns_clear_error(client: TestClient) -> None:
  response = client.get("/")

  assert response.status_code == 503
  assert "Frontend build not found" in response.text


def test_health_route_reports_ok(client: TestClient) -> None:
  response = client.get("/api/health")

  assert response.status_code == 200
  assert response.json() == {"status": "ok"}


def test_hello_route_returns_example_message(client: TestClient) -> None:
  response = client.get("/api/hello")

  assert response.status_code == 200
  assert response.json() == {"message": "Hello from FastAPI."}


def test_test_reset_board_route_is_disabled_by_default(client: TestClient) -> None:
  response = client.post("/api/test/reset-board")

  assert response.status_code == 404


def test_test_reset_board_route_restores_seed_data_when_enabled(
  make_authenticated_client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
  db_path = tmp_path / "data" / "db.sqlite3"
  monkeypatch.setenv("ENABLE_TEST_API", "1")
  client = make_authenticated_client(db_path=db_path)

  renamed = client.patch("/api/board/columns/col-backlog", json={"title": "Ideas"})
  assert renamed.status_code == 200
  assert renamed.json()["columns"][0]["title"] == "Ideas"

  reset = client.post("/api/test/reset-board")
  assert reset.status_code == 200
  assert reset.json()["columns"][0]["title"] == "Backlog"
