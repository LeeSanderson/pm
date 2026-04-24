# Database Proposal

## Goal

Define the SQLite persistence model for the MVP Kanban board before implementing backend board storage.

The proposal should match what the application already does today:

- one signed-in user session at a time for the demo flow
- one board per user
- a board shape that already exists in the frontend as a JSON aggregate
- simple board mutations today, with room to grow into richer querying later

## Current board shape

The frontend already uses this canonical shape:

```json
{
  "columns": [
    {
      "id": "col-backlog",
      "title": "Backlog",
      "cardIds": ["card-1", "card-2"]
    }
  ],
  "cards": {
    "card-1": {
      "id": "card-1",
      "title": "Align roadmap themes",
      "details": "Draft quarterly themes with impact statements and metrics."
    }
  }
}
```

That shape already captures:

- column order
- card order within each column
- the full editable payload for each card

This matters because the backend still needs to return this exact aggregate to the frontend, even if the persisted representation is relational.

## Options considered

### Option A: one JSON board row per user

Store one `users` row and one `boards` row per user. The board payload is stored as JSON text in SQLite.

Schema sketch:

```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE boards (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL UNIQUE,
  schema_version INTEGER NOT NULL DEFAULT 1,
  board_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

Pros:

- matches the frontend model exactly
- simplest read path: one query to load the full board
- simplest write path: validate, update, replace one JSON payload
- keeps Part 6 and Part 7 focused on product behavior rather than mapping logic
- still supports future multi-user behavior through `users`
- easy to seed a default board when a user has no existing board

Cons:

- individual card or column queries are not first-class SQL operations
- concurrent partial updates would require whole-board overwrite protection if the app grows
- reporting and analytics are weaker without later extraction or denormalization

### Option B: normalized board tables

Store users, boards, columns, cards, and card positions as separate relational records.

Schema sketch:

```sql
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
  id TEXT PRIMARY KEY,
  board_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  sort_order INTEGER NOT NULL,
  FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE
);

CREATE TABLE cards (
  id TEXT PRIMARY KEY,
  board_id INTEGER NOT NULL,
  column_id TEXT NOT NULL,
  title TEXT NOT NULL,
  details TEXT NOT NULL,
  sort_order INTEGER NOT NULL,
  FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
  FOREIGN KEY (column_id) REFERENCES columns(id) ON DELETE CASCADE
);
```

Pros:

- strong relational integrity
- easy SQL querying by column, card, or ordering
- easier future reporting if the product expands significantly

Cons:

- forces backend-to-frontend mapping immediately
- more tables, more queries, more reorder logic, more tests
- adds complexity before the MVP needs it
- increases the risk of overengineering relative to the current product scope

## Decision

The schema decision is Option B.

Why this was chosen:

- it is more flexible for future changes
- it is easier to reason about as explicit relational data
- it keeps card ordering and column ordering visible in the schema instead of implicit inside a JSON blob

## Recommended MVP schema

Use four tables:

- `users`
- `boards`
- `columns`
- `cards`

The frontend board shape stays the same at the API boundary. The backend assembles and returns that aggregate from relational rows.

### `users`

Purpose:
- support the current demo user and future multi-user behavior

Columns:
- `id INTEGER PRIMARY KEY`
- `username TEXT NOT NULL UNIQUE`
- `created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`

### `boards`

Purpose:
- represent one board owned by one user

Columns:
- `id INTEGER PRIMARY KEY`
- `user_id INTEGER NOT NULL UNIQUE`
- `created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`

Constraints:
- `user_id` is unique so a user can only own one board in the MVP
- `FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE`

### `columns`

Purpose:
- store board columns and their order

Columns:
- `board_id INTEGER NOT NULL`
- `column_id TEXT NOT NULL`
- `title TEXT NOT NULL`
- `sort_order INTEGER NOT NULL`

Constraints:
- `PRIMARY KEY (board_id, column_id)`
- `UNIQUE (board_id, sort_order)`
- `FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE`

### `cards`

Purpose:
- store cards, their owning column, and their order within that column

Columns:
- `board_id INTEGER NOT NULL`
- `card_id TEXT NOT NULL`
- `column_id TEXT NOT NULL`
- `title TEXT NOT NULL`
- `details TEXT NOT NULL`
- `sort_order INTEGER NOT NULL`

Constraints:
- `PRIMARY KEY (board_id, card_id)`
- `UNIQUE (board_id, column_id, sort_order)`
- `FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE`
- `FOREIGN KEY (board_id, column_id) REFERENCES columns(board_id, column_id) ON DELETE CASCADE`

## Schema sketch

```sql
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
```

## Mapping to the existing frontend shape

The API returned to the frontend should remain:

```json
{
  "columns": [
    {
      "id": "col-backlog",
      "title": "Backlog",
      "cardIds": ["card-1", "card-2"]
    }
  ],
  "cards": {
    "card-1": {
      "id": "card-1",
      "title": "Align roadmap themes",
      "details": "Draft quarterly themes with impact statements and metrics."
    }
  }
}
```

The relational model stores the same information as:

- one `boards` row
- ordered `columns` rows for that board
- ordered `cards` rows, each linked to a column

The backend read path reconstructs the current aggregate from those rows.

## Read and write model

### User lookup

- On authenticated board requests, use the session username from the auth cookie.
- Look up `users.username`.
- If the user row does not exist yet, create it lazily.

### Board initialization

- When the user exists but has no `boards` row yet, create one automatically.
- Insert one `boards` row.
- Seed the default column rows with `sort_order` values in display order.
- Seed the default card rows with `column_id` and `sort_order` values matching the current frontend seed data.

### Board reads

- Query the `boards` row for the current user.
- Query `columns` ordered by `sort_order`.
- Query `cards` ordered by `column_id`, then `sort_order`.
- Reconstruct the existing frontend board aggregate in Python.
- Return that aggregate to the frontend.

### Board writes

Apply validated mutation-specific writes in a transaction.

Examples:

- rename column: update `columns.title`
- create card: insert into `cards` with the next `sort_order` in the target column
- delete card: delete the row, then compact `sort_order` in that column
- move card within a column: rewrite `sort_order` for the affected rows in that column
- move card across columns: update `column_id`, then rewrite `sort_order` in both affected columns

Each successful write should update `boards.updated_at`.

## API shape implication for Part 6

The normalized schema aligns well with mutation-specific endpoints:

- `GET /api/board`
- `PATCH /api/board/columns/{columnId}` for rename
- `POST /api/board/columns/{columnId}/cards`
- `DELETE /api/board/columns/{columnId}/cards/{cardId}`
- `PATCH /api/board/cards/{cardId}/move`

This is preferable to a whole-board `PUT` for the normalized design because:

- each endpoint maps naturally to a small relational write
- validation is clearer per mutation
- it avoids sending the full board payload for every small change

## Initialization and migrations

Use simple startup initialization in Part 6:

1. Open the SQLite database file.
2. Enable foreign keys with `PRAGMA foreign_keys = ON`.
3. Check `PRAGMA user_version`.
4. If `user_version = 0`, create the initial tables and set `PRAGMA user_version = 1`.

Initial migration should create:

- `users`
- `boards`
- `columns`
- `cards`
- indexes implied by the unique constraints

Migration strategy after that:

- keep database schema versioning in `PRAGMA user_version`
- add future migrations as explicit table/index evolution steps
- keep the API response shape stable even if storage evolves internally

Unlike the JSON-board design, this option does not need a separate per-board payload version column.

## Why this is the right cutoff for now

This design deliberately does not add:

- separate database-backed session storage
- chat history persistence
- audit trails or event sourcing

It does add normalized board storage now, because that is the chosen tradeoff for flexibility and clarity.

## Approved decision

Approved target:

- adopt `users`, `boards`, `columns`, and `cards` as the MVP schema
- keep the frontend API payload in the current board aggregate shape
- use `PRAGMA user_version` for schema migrations

Part 6 should implement persistence against this relational schema.