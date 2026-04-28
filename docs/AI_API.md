# AI API

All AI routes require the authenticated demo session cookie established by `POST /api/auth/login`.

## POST /api/ai/probe

Simple Part 8 verification route.

Response shape:

```json
{
  "model": "openai/gpt-oss-120b:free",
  "prompt": "What is 2+2? Reply with digits only.",
  "reply": "4"
}
```

## POST /api/ai/chat

Board-aware Part 9 route.

Request body:

```json
{
  "message": "Move card-1 to Review and add a follow-up card in Backlog."
}
```

Response shape:

```json
{
  "assistantMessage": "I moved the roadmap card into Review and added a follow-up item in Backlog.",
  "appliedOperations": [
    {
      "type": "move_card",
      "card_id": "card-1",
      "column_id": "col-review",
      "position": 0
    },
    {
      "type": "create_card",
      "column_id": "col-backlog",
      "title": "Schedule roadmap review",
      "details": "Book time with design and engineering leads."
    }
  ],
  "board": {
    "columns": [
      {
        "id": "col-backlog",
        "title": "Backlog",
        "cardIds": ["card-2", "card-9"]
      }
    ],
    "cards": {
      "card-1": {
        "id": "card-1",
        "title": "Align roadmap themes",
        "details": "Draft quarterly themes with impact statements and metrics."
      }
    }
  },
  "model": "openai/gpt-oss-120b:free"
}
```

The `board` object uses the same aggregate shape returned by the board routes.

## Model contract

The backend sends the model:

- The current board JSON.
- Conversation history for the current chat session, kept in server memory only.
- The latest user message.
- Instructions to return JSON only.

The model must return this JSON shape:

```json
{
  "assistant_message": "string",
  "board_operations": [
    {
      "type": "rename_column",
      "column_id": "col-review",
      "title": "Ready"
    },
    {
      "type": "create_card",
      "column_id": "col-backlog",
      "title": "Schedule roadmap review",
      "details": "Book time with design and engineering leads."
    },
    {
      "type": "update_card",
      "card_id": "card-1",
      "title": "Align roadmap themes and owners",
      "details": "Add owners and due dates."
    },
    {
      "type": "move_card",
      "card_id": "card-1",
      "column_id": "col-review",
      "position": 0
    },
    {
      "type": "delete_card",
      "card_id": "card-7"
    }
  ]
}
```

Rules enforced by the backend:

- `assistant_message` is required.
- `board_operations` must be an array.
- Unknown operation types are rejected.
- Referenced card and column ids must exist when required.
- Multi-step AI mutations are applied atomically. If any operation is invalid, none of the operations are persisted.
- Invalid model outputs return `502` and leave the board unchanged.

## Conversation history

Conversation history is stored in backend memory per authenticated session.

- It is cleared on logout.
- It is cleared when the backend process restarts.
- It is not written to SQLite.

## Error behavior

- Missing `OPENROUTER_API_KEY` returns `503` when an AI route is used.
- Upstream OpenRouter failures return `502`.
- Invalid AI JSON or invalid AI-generated board operations return `502`.