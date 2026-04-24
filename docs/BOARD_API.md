# Board API

All board routes require the authenticated demo session cookie established by `POST /api/auth/login`.

All successful mutation routes return the full board aggregate in the current frontend shape.

## GET /api/board

Returns the authenticated user's board.

If the user or board does not exist yet, the backend creates them automatically and seeds the default board.

Response shape:

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

## PATCH /api/board/columns/{columnId}

Rename a column.

Request body:

```json
{
  "title": "In Review"
}
```

## POST /api/board/columns/{columnId}/cards

Create a card in a column.

Request body:

```json
{
  "title": "Write migration tests",
  "details": "Cover board reads and moves."
}
```

If `details` is blank, the backend stores `No details yet.`.

## PATCH /api/board/cards/{cardId}

Update a card's title and details.

Request body:

```json
{
  "title": "Write backend tests",
  "details": "Cover board reads, updates, deletes, and moves."
}
```

Both fields are required by the current MVP contract.

## DELETE /api/board/columns/{columnId}/cards/{cardId}

Delete a card from a column.

## PATCH /api/board/cards/{cardId}/move

Move a card to a target column and index.

Request body:

```json
{
  "column_id": "col-review",
  "position": 0
}
```

`position` is the final index of the card inside the target column after the move is applied.