from __future__ import annotations

import secrets
import sqlite3
from pathlib import Path

DEFAULT_BOARD = {
  "columns": [
    {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"]},
    {"id": "col-discovery", "title": "Discovery", "cardIds": ["card-3"]},
    {"id": "col-progress", "title": "In Progress", "cardIds": ["card-4", "card-5"]},
    {"id": "col-review", "title": "Review", "cardIds": ["card-6"]},
    {"id": "col-done", "title": "Done", "cardIds": ["card-7", "card-8"]},
  ],
  "cards": {
    "card-1": {
      "id": "card-1",
      "title": "Align roadmap themes",
      "details": "Draft quarterly themes with impact statements and metrics.",
    },
    "card-2": {
      "id": "card-2",
      "title": "Gather customer signals",
      "details": "Review support tags, sales notes, and churn feedback.",
    },
    "card-3": {
      "id": "card-3",
      "title": "Prototype analytics view",
      "details": "Sketch initial dashboard layout and key drill-downs.",
    },
    "card-4": {
      "id": "card-4",
      "title": "Refine status language",
      "details": "Standardize column labels and tone across the board.",
    },
    "card-5": {
      "id": "card-5",
      "title": "Design card layout",
      "details": "Add hierarchy and spacing for scanning dense lists.",
    },
    "card-6": {
      "id": "card-6",
      "title": "QA micro-interactions",
      "details": "Verify hover, focus, and loading states.",
    },
    "card-7": {
      "id": "card-7",
      "title": "Ship marketing page",
      "details": "Final copy approved and asset pack delivered.",
    },
    "card-8": {
      "id": "card-8",
      "title": "Close onboarding sprint",
      "details": "Document release notes and share internally.",
    },
  },
}


class BoardStoreError(Exception):
  pass


class BoardValidationError(BoardStoreError):
  pass


class ColumnNotFoundError(BoardStoreError):
  pass


class CardNotFoundError(BoardStoreError):
  pass


class BoardStore:
  def __init__(self, db_path: Path):
    self.db_path = db_path

  def initialize(self) -> None:
    self.db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = self._connect()
    try:
      version = connection.execute("PRAGMA user_version").fetchone()[0]
      if version != 0:
        return

      connection.executescript(
        """
        CREATE TABLE users (
          id INTEGER PRIMARY KEY,
          username TEXT NOT NULL UNIQUE,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE boards (
          id INTEGER PRIMARY KEY,
          user_id INTEGER NOT NULL UNIQUE,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE columns (
          board_id INTEGER NOT NULL,
          column_id TEXT NOT NULL,
          title TEXT NOT NULL,
          sort_order INTEGER NOT NULL,
          PRIMARY KEY (board_id, column_id),
          UNIQUE (board_id, sort_order),
          FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE
        );

        CREATE TABLE cards (
          board_id INTEGER NOT NULL,
          card_id TEXT NOT NULL,
          column_id TEXT NOT NULL,
          title TEXT NOT NULL,
          details TEXT NOT NULL,
          sort_order INTEGER NOT NULL,
          PRIMARY KEY (board_id, card_id),
          UNIQUE (board_id, column_id, sort_order),
          FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
          FOREIGN KEY (board_id, column_id) REFERENCES columns(board_id, column_id) ON DELETE CASCADE
        );

        CREATE INDEX idx_columns_board_id ON columns(board_id);
        CREATE INDEX idx_cards_board_id ON cards(board_id);
        CREATE INDEX idx_cards_column_id ON cards(column_id);
        """
      )
      connection.execute("PRAGMA user_version = 1")
      connection.commit()
    finally:
      connection.close()

  def get_board(self, username: str) -> dict[str, object]:
    connection = self._connect()
    try:
      board_id = self._ensure_board(connection, username)
      connection.commit()
      return self._load_board(connection, board_id)
    finally:
      connection.close()

  def rename_column(self, username: str, column_id: str, title: str) -> dict[str, object]:
    normalized_title = self._normalize_title(title, "Column title is required")
    connection = self._connect()
    try:
      board_id = self._ensure_board(connection, username)
      updated = connection.execute(
        "UPDATE columns SET title = ? WHERE board_id = ? AND column_id = ?",
        (normalized_title, board_id, column_id),
      )
      if updated.rowcount == 0:
        raise ColumnNotFoundError("Column not found")
      self._touch_board(connection, board_id)
      connection.commit()
      return self._load_board(connection, board_id)
    finally:
      connection.close()

  def add_card(self, username: str, column_id: str, title: str, details: str) -> dict[str, object]:
    normalized_title = self._normalize_title(title, "Card title is required")
    normalized_details = self._normalize_details(details)
    connection = self._connect()
    try:
      board_id = self._ensure_board(connection, username)
      self._require_column(connection, board_id, column_id)
      next_order = connection.execute(
        "SELECT COALESCE(MAX(sort_order) + 1, 0) FROM cards WHERE board_id = ? AND column_id = ?",
        (board_id, column_id),
      ).fetchone()[0]
      card_id = self._generate_card_id()
      connection.execute(
        "INSERT INTO cards (board_id, card_id, column_id, title, details, sort_order) VALUES (?, ?, ?, ?, ?, ?)",
        (board_id, card_id, column_id, normalized_title, normalized_details, next_order),
      )
      self._touch_board(connection, board_id)
      connection.commit()
      return self._load_board(connection, board_id)
    finally:
      connection.close()

  def update_card(self, username: str, card_id: str, title: str, details: str) -> dict[str, object]:
    normalized_title = self._normalize_title(title, "Card title is required")
    normalized_details = self._normalize_details(details)
    connection = self._connect()
    try:
      board_id = self._ensure_board(connection, username)
      updated = connection.execute(
        "UPDATE cards SET title = ?, details = ? WHERE board_id = ? AND card_id = ?",
        (normalized_title, normalized_details, board_id, card_id),
      )
      if updated.rowcount == 0:
        raise CardNotFoundError("Card not found")
      self._touch_board(connection, board_id)
      connection.commit()
      return self._load_board(connection, board_id)
    finally:
      connection.close()

  def delete_card(self, username: str, column_id: str, card_id: str) -> dict[str, object]:
    connection = self._connect()
    try:
      board_id = self._ensure_board(connection, username)
      card_row = self._require_card(connection, board_id, card_id)
      if card_row["column_id"] != column_id:
        raise CardNotFoundError("Card not found in column")

      remaining_ids = self._get_ordered_card_ids(connection, board_id, column_id)
      remaining_ids.remove(card_id)
      connection.execute(
        "DELETE FROM cards WHERE board_id = ? AND card_id = ?",
        (board_id, card_id),
      )
      self._rewrite_column_order(connection, board_id, column_id, remaining_ids)
      self._touch_board(connection, board_id)
      connection.commit()
      return self._load_board(connection, board_id)
    finally:
      connection.close()

  def move_card(
    self,
    username: str,
    card_id: str,
    target_column_id: str,
    position: int,
  ) -> dict[str, object]:
    connection = self._connect()
    try:
      board_id = self._ensure_board(connection, username)
      self._require_column(connection, board_id, target_column_id)
      card_row = self._require_card(connection, board_id, card_id)
      source_column_id = card_row["column_id"]

      if position < 0:
        raise BoardValidationError("Position must be zero or greater")

      if source_column_id == target_column_id:
        ordered_ids = self._get_ordered_card_ids(connection, board_id, source_column_id)
        ordered_ids.remove(card_id)
        if position > len(ordered_ids):
          raise BoardValidationError("Position is out of range")
        ordered_ids.insert(position, card_id)
        self._rewrite_column_order(connection, board_id, source_column_id, ordered_ids)
      else:
        source_ids = self._get_ordered_card_ids(connection, board_id, source_column_id)
        source_ids.remove(card_id)
        target_ids = self._get_ordered_card_ids(connection, board_id, target_column_id)
        if position > len(target_ids):
          raise BoardValidationError("Position is out of range")

        self._prepare_column_for_reorder(connection, board_id, source_column_id)
        self._prepare_column_for_reorder(connection, board_id, target_column_id)
        connection.execute(
          "UPDATE cards SET column_id = ?, sort_order = ? WHERE board_id = ? AND card_id = ?",
          (target_column_id, 2_000_000, board_id, card_id),
        )
        target_ids.insert(position, card_id)
        self._apply_column_order(connection, board_id, source_column_id, source_ids)
        self._apply_column_order(connection, board_id, target_column_id, target_ids)

      self._touch_board(connection, board_id)
      connection.commit()
      return self._load_board(connection, board_id)
    finally:
      connection.close()

  def reset_board(self, username: str) -> dict[str, object]:
    connection = self._connect()
    try:
      user_row = connection.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,),
      ).fetchone()
      if user_row is not None:
        connection.execute(
          "DELETE FROM boards WHERE user_id = ?",
          (user_row["id"],),
        )

      board_id = self._ensure_board(connection, username)
      connection.commit()
      return self._load_board(connection, board_id)
    finally:
      connection.close()

  def _connect(self) -> sqlite3.Connection:
    connection = sqlite3.connect(self.db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

  def _ensure_board(self, connection: sqlite3.Connection, username: str) -> int:
    user_row = connection.execute(
      "SELECT id FROM users WHERE username = ?",
      (username,),
    ).fetchone()
    if user_row is None:
      cursor = connection.execute(
        "INSERT INTO users (username) VALUES (?)",
        (username,),
      )
      user_id = cursor.lastrowid
    else:
      user_id = user_row["id"]

    board_row = connection.execute(
      "SELECT id FROM boards WHERE user_id = ?",
      (user_id,),
    ).fetchone()
    if board_row is not None:
      return board_row["id"]

    cursor = connection.execute(
      "INSERT INTO boards (user_id) VALUES (?)",
      (user_id,),
    )
    board_id = cursor.lastrowid
    self._seed_default_board(connection, board_id)
    return board_id

  def _seed_default_board(self, connection: sqlite3.Connection, board_id: int) -> None:
    for column_index, column in enumerate(DEFAULT_BOARD["columns"]):
      connection.execute(
        "INSERT INTO columns (board_id, column_id, title, sort_order) VALUES (?, ?, ?, ?)",
        (board_id, column["id"], column["title"], column_index),
      )
      for card_index, card_id in enumerate(column["cardIds"]):
        card = DEFAULT_BOARD["cards"][card_id]
        connection.execute(
          "INSERT INTO cards (board_id, card_id, column_id, title, details, sort_order) VALUES (?, ?, ?, ?, ?, ?)",
          (
            board_id,
            card["id"],
            column["id"],
            card["title"],
            card["details"],
            card_index,
          ),
        )

  def _load_board(self, connection: sqlite3.Connection, board_id: int) -> dict[str, object]:
    column_rows = connection.execute(
      "SELECT column_id, title FROM columns WHERE board_id = ? ORDER BY sort_order",
      (board_id,),
    ).fetchall()
    card_rows = connection.execute(
      "SELECT card_id, column_id, title, details FROM cards WHERE board_id = ? ORDER BY column_id, sort_order",
      (board_id,),
    ).fetchall()

    cards_by_id: dict[str, dict[str, str]] = {}
    card_ids_by_column: dict[str, list[str]] = {}
    for row in card_rows:
      card_id = row["card_id"]
      column_id = row["column_id"]
      cards_by_id[card_id] = {
        "id": card_id,
        "title": row["title"],
        "details": row["details"],
      }
      card_ids_by_column.setdefault(column_id, []).append(card_id)

    columns = [
      {
        "id": row["column_id"],
        "title": row["title"],
        "cardIds": card_ids_by_column.get(row["column_id"], []),
      }
      for row in column_rows
    ]
    return {"columns": columns, "cards": cards_by_id}

  def _get_ordered_card_ids(
    self,
    connection: sqlite3.Connection,
    board_id: int,
    column_id: str,
  ) -> list[str]:
    rows = connection.execute(
      "SELECT card_id FROM cards WHERE board_id = ? AND column_id = ? ORDER BY sort_order",
      (board_id, column_id),
    ).fetchall()
    return [row["card_id"] for row in rows]

  def _require_column(
    self,
    connection: sqlite3.Connection,
    board_id: int,
    column_id: str,
  ) -> sqlite3.Row:
    row = connection.execute(
      "SELECT column_id FROM columns WHERE board_id = ? AND column_id = ?",
      (board_id, column_id),
    ).fetchone()
    if row is None:
      raise ColumnNotFoundError("Column not found")
    return row

  def _require_card(
    self,
    connection: sqlite3.Connection,
    board_id: int,
    card_id: str,
  ) -> sqlite3.Row:
    row = connection.execute(
      "SELECT card_id, column_id FROM cards WHERE board_id = ? AND card_id = ?",
      (board_id, card_id),
    ).fetchone()
    if row is None:
      raise CardNotFoundError("Card not found")
    return row

  def _prepare_column_for_reorder(
    self,
    connection: sqlite3.Connection,
    board_id: int,
    column_id: str,
  ) -> None:
    connection.execute(
      "UPDATE cards SET sort_order = sort_order + 1000000 WHERE board_id = ? AND column_id = ?",
      (board_id, column_id),
    )

  def _apply_column_order(
    self,
    connection: sqlite3.Connection,
    board_id: int,
    column_id: str,
    card_ids: list[str],
  ) -> None:
    for index, current_card_id in enumerate(card_ids):
      connection.execute(
        "UPDATE cards SET sort_order = ? WHERE board_id = ? AND card_id = ? AND column_id = ?",
        (index, board_id, current_card_id, column_id),
      )

  def _rewrite_column_order(
    self,
    connection: sqlite3.Connection,
    board_id: int,
    column_id: str,
    card_ids: list[str],
  ) -> None:
    self._prepare_column_for_reorder(connection, board_id, column_id)
    self._apply_column_order(connection, board_id, column_id, card_ids)

  def _touch_board(self, connection: sqlite3.Connection, board_id: int) -> None:
    connection.execute(
      "UPDATE boards SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
      (board_id,),
    )

  def _generate_card_id(self) -> str:
    return f"card-{secrets.token_hex(8)}"

  def _normalize_title(self, value: str, message: str) -> str:
    normalized = value.strip()
    if not normalized:
      raise BoardValidationError(message)
    return normalized

  def _normalize_details(self, value: str) -> str:
    normalized = value.strip()
    return normalized or "No details yet."