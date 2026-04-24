## Scripts Agent Notes

This folder contains helper scripts for running and stopping the local Docker-based app.

Current scope in Part 3:
- Build the single application image.
- Start the container locally on port 8000 with the exported frontend served by FastAPI.
- Stop and remove the local container cleanly.

Working guidance:
- Keep scripts explicit and readable.
- Prefer deterministic container names and image tags.
- Avoid adding environment-specific behavior unless it is required.