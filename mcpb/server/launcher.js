#!/usr/bin/env node

import { spawn } from "node:child_process";
import { existsSync, mkdirSync } from "node:fs";
import { dirname, delimiter } from "node:path";

function splitCommands(value) {
  return value
    .split(delimiter)
    .map((item) => item.trim())
    .filter(Boolean);
}

function pythonCandidates() {
  const configured = process.env.KINOCUT_MCPB_PYTHON?.trim();
  if (configured) {
    return [configured];
  }
  if (process.platform === "win32") {
    return ["py", "python"];
  }
  return ["python3", "python"];
}

function buildEnv() {
  const env = { ...process.env };
  const ffmpegPath = env.KINOCUT_MCPB_FFMPEG?.trim();
  if (ffmpegPath) {
    env.PATH = `${dirname(ffmpegPath)}${delimiter}${env.PATH ?? ""}`;
  }
  const outputRoot = env.KINOCUT_MCPB_OUTPUT_ROOT?.trim();
  if (outputRoot && !existsSync(outputRoot)) {
    mkdirSync(outputRoot, { recursive: true });
  }
  return env;
}

function launch(command, env) {
  const args = command === "py" ? ["-3", "-m", "kinocut", "--mcp"] : ["-m", "kinocut", "--mcp"];
  return spawn(command, args, {
    stdio: "inherit",
    env,
    shell: false,
  });
}

const env = buildEnv();
const commands = pythonCandidates().flatMap(splitCommands);
let child = null;
let lastError = null;

for (const command of commands) {
  child = launch(command, env);
  const started = await new Promise((resolve) => {
    child.once("spawn", () => resolve(true));
    child.once("error", (error) => {
      lastError = error;
      resolve(false);
    });
  });
  if (started) {
    break;
  }
}

if (!child || child.exitCode !== null) {
  const detail = lastError ? ` (${lastError.message})` : "";
  console.error(
    "Unable to start Kinocut MCPB. Install Python 3.11+, install kinocut==1.7.0 in that environment, "
      + `or configure pythonExecutable.${detail}`,
  );
  process.exit(127);
}

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 1);
});
