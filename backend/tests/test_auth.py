from pathlib import Path

from fastapi.testclient import TestClient


def test_session_requires_login(client: TestClient) -> None:
  response = client.get("/api/auth/session")

  assert response.status_code == 401
  assert response.json() == {"detail": "Not authenticated"}


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
  response = client.post(
    "/api/auth/login",
    json={"username": "user", "password": "wrong"},
  )

  assert response.status_code == 401
  assert response.json() == {"detail": "Invalid credentials"}


def test_login_sets_persistent_session_cookie(client: TestClient) -> None:
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


def test_logout_clears_session(client: TestClient) -> None:
  client.post("/api/auth/login", json={"username": "user", "password": "password"})

  logout_response = client.post("/api/auth/logout")
  assert logout_response.status_code == 204

  session_response = client.get("/api/auth/session")
  assert session_response.status_code == 401


def test_session_cookie_survives_app_restart(make_client, tmp_path: Path) -> None:
  db_path = tmp_path / "data" / "db.sqlite3"
  login_client = make_client(db_path=db_path)
  login_response = login_client.post(
    "/api/auth/login",
    json={"username": "user", "password": "password"},
  )

  session_cookie = login_response.cookies.get("pm_session")
  assert session_cookie is not None

  restarted_client = make_client(db_path=db_path)
  restarted_client.cookies.set("pm_session", session_cookie)

  session_response = restarted_client.get("/api/auth/session")
  assert session_response.status_code == 200
  assert session_response.json() == {"username": "user"}
