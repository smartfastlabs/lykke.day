import { writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { execSync } from "child_process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const distDir = join(__dirname, "../dist");
const versionPath = join(distDir, "version.json");

function getBuildId() {
  if (process.env.NETLIFY_COMMIT_REF) {
    return process.env.NETLIFY_COMMIT_REF;
  }
  try {
    return execSync("git rev-parse HEAD", { encoding: "utf8" }).trim();
  } catch {
    return String(Date.now());
  }
}

if (!existsSync(distDir)) {
  console.error("inject-version: dist/ not found. Run after vite build.");
  process.exit(1);
}

const buildId = getBuildId();
const payload = JSON.stringify({ buildId });
writeFileSync(versionPath, payload, "utf8");
console.log("inject-version: wrote version.json with buildId:", buildId);
