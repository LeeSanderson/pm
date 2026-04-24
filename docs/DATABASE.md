# Database Proposal

## Goal

Define the SQLite persistence model for the MVP Kanban board before implementing backend board storage.

The proposal should match what the application already does today:

- one signed-in user session at a time for the demo flow
- one board per user
- a board shape that already exists in the frontend as a JSON aggregate
- simple board mutations without premature normalization

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

This matters because every Part 6 and Part 7 operation can be expressed as: load one board, modify one in-memory aggregate, write one board back.

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

## Recommendation

Recommend Option A for the MVP.

Reasoning:

- It is the simplest schema that supports all currently planned board mutations.
- It preserves the existing frontend board structure without translation.
- It keeps Part 6 focused on API behavior and persistence instead of schema choreography.
- It still leaves a clean migration path to normalization later if the product needs richer querying.

## Proposed MVP schema

Use two tables:

### `users`

Purpose:
- future-proof the app for multiple users even though the demo login is fixed today

Columns:
- `id INTEGER PRIMARY KEY`
- `username TEXT NOT NULL UNIQUE`
- `created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`

### `boards`

Purpose:
- store exactly one board per user as a single JSON payload

Columns:
- `id INTEGER PRIMARY KEY`
- `user_id INTEGER NOT NULL UNIQUE`
- `schema_version INTEGER NOT NULL DEFAULT 1`
- `board_json TEXT NOT NULL`
- `created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`

Constraints:
- `user_id` is unique so a user can only own one board in the MVP
- `FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE`

Canonical payload stored in `board_json`:

```json
{
  "columns": [
    {
      "id": "col-backlog",
      "title": "Backlog",
      "cardIds": ["card-1", "card-2"]
    },
    {
      "id": "col-discovery",
      "title": "Discovery",
      "cardIds": ["card-3"]
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

## Read and write model

### User lookup

- On authenticated board requests, use the session username from the auth cookie.
- Look up `users.username`.
- If the user row does not exist yet, create it lazily.

### Board initialization

- When the user exists but has no `boards` row yet, create one automatically.
- Seed `board_json` from the current default board data.
- Set `schema_version = 1`.

### Board reads

- Query `boards` by `user_id`.
- Deserialize `board_json` into the existing Python/TypeScript board shape.
- Return that payload directly to the frontend.

### Board writes

- Read the current board for the authenticated user.
- Apply one validated mutation in Python.
- Serialize the full board back into `board_json`.
- Update `updated_at` in the same transaction.

For the MVP, whole-board writes are acceptable because:

- there is only one board per user
- edits are user-driven and low volume
- the board payload is small

## API shape implication for Part 6

This proposal supports either of these API styles:

### Preferred MVP style

- `GET /api/board`
- `PATCH /api/board/columns/{columnId}` for rename
- `POST /api/board/columns/{columnId}/cards`
- `DELETE /api/board/columns/{columnId}/cards/{cardId}`
- `PATCH /api/board/cards/{cardId}/move`

Each route can still:

- load one board aggregate
- modify it in memory
- write one JSON payload back

### Simpler fallback

- `GET /api/board`
- `PUT /api/board`

That is even simpler technically, but the first style gives cleaner backend validation and smaller frontend payloads.

## Initialization and migrations

Use simple startup initialization in Part 6:

1. Open the SQLite database file.
2. Enable foreign keys with `PRAGMA foreign_keys = ON`.
3. Check `PRAGMA user_version`.
4. If `user_version = 0`, create the initial tables and set `PRAGMA user_version = 1`.

Initial migration should create:

- `users`
- `boards`
- indexes implied by the unique constraints

Migration strategy after that:

- keep database schema versioning in `PRAGMA user_version`
- keep board payload versioning in `boards.schema_version`
- if the JSON payload shape changes later, migrate rows in Python on startup or in an explicit migration step

That split keeps relational migrations separate from payload migrations.

## Why this is the right cutoff for now

This design deliberately does not add:

- separate database-backed session storage
- chat history persistence
- normalized card and column tables
- audit trails or event sourcing

Those would all be valid future directions, but none are required to support the current MVP parts.

## Approval requested

Recommended approval target:

- adopt `users` plus `boards(board_json)` as the MVP schema
- keep `board_json` aligned to the current frontend board shape
- use `PRAGMA user_version` for schema migrations and `boards.schema_version` for payload versioning

If approved, Part 6 can implement the persistence layer against this design without reopening the schema decision.