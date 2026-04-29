from pathlib import Path

from fastapi.testclient import TestClient


def test_board_route_requires_login(client: TestClient) -> None:
  response = client.get("/api/board")

  assert response.status_code == 401
  assert response.json() == {"detail": "Not authenticated"}


def test_board_fetch_creates_database_and_returns_seed_data(
  make_authenticated_client, tmp_path: Path
) -> None:
  db_path = tmp_path / "data" / "db.sqlite3"
  client = make_authenticated_client(db_path=db_path)

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


def test_rename_column_persists_after_restart(
  make_authenticated_client, tmp_path: Path
) -> None:
  db_path = tmp_path / "data" / "db.sqlite3"
  client = make_authenticated_client(db_path=db_path)

  response = client.patch("/api/board/columns/col-backlog", json={"title": "Ideas"})

  assert response.status_code == 200
  assert response.json()["columns"][0]["title"] == "Ideas"

  restarted_client = make_authenticated_client(db_path=db_path)
  persisted = restarted_client.get("/api/board")
  assert persisted.status_code == 200
  assert persisted.json()["columns"][0]["title"] == "Ideas"


def test_add_edit_and_delete_card_round_trip(auth_client: TestClient) -> None:
  created = auth_client.post(
    "/api/board/columns/col-backlog/cards",
    json={"title": "New backend card", "details": "Stored in sqlite."},
  )
  assert created.status_code == 200
  created_payload = created.json()
  created_card_id = created_payload["columns"][0]["cardIds"][-1]
  assert created_payload["cards"][created_card_id]["title"] == "New backend card"

  updated = auth_client.patch(
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

  deleted = auth_client.delete(f"/api/board/columns/col-backlog/cards/{created_card_id}")
  assert deleted.status_code == 200
  deleted_payload = deleted.json()
  assert created_card_id not in deleted_payload["cards"]
  assert created_card_id not in deleted_payload["columns"][0]["cardIds"]


def test_move_card_updates_column_and_order_and_persists(
  make_authenticated_client, tmp_path: Path
) -> None:
  db_path = tmp_path / "data" / "db.sqlite3"
  client = make_authenticated_client(db_path=db_path)

  moved = client.patch(
    "/api/board/cards/card-1/move",
    json={"column_id": "col-review", "position": 1},
  )
  assert moved.status_code == 200
  moved_payload = moved.json()
  review_column = next(col for col in moved_payload["columns"] if col["id"] == "col-review")
  backlog_column = next(col for col in moved_payload["columns"] if col["id"] == "col-backlog")
  assert review_column["cardIds"] == ["card-6", "card-1"]
  assert backlog_column["cardIds"] == ["card-2"]

  restarted_client = make_authenticated_client(db_path=db_path)
  persisted = restarted_client.get("/api/board")
  assert persisted.status_code == 200
  persisted_review = next(
    col for col in persisted.json()["columns"] if col["id"] == "col-review"
  )
  assert persisted_review["cardIds"] == ["card-6", "card-1"]


def test_board_routes_return_not_found_and_validation_errors(auth_client: TestClient) -> None:
  missing_column = auth_client.patch(
    "/api/board/columns/col-missing",
    json={"title": "Nope"},
  )
  assert missing_column.status_code == 404
  assert missing_column.json() == {"detail": "Column not found"}

  bad_title = auth_client.post(
    "/api/board/columns/col-backlog/cards",
    json={"title": "   ", "details": "Ignored"},
  )
  assert bad_title.status_code == 400
  assert bad_title.json() == {"detail": "Card title is required"}

  bad_move = auth_client.patch(
    "/api/board/cards/card-1/move",
    json={"column_id": "col-review", "position": 99},
  )
  assert bad_move.status_code == 400
  assert bad_move.json() == {"detail": "Position is out of range"}


def test_update_card_requires_non_empty_title(auth_client: TestClient) -> None:
  response = auth_client.patch(
    "/api/board/cards/card-1",
    json={"title": "   ", "details": "Still here."},
  )

  assert response.status_code == 400
  assert response.json() == {"detail": "Card title is required"}


def test_update_card_allows_empty_details(auth_client: TestClient) -> None:
  response = auth_client.patch(
    "/api/board/cards/card-1",
    json={"title": "Align roadmap themes", "details": ""},
  )

  assert response.status_code == 200
  assert response.json()["cards"]["card-1"]["details"] == ""
