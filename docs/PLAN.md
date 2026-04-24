# Project Plan

This document is the working execution plan for the Project Management MVP. Work should proceed one numbered part at a time. Do not start the next part until the current part is complete and, where called out below, explicitly approved by the user.

## Confirmed constraints

- Ship a single Docker image.
- FastAPI serves the statically built Next.js frontend at `/`.
- Fake auth uses a persistent signed HTTP-only cookie and should survive app restarts.
- Keep the Kanban rules simple for the MVP.
- SQLite is required and must create the database automatically if it does not exist.
- Chat history does not need to be persisted in the database.
- The OpenRouter model string is `openai/gpt-oss-120b:free`.
- Missing `OPENROUTER_API_KEY` is an application error for AI-enabled flows.
- Backend unit tests mock AI calls.
- Integration testing can use dummy AI implementations, but at least one opt-in live integration test must exercise the real OpenRouter path.
- Test stack: `pytest` for backend, `vitest` for frontend, `playwright` for end-to-end.

## Execution rules

- Prefer the smallest working slice in each part.
- Prove root cause before fixing issues.
- Keep documentation concise and current.
- Do not implement future parts early just because the code path is nearby.

## Part 1: Plan

Goal: convert this outline into an execution-ready checklist and document the existing frontend implementation.

Checklist:
- [x] Review root requirements in `AGENTS.md` and current frontend implementation.
- [x] Expand each project part into concrete implementation substeps.
- [x] Add tests to run for each part.
- [x] Add clear success criteria for each part.
- [x] Create `frontend/AGENTS.md` describing the current frontend code and its current limits.
- [x] Ask the user to review and approve the plan before Part 2 begins.

Tests:
- Documentation review only; no runtime tests required.

Success criteria:
- `docs/PLAN.md` is detailed enough to execute part-by-part without guessing major scope.
- `frontend/AGENTS.md` accurately reflects the current frontend demo and test surface.
- The user reviews and approves the plan before implementation continues.

Approval gate:
- Required before Part 2.

Status:
- Approved by the user on 2026-04-24.

## Part 2: Scaffolding

Goal: stand up the backend, container, and local scripts with a minimal working FastAPI plus static HTML proof of life.

Checklist:
- [x] Create backend project structure in `backend/` using FastAPI.
- [x] Add Python dependency management suitable for `uv` in Docker.
- [x] Add an app entrypoint and a health-style API endpoint.
- [x] Add a temporary static HTML response at `/` served by FastAPI.
- [x] Create a single-image Dockerfile that can run the backend locally.
- [x] Add cross-platform start and stop scripts in `scripts/` for Windows, macOS, and Linux.
- [x] Document how to run the scaffold locally.

Tests:
- [x] Backend unit test for the health/example API route.
- [x] Backend integration test confirming `/` returns the temporary HTML.
- [x] Docker smoke test that the container starts and responds locally.
- [x] Script smoke test on the current platform.

Success criteria:
- `docker build` succeeds.
- Starting the app locally serves example HTML at `/`.
- The example page can make at least one successful API call to the backend.
- Start and stop scripts work on the validated platform and are documented for the others.

Status:
- Completed on 2026-04-24.
- Backend scaffold, Docker image, local scripts, and runtime validation are complete.

## Part 3: Add In Frontend

Goal: replace the temporary HTML with the statically built existing Next.js frontend, still served by FastAPI from the same container.

Checklist:
- [x] Decide the frontend build output approach that works cleanly with FastAPI static serving.
- [x] Wire the Docker build so the frontend is built and copied into the final image.
- [x] Update FastAPI to serve the exported frontend assets at `/`.
- [x] Preserve the existing visual design and interactions from the frontend demo.
- [x] Keep the frontend running entirely client-side and in-memory for this part.
- [x] Document the new build and run flow.

Tests:
- [x] Frontend unit tests pass.
- [x] Frontend build succeeds.
- [x] Playwright tests verify the board loads inside the integrated app.
- [x] Integration test confirms FastAPI serves the built frontend asset entrypoint.

Success criteria:
- `/` shows the current Kanban demo instead of placeholder HTML.
- The single container serves both frontend assets and backend routes.
- Existing board interactions still work after integration.

Status:
- Completed on 2026-04-24.
- FastAPI now serves the statically exported Next.js Kanban app at `/`.
- Backend tests, frontend unit tests, integrated Playwright tests, and Docker smoke validation all passed.

## Part 4: Fake User Sign-In

Goal: require a dummy login before showing the board and support logout.

Checklist:
- [x] Define the minimal auth flow using hardcoded credentials `user` and `password`.
- [x] Implement persistent signed HTTP-only cookie-based session handling in FastAPI.
- [x] Add a login screen and logout affordance in the frontend.
- [x] Guard the Kanban page so unauthenticated users are redirected or shown login.
- [x] Return authenticated user state from the backend in a simple, testable way.
- [x] Document session behavior and credential limitations.

Tests:
- [x] Backend unit tests for login, logout, invalid credentials, and session validation.
- [x] Frontend unit tests for login form behavior and authenticated/unauthenticated rendering.
- [x] Playwright tests for successful login, failed login, reload persistence, and logout.

Success criteria:
- Unauthenticated users cannot access the board UI.
- Successful login persists across page reloads and app restarts.
- Logout clears access and returns the user to the login experience.

Status:
- Completed on 2026-04-24.
- FastAPI now provides persistent signed cookie auth for the fixed demo account.
- Frontend login gating, logout, backend auth tests, frontend unit tests, integrated Playwright tests, and Docker auth smoke validation all passed.

## Part 5: Database Modeling

Goal: propose and document the SQLite persistence model for the Kanban board before implementing it.

Checklist:
- [x] Review the current frontend board shape and upcoming backend requirements.
- [x] Compare at least two viable SQLite storage approaches, including a JSON-based approach.
- [x] Recommend one schema for the MVP with reasoning focused on simplicity and future multi-user support.
- [x] Define how board reads, writes, initialization, and migrations will work.
- [x] Document the proposal in `docs/`.
- [x] Ask the user to approve the schema before implementation begins.

Tests:
- [x] Documentation review only; no schema implementation tests yet.

Success criteria:
- The proposal clearly defines the stored entities, JSON usage, and how a user maps to a board.
- Tradeoffs are explicit enough for the user to approve or redirect.
- No implementation begins until the user signs off.

Approval gate:
- Required before Part 6.

Status:
- Completed on 2026-04-24.
- Approved schema is documented in `docs/DATABASE.md`.
- Option B, the normalized relational schema, is the chosen design for Part 6.

## Part 6: Backend

Goal: add the backend persistence and API routes for reading and mutating a user's board.

Checklist:
- [x] Implement SQLite connection and startup initialization.
- [x] Create the database automatically if it does not exist.
- [x] Seed a default board for a user when needed.
- [x] Add authenticated API routes to fetch the current board.
- [x] Add authenticated API routes to rename columns and create, delete, edit, and move cards.
- [x] Validate request payloads with clear error responses.
- [x] Keep API shapes aligned with the frontend board model where practical.
- [x] Document the board API endpoints.

Tests:
- [x] Backend unit tests for database helpers and route validation.
- [x] Backend integration tests for board fetch, mutation flows, and auto-creation behavior.
- [x] Authenticated API tests covering unauthorized access.

Success criteria:
- The backend can fully reconstruct and persist a user's board.
- Board changes survive app restarts.
- API failures are deterministic and readable.

Status:
- Completed on 2026-04-24.
- SQLite board persistence and authenticated board mutation routes are implemented.
- Backend tests cover auto-creation, persistence, validation, and core mutation flows.

## Part 7: Frontend + Backend

Goal: move the Kanban UI from local in-memory state to the backend API.

Checklist:
- [x] Replace local-only board initialization with backend fetch on load.
- [x] Replace direct local mutations with API-backed actions.
- [x] Add loading, saving, and error states that stay visually simple.
- [x] Keep drag-and-drop responsive while ensuring persisted ordering is correct.
- [x] Preserve the existing styling direction while introducing the live data flow.
- [x] Decide whether optimistic updates are necessary; prefer the simplest approach that feels correct.

Tests:
- [x] Frontend unit tests for API-backed board state flows.
- [x] Backend integration tests for the routes used by the UI.
- [x] Playwright end-to-end tests for login plus persistent board interactions.

Success criteria:
- Reloading the page shows the persisted board from SQLite.
- Board mutations from the UI are reflected in the database.
- The UI remains usable and visually consistent during network-backed interactions.

Status:
- Completed on 2026-04-24.
- The frontend now loads the board from the backend and persists rename, add, delete, and move operations through the API.
- Unit, backend integration, and integrated Playwright tests cover the live board flow and persistence across reloads.

## Part 8: AI Connectivity

Goal: add a backend integration with OpenRouter and prove the external call works.

Checklist:
- [x] Add backend configuration for `OPENROUTER_API_KEY` and the fixed model string.
- [x] Fail clearly when AI routes are used without the API key.
- [x] Create a small backend AI client abstraction so unit tests can mock it.
- [x] Add a simple backend route or service path that asks the model a basic prompt such as `2+2`.
- [x] Add a dummy implementation path for non-live integration tests.
- [x] Add one opt-in live integration test for the real OpenRouter path.

Tests:
- [x] Backend unit tests for AI client configuration and error handling.
- [x] Backend unit tests with mocked OpenRouter responses.
- [x] Integration test using a dummy AI implementation.
- [x] Opt-in live integration test against OpenRouter when credentials are available.

Success criteria:
- The backend can successfully call OpenRouter using the configured model.
- Missing API key errors are explicit and covered by tests.
- Live AI verification exists without destabilizing the default local test suite.

Status:
- Completed on 2026-04-24.
- The backend now exposes an authenticated AI probe route backed by an OpenRouter client with a dummy test path.
- Default backend tests pass locally, and the real OpenRouter verification is available through an opt-in live test.

## Part 9: AI Board-Aware Structured Outputs

Goal: always send the board state plus user request to the model and receive a structured response that can optionally update the board.

Checklist:
- [ ] Define the request payload sent to the model, including board JSON and conversation history held in memory for the current chat session.
- [ ] Define the structured response schema with both chat reply content and optional board update instructions.
- [ ] Validate and parse the model response defensively enough to reject invalid outputs.
- [ ] Apply approved board mutations on the backend.
- [ ] Return both the assistant message and the updated board payload to the frontend.
- [ ] Document the AI contract in `docs/`.

Tests:
- [ ] Backend unit tests for schema validation and invalid model outputs.
- [ ] Backend integration tests for no-op replies and board-mutating replies.
- [ ] Dummy AI integration tests covering multiple card/column update scenarios.
- [ ] Opt-in live integration test covering one real structured-output interaction.

Success criteria:
- The backend consistently returns a typed response the frontend can consume.
- Valid AI-generated board changes are persisted.
- Invalid or partial AI outputs fail safely without corrupting the board.

## Part 10: AI Sidebar UI

Goal: add the sidebar chat experience and refresh the board automatically when AI-driven mutations occur.

Checklist:
- [ ] Design and implement a sidebar chat UI that fits the existing visual language.
- [ ] Add message input, submission, loading, error, and response rendering states.
- [ ] Hook the UI into the backend AI endpoint.
- [ ] Refresh or reconcile board state automatically after AI-driven updates.
- [ ] Keep the Kanban and chat interactions usable on desktop and mobile widths.
- [ ] Document how to use the AI feature and its MVP limits.

Tests:
- [ ] Frontend unit tests for chat widget state transitions.
- [ ] Backend integration tests for the AI route used by the sidebar.
- [ ] Playwright tests for sending a chat prompt, receiving a response, and seeing the board refresh.
- [ ] Playwright test for an AI no-op response that leaves the board unchanged.

Success criteria:
- Users can chat with the assistant from the sidebar.
- AI-generated board updates appear in the UI automatically.
- The chat UI is usable without compromising the existing board experience.

## Review checkpoint

Part 1 review completed on 2026-04-24.

Confirmed by the user:

- The part ordering matches the intended delivery sequence.
- The approval gates are in the right places.
- The testing expectations are appropriate for each part.
- The database modeling decision remains deferred until Part 5.
- Part 2 may begin.