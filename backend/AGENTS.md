## Backend Agent Notes

This folder contains the FastAPI backend for the Project Management MVP.

Current scope in Part 4:
- Serve the statically exported Next.js frontend at `/`.
- Keep simple JSON API routes available for backend verification.
- Provide session-based fake auth using the fixed demo credentials.
- Provide the foundation for later persistence and AI work.

Working guidance:
- Keep the backend small and explicit.
- Prefer simple route handlers and testable helpers over premature abstraction.
- Preserve a clean separation between frontend serving concerns and future Kanban logic.