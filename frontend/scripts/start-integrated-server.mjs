import { existsSync, mkdirSync, rmSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { spawn, spawnSync } from "node:child_process";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(scriptDir, "..");
const backendDir = path.resolve(frontendDir, "..", "backend");
const frontendDistDir = path.join(frontendDir, "out");
const e2eDataDir = path.join(frontendDir, ".playwright");
const e2eDbPath = path.join(e2eDataDir, "e2e.sqlite3");
const port = process.env.PM_E2E_PORT ?? "4100";
const pythonExecutable =
  process.platform === "win32"
    ? path.join(backendDir, ".venv", "Scripts", "python.exe")
    : path.join(backendDir, ".venv", "bin", "python");

mkdirSync(e2eDataDir, { recursive: true });
rmSync(e2eDbPath, { force: true });

const uvVersionCheck = spawnSync("uv", ["--version"], {
  cwd: backendDir,
  stdio: "ignore",
});

if (uvVersionCheck.status === 0) {
  const syncResult = spawnSync("uv", ["sync", "--dev"], {
    cwd: backendDir,
    stdio: "inherit",
  });

  if (syncResult.status !== 0) {
    process.exit(syncResult.status ?? 1);
  }
} else {
  console.log("uv not found on PATH. Reusing the existing backend virtualenv for Playwright.");
}

if (!existsSync(pythonExecutable)) {
  console.error(`Backend Python executable not found at ${pythonExecutable}`);
  process.exit(1);
}

const server = spawn(
  pythonExecutable,
  ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", port],
  {
    cwd: backendDir,
    env: {
      ...process.env,
      DB_PATH: e2eDbPath,
      ENABLE_TEST_API: "1",
      FRONTEND_DIST_DIR: frontendDistDir,
    },
    stdio: "inherit",
  }
);

console.log(`Using e2e database at ${e2eDbPath}`);

const stopServer = (signal) => {
  if (!server.killed) {
    server.kill(signal);
  }
};

process.on("SIGINT", () => stopServer("SIGINT"));
process.on("SIGTERM", () => stopServer("SIGTERM"));
process.on("exit", () => stopServer("SIGTERM"));

server.on("exit", (code) => {
  process.exit(code ?? 0);
});