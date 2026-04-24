from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app


def write_frontend_dist(dist_dir: Path) -> Path:
  dist_dir.mkdir(parents=True)
  (dist_dir / "index.html").write_text(
    """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <title>Kanban Studio</title>
        <script src="/_next/static/chunks/app.js" defer></script>
      </head>
      <body>
        <h1>Kanban Studio</h1>
      </body>
    </html>
    """.strip(),
    encoding="utf-8",
  )
  asset_dir = dist_dir / "_next" / "static" / "chunks"
  asset_dir.mkdir(parents=True)
  (asset_dir / "app.js").write_text("console.log('frontend asset');", encoding="utf-8")
  return dist_dir


def create_client(tmp_path: Path, db_path: Path | None = None) -> TestClient:
  return TestClient(create_app(tmp_path / "missing", db_path=db_path))


def create_authenticated_client(
  tmp_path: Path,
  db_path: Path | None = None,
) -> TestClient:
  client = create_client(tmp_path, db_path)
  response = client.post(
    "/api/auth/login",
    json={"username": "user", "password": "password"},
  )
  assert response.status_code == 200
  return client


def test_root_serves_exported_frontend(tmp_path: Path) -> None:
  client = TestClient(create_app(write_frontend_dist(tmp_path / "out"), db_path=tmp_path / "db.sqlite3"))
  response = client.get("/")

  assert response.status_code == 200
  assert response.headers["content-type"].startswith("text/html")
  assert "Kanban Studio" in response.text
  assert "/_next/static/chunks/app.js" in response.text


def test_frontend_static_assets_are_served(tmp_path: Path) -> None:
  client = TestClient(create_app(write_frontend_dist(tmp_path / "out"), db_path=tmp_path / "db.sqlite3"))
  response = client.get("/_next/static/chunks/app.js")

  assert response.status_code == 200
  assert response.text == "console.log('frontend asset');"


def test_missing_frontend_build_returns_clear_error(tmp_path: Path) -> None:
  client = create_client(tmp_path)
  response = client.get("/")

  assert response.status_code == 503
  assert "Frontend build not found" in response.text


def test_session_requires_login(tmp_path: Path) -> None:
  client = create_client(tmp_path)
  response = client.get("/api/auth/session")

  assert response.status_code == 401
  assert response.json() == {"detail": "Not authenticated"}


def test_login_rejects_invalid_credentials(tmp_path: Path) -> None:
  client = create_client(tmp_path)
  response = client.post(
    "/api/auth/login",
    json={"username": "user", "password": "wrong"},
  )

  assert response.status_code == 401
  assert response.json() == {"detail": "Invalid credentials"}


def test_login_sets_persistent_session_cookie(tmp_path: Path) -> None:
  client = create_client(tmp_path)
  response = client.post(
    "/api/auth/login",
    json={"username": "user", "password": "password"},
  )

  assert response.status_code == 200
  assert response.json() == {"username": "user"}
  assert response.cookies.get("pm_session")
  assert "httponly" in response.headers["set-cookie"].lower()

  session_response = client.get("/api/auth/session")
  assert session_response.status_code == 200
  assert session_response.json() == {"username": "user"}


def test_logout_clears_session(tmp_path: Path) -> None:
  client = create_client(tmp_path)
  client.post(
    "/api/auth/login",
    json={"username": "user", "password": "password"},
  )

  logout_response = client.post("/api/auth/logout")
  assert logout_response.status_code == 204

  session_response = client.get("/api/auth/session")
  assert session_response.status_code == 401


def test_session_cookie_survives_app_restart(tmp_path: Path) -> None:
  db_path = tmp_path / "data" / "db.sqlite3"
  login_client = create_client(tmp_path, db_path)
  login_response = login_client.post(
    "/api/auth/login",
    json={"username": "user", "password": "password"},
  )

  session_cookie = login_response.cookies.get("pm_session")
  assert session_cookie is not None

  restarted_client = create_client(tmp_path, db_path)
  restarted_client.cookies.set("pm_session", session_cookie)

  session_response = restarted_client.get("/api/auth/session")
  assert session_response.status_code == 200
  assert session_response.json() == {"username": "user"}


def test_health_route_reports_ok(tmp_path: Path) -> None:
  client = create_client(tmp_path, tmp_path / "db.sqlite3")
  response = client.get("/api/health")

  assert response.status_code == 200
  assert response.json() == {"status": "ok"}


def test_hello_route_returns_example_message(tmp_path: Path) -> None:
  client = create_client(tmp_path, tmp_path / "db.sqlite3")
  response = client.get("/api/hello")

  assert response.status_code == 200
  assert response.json() == {"message": "Hello from FastAPI."}


def test_board_route_requires_login(tmp_path: Path) -> None:
  client = create_client(tmp_path)
  response = client.get("/api/board")

  assert response.status_code == 401
  assert response.json() == {"detail": "Not authenticated"}


def test_board_fetch_creates_database_and_returns_seed_data(tmp_path: Path) -> None:
  db_path = tmp_path / "data" / "db.sqlite3"
  client = create_authenticated_client(tmp_path, db_path)

  response = client.get("/api/board")

  assert response.status_code == 200
  assert db_path.exists()
  payload = response.json()
  assert [column["id"] for column in payload["columns"]] == [
    "col-backlog",
    "col-discovery",
    "col-progress",
    "col-review",
    "col-done",
  ]
  assert payload["columns"][0]["cardIds"] == ["card-1", "card-2"]
  assert payload["cards"]["card-1"]["title"] == "Align roadmap themes"


def test_rename_column_persists_after_restart(tmp_path: Path) -> None:
  db_path = tmp_path / "data" / "db.sqlite3"
  client = create_authenticated_client(tmp_path, db_path)

  response = client.patch(
    "/api/board/columns/col-backlog",
    json={"title": "Ideas"},
  )

  assert response.status_code == 200
  payload = response.json()
  assert payload["columns"][0]["title"] == "Ideas"

  restarted_client = create_authenticated_client(tmp_path, db_path)
  persisted = restarted_client.get("/api/board")
  assert persisted.status_code == 200
  assert persisted.json()["columns"][0]["title"] == "Ideas"


def test_add_edit_and_delete_card_round_trip(tmp_path: Path) -> None:
  client = create_authenticated_client(tmp_path, tmp_path / "db.sqlite3")

  created = client.post(
    "/api/board/columns/col-backlog/cards",
    json={"title": "New backend card", "details": "Stored in sqlite."},
  )
  assert created.status_code == 200
  created_payload = created.json()
  created_card_id = created_payload["columns"][0]["cardIds"][-1]
  assert created_payload["cards"][created_card_id]["title"] == "New backend card"

  updated = client.patch(
    f"/api/board/cards/{created_card_id}",
    json={"title": "Updated backend card", "details": "Edited details."},
  )
  assert updated.status_code == 200
  updated_payload = updated.json()
  assert updated_payload["cards"][created_card_id] == {
    "id": created_card_id,
    "title": "Updated backend card",
    "details": "Edited details.",
  }

  deleted = client.delete(
    f"/api/board/columns/col-backlog/cards/{created_card_id}"
  )
  assert deleted.status_code == 200
  deleted_payload = deleted.json()
  assert created_card_id not in deleted_payload["cards"]
  assert created_card_id not in deleted_payload["columns"][0]["cardIds"]


def test_move_card_updates_column_and_order_and_persists(tmp_path: Path) -> None:
  db_path = tmp_path / "data" / "db.sqlite3"
  client = create_authenticated_client(tmp_path, db_path)

  moved = client.patch(
    "/api/board/cards/card-1/move",
    json={"column_id": "col-review", "position": 1},
  )
  assert moved.status_code == 200
  moved_payload = moved.json()
  review_column = next(
    column for column in moved_payload["columns"] if column["id"] == "col-review"
  )
  backlog_column = next(
    column for column in moved_payload["columns"] if column["id"] == "col-backlog"
  )
  assert review_column["cardIds"] == ["card-6", "card-1"]
  assert backlog_column["cardIds"] == ["card-2"]

  restarted_client = create_authenticated_client(tmp_path, db_path)
  persisted = restarted_client.get("/api/board")
  assert persisted.status_code == 200
  persisted_review = next(
    column for column in persisted.json()["columns"] if column["id"] == "col-review"
  )
  assert persisted_review["cardIds"] == ["card-6", "card-1"]


def test_board_routes_return_not_found_and_validation_errors(tmp_path: Path) -> None:
  client = create_authenticated_client(tmp_path, tmp_path / "db.sqlite3")

  missing_column = client.patch(
    "/api/board/columns/col-missing",
    json={"title": "Nope"},
  )
  assert missing_column.status_code == 404
  assert missing_column.json() == {"detail": "Column not found"}

  bad_title = client.post(
    "/api/board/columns/col-backlog/cards",
    json={"title": "   ", "details": "Ignored"},
  )
  assert bad_title.status_code == 400
  assert bad_title.json() == {"detail": "Card title is required"}

  bad_move = client.patch(
    "/api/board/cards/card-1/move",
    json={"column_id": "col-review", "position": 99},
  )
  assert bad_move.status_code == 400
  assert bad_move.json() == {"detail": "Position is out of range"}


def test_update_card_requires_non_empty_title(tmp_path: Path) -> None:
  client = create_authenticated_client(tmp_path, tmp_path / "db.sqlite3")

  response = client.patch(
    "/api/board/cards/card-1",
    json={"title": "   ", "details": "Still here."},
  )

  assert response.status_code == 400
  assert response.json() == {"detail": "Card title is required"}


def test_test_reset_board_route_is_disabled_by_default(tmp_path: Path) -> None:
  client = create_client(tmp_path, tmp_path / "db.sqlite3")

  response = client.post("/api/test/reset-board")

  assert response.status_code == 404


def test_test_reset_board_route_restores_seed_data_when_enabled(tmp_path: Path, monkeypatch) -> None:
  db_path = tmp_path / "data" / "db.sqlite3"
  monkeypatch.setenv("ENABLE_TEST_API", "1")
  client = create_authenticated_client(tmp_path, db_path)

  renamed = client.patch(
    "/api/board/columns/col-backlog",
    json={"title": "Ideas"},
  )
  assert renamed.status_code == 200
  assert renamed.json()["columns"][0]["title"] == "Ideas"

  reset = client.post("/api/test/reset-board")
  assert reset.status_code == 200
  assert reset.json()["columns"][0]["title"] == "Backlog"