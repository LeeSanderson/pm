import { existsSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { spawn, spawnSync } from "node:child_process";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(scriptDir, "..");
const backendDir = path.resolve(frontendDir, "..", "backend");
const frontendDistDir = path.join(frontendDir, "out");
const port = process.env.PM_E2E_PORT ?? "4100";

const syncResult = spawnSync("uv", ["sync", "--dev"], {
  cwd: backendDir,
  stdio: "inherit",
});

if (syncResult.status !== 0) {
  process.exit(syncResult.status ?? 1);
}

const pythonExecutable =
  process.platform === "win32"
    ? path.join(backendDir, ".venv", "Scripts", "python.exe")
    : path.join(backendDir, ".venv", "bin", "python");

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
      FRONTEND_DIST_DIR: frontendDistDir,
    },
    stdio: "inherit",
  }
);

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