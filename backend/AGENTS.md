## Backend Agent Notes

This folder contains the FastAPI backend for the Project Management MVP.

Current scope in Part 2:
- Serve a temporary HTML scaffold at `/`.
- Expose simple JSON API routes used to verify the backend is running.
- Provide the foundation for later auth, persistence, and AI work.

Working guidance:
- Keep the backend small and explicit.
- Prefer simple route handlers and testable helpers over premature abstraction.
- Preserve a clean separation between scaffold-only behavior and future Kanban logic.