from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app


client = TestClient(app)


def test_root_serves_html_scaffold() -> None:
  response = client.get("/")

  assert response.status_code == 200
  assert response.headers["content-type"].startswith("text/html")
  assert "Hello from the Project Management MVP" in response.text
  assert 'fetch("/api/hello")' in response.text


def test_health_route_reports_ok() -> None:
  response = client.get("/api/health")

  assert response.status_code == 200
  assert response.json() == {"status": "ok"}


def test_hello_route_returns_example_message() -> None:
  response = client.get("/api/hello")

  assert response.status_code == 200
  assert response.json() == {"message": "Hello from FastAPI."}