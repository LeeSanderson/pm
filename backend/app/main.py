from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Project Management MVP Backend")


INDEX_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Project Management MVP</title>
    <style>
      :root {
        color-scheme: light;
        --accent-yellow: #ecad0a;
        --primary-blue: #209dd7;
        --secondary-purple: #753991;
        --navy-dark: #032147;
        --gray-text: #888888;
        --surface: #f7f8fb;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        padding: 24px;
        background:
          radial-gradient(circle at top left, rgba(32, 157, 215, 0.18), transparent 32%),
          radial-gradient(circle at bottom right, rgba(117, 57, 145, 0.12), transparent 34%),
          var(--surface);
        color: var(--navy-dark);
        font-family: "Segoe UI", sans-serif;
      }

      main {
        width: min(720px, 100%);
        border: 1px solid rgba(3, 33, 71, 0.08);
        border-radius: 28px;
        background: rgba(255, 255, 255, 0.92);
        padding: 32px;
        box-shadow: 0 18px 40px rgba(3, 33, 71, 0.12);
      }

      .eyebrow {
        margin: 0;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.28em;
        text-transform: uppercase;
        color: var(--gray-text);
      }

      h1 {
        margin: 14px 0 10px;
        font-size: clamp(2rem, 4vw, 3rem);
      }

      p {
        margin: 0;
        line-height: 1.7;
      }

      .status {
        margin-top: 24px;
        padding: 18px 20px;
        border-radius: 18px;
        background: rgba(32, 157, 215, 0.08);
        border: 1px solid rgba(32, 157, 215, 0.16);
      }

      .status strong {
        display: block;
        margin-bottom: 8px;
      }

      code {
        font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
      }
    </style>
  </head>
  <body>
    <main>
      <p class="eyebrow">Part 2 Scaffold</p>
      <h1>Hello from the Project Management MVP</h1>
      <p>
        FastAPI is serving this temporary page from <code>/</code>. This will be
        replaced by the built Next.js frontend in Part 3.
      </p>

      <section class="status" aria-live="polite">
        <strong>Example API call</strong>
        <div id="api-result">Calling <code>/api/hello</code>...</div>
      </section>
    </main>

    <script>
      const result = document.getElementById("api-result");

      fetch("/api/hello")
        .then((response) => response.json())
        .then((payload) => {
          result.textContent = payload.message;
        })
        .catch(() => {
          result.textContent = "Unable to reach the API.";
        });
    </script>
  </body>
</html>
""".strip()


@app.get("/", response_class=HTMLResponse)
def read_index() -> HTMLResponse:
  return HTMLResponse(INDEX_HTML)


@app.get("/api/health")
def read_health() -> dict[str, str]:
  return {"status": "ok"}


@app.get("/api/hello")
def read_hello() -> dict[str, str]:
  return {"message": "Hello from FastAPI."}