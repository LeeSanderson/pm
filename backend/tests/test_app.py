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


def test_root_serves_exported_frontend(tmp_path: Path) -> None:
  client = TestClient(create_app(write_frontend_dist(tmp_path / "out")))
  response = client.get("/")

  assert response.status_code == 200
  assert response.headers["content-type"].startswith("text/html")
  assert "Kanban Studio" in response.text
  assert "/_next/static/chunks/app.js" in response.text


def test_frontend_static_assets_are_served(tmp_path: Path) -> None:
  client = TestClient(create_app(write_frontend_dist(tmp_path / "out")))
  response = client.get("/_next/static/chunks/app.js")

  assert response.status_code == 200
  assert response.text == "console.log('frontend asset');"


def test_missing_frontend_build_returns_clear_error(tmp_path: Path) -> None:
  client = TestClient(create_app(tmp_path / "missing"))
  response = client.get("/")

  assert response.status_code == 503
  assert "Frontend build not found" in response.text


def test_session_requires_login(tmp_path: Path) -> None:
  client = TestClient(create_app(tmp_path / "missing"))
  response = client.get("/api/auth/session")

  assert response.status_code == 401
  assert response.json() == {"detail": "Not authenticated"}


def test_login_rejects_invalid_credentials(tmp_path: Path) -> None:
  client = TestClient(create_app(tmp_path / "missing"))
  response = client.post(
    "/api/auth/login",
    json={"username": "user", "password": "wrong"},
  )

  assert response.status_code == 401
  assert response.json() == {"detail": "Invalid credentials"}


def test_login_sets_persistent_session_cookie(tmp_path: Path) -> None:
  client = TestClient(create_app(tmp_path / "missing"))
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
  client = TestClient(create_app(tmp_path / "missing"))
  client.post(
    "/api/auth/login",
    json={"username": "user", "password": "password"},
  )

  logout_response = client.post("/api/auth/logout")
  assert logout_response.status_code == 204

  session_response = client.get("/api/auth/session")
  assert session_response.status_code == 401


def test_session_cookie_survives_app_restart(tmp_path: Path) -> None:
  dist_dir = tmp_path / "missing"
  login_client = TestClient(create_app(dist_dir))
  login_response = login_client.post(
    "/api/auth/login",
    json={"username": "user", "password": "password"},
  )

  session_cookie = login_response.cookies.get("pm_session")
  assert session_cookie is not None

  restarted_client = TestClient(create_app(dist_dir))
  restarted_client.cookies.set("pm_session", session_cookie)

  session_response = restarted_client.get("/api/auth/session")
  assert session_response.status_code == 200
  assert session_response.json() == {"username": "user"}


def test_health_route_reports_ok() -> None:
  client = TestClient(create_app())
  response = client.get("/api/health")

  assert response.status_code == 200
  assert response.json() == {"status": "ok"}


def test_hello_route_returns_example_message() -> None:
  client = TestClient(create_app())
  response = client.get("/api/hello")

  assert response.status_code == 200
  assert response.json() == {"message": "Hello from FastAPI."}