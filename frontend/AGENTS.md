# Frontend Agent Notes

## Purpose

The `frontend/` directory contains the existing standalone Kanban demo. It is currently a frontend-only Next.js application and is the visual/interaction baseline for later integration work.

## Current stack

- Next.js 16 App Router
- React 19
- TypeScript
- Tailwind CSS 4
- `@dnd-kit` for drag-and-drop
- Vitest plus Testing Library for unit tests
- Playwright for end-to-end tests

## Current entrypoints

- `src/app/page.tsx` renders `KanbanBoard` directly.
- `src/app/layout.tsx` defines metadata and loads the font setup.
- `src/app/globals.css` defines the color variables and global styling foundation.

## Current behavior

- Shows a login screen until the user authenticates with the demo account.
- Renders a single-board Kanban UI with five columns after login.
- Column titles are editable inline.
- Cards can be dragged within and across columns.
- Cards can be added and removed.
- Authentication uses backend session endpoints and a persistent HTTP-only cookie.
- Board state is still entirely client-side and starts from static seed data in `src/lib/kanban.ts`.
- There is no board persistence or AI UI yet.
- There is currently no inline editing flow for existing card title/details beyond add and delete.

## Key files

- `src/components/KanbanBoard.tsx`: top-level client component that owns board state and drag handlers.
- `src/components/KanbanApp.tsx`: auth-aware client shell that checks session state and decides whether to render login or board UI.
- `src/components/LoginForm.tsx`: login screen and credential form.
- `src/components/KanbanColumn.tsx`: column shell, rename input, droppable area, and new-card form wiring.
- `src/components/KanbanCard.tsx`: sortable card UI with delete action.
- `src/components/NewCardForm.tsx`: local add-card form state.
- `src/components/KanbanCardPreview.tsx`: drag overlay preview.
- `src/lib/kanban.ts`: board types, initial seeded data, move logic, and ID creation helper.

## Existing tests

- `src/components/KanbanApp.test.tsx` covers unauthenticated load, login success, login failure, and logout.
- `src/components/KanbanBoard.test.tsx` covers rendering, renaming a column, and adding/removing a card.
- `src/lib/kanban.test.ts` covers card movement logic.
- `tests/kanban.spec.ts` covers login gating, board load, add-card flow, drag-and-drop flow, session persistence, and logout in Playwright.

## Working guidance

- Preserve the current visual language unless a later plan step explicitly changes it.
- Treat this directory as the source of truth for the current Kanban UI behavior.
- When integrating with the backend later, keep changes incremental so existing interactions stay testable.
- Do not assume board persistence or AI support already exists here.

## Commands

- `npm run dev`
- `npm run build`
- `npm run test:unit`
- `npm run test:e2e`
- `npm run test:all`