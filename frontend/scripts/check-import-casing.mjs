import { promises as fs } from "fs";
import path from "path";
import ts from "typescript";
import { fileURLToPath } from "url";

const filePath = fileURLToPath(import.meta.url);
const FRONTEND_ROOT = path.resolve(filePath, "..", "..");
const SRC_ROOT = path.join(FRONTEND_ROOT, "src");
const TS_CONFIG_PATH = path.join(FRONTEND_ROOT, "tsconfig.json");
const ALLOWED_EXTENSIONS = [".ts", ".tsx", ".js", ".jsx"];
const IGNORE_DIRS = new Set(["node_modules", "dist", ".git"]);

function loadTsConfig() {
  const configFile = ts.readConfigFile(TS_CONFIG_PATH, ts.sys.readFile);
  if (configFile.error) {
    throw new Error(
      `Failed to read tsconfig.json: ${configFile.error.messageText}`,
    );
  }
  const parsed = ts.parseJsonConfigFileContent(
    configFile.config,
    ts.sys,
    FRONTEND_ROOT,
  );
  return parsed.options;
}

const compilerOptions = loadTsConfig();

async function* walkFiles(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    if (IGNORE_DIRS.has(entry.name)) continue;
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      yield* walkFiles(fullPath);
    } else if (ALLOWED_EXTENSIONS.includes(path.extname(entry.name))) {
      yield fullPath;
    }
  }
}

async function resolveRealPathCase(targetPath) {
  if (!path.isAbsolute(targetPath)) {
    throw new Error(`Expected absolute path, received: ${targetPath}`);
  }
  const parts = targetPath.split(path.sep).filter(Boolean);
  let current = path.sep;

  for (const part of parts) {
    const entries = await fs.readdir(current, { withFileTypes: true });
    const match = entries.find(
      (entry) => entry.name.toLowerCase() === part.toLowerCase(),
    );
    if (!match) {
      return null;
    }
    current = path.join(current, match.name);
  }
  return current;
}

function getScriptKind(filename) {
  const ext = path.extname(filename).toLowerCase();
  switch (ext) {
    case ".ts":
      return ts.ScriptKind.TS;
    case ".tsx":
      return ts.ScriptKind.TSX;
    case ".js":
      return ts.ScriptKind.JS;
    case ".jsx":
      return ts.ScriptKind.JSX;
    default:
      return ts.ScriptKind.TS;
  }
}

async function checkFile(filePath) {
  const content = await fs.readFile(filePath, "utf8");
  const sourceFile = ts.createSourceFile(
    filePath,
    content,
    ts.ScriptTarget.Latest,
    true,
    getScriptKind(filePath),
  );

  const issues = [];

  function visit(node) {
    if (
      ts.isImportDeclaration(node) ||
      ts.isExportDeclaration(node) ||
      ts.isImportEqualsDeclaration(node)
    ) {
      const moduleSpecifier =
        node.moduleSpecifier && ts.isStringLiteral(node.moduleSpecifier)
          ? node.moduleSpecifier.text
          : null;

      if (moduleSpecifier) {
        issues.push({
          moduleSpecifier,
          node,
        });
      }
    }
    ts.forEachChild(node, visit);
  }

  visit(sourceFile);

  const results = [];

  for (const { moduleSpecifier, node } of issues) {
    const resolution = ts.resolveModuleName(
      moduleSpecifier,
      filePath,
      compilerOptions,
      ts.sys,
    );
    const resolvedFileName = resolution.resolvedModule?.resolvedFileName;
    if (!resolvedFileName) {
      continue; // skip unresolved imports; Vite/tsc will catch separately
    }
    const ext = path.extname(resolvedFileName).toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      continue; // ignore non-source imports like css/assets
    }
    if (resolvedFileName.includes("node_modules")) {
      continue; // skip third-party packages
    }

    const realPath = await resolveRealPathCase(resolvedFileName);
    if (realPath && realPath !== resolvedFileName) {
      const { line, character } = sourceFile.getLineAndCharacterOfPosition(
        node.getStart(),
      );
      results.push({
        file: filePath,
        line: line + 1,
        column: character + 1,
        importPath: moduleSpecifier,
        diskPath: realPath,
      });
    }
  }

  return results;
}

async function main() {
  let totalIssues = 0;
  for await (const file of walkFiles(SRC_ROOT)) {
    const issues = await checkFile(file);
    totalIssues += issues.length;
    for (const issue of issues) {
      const relativeFile = path.relative(FRONTEND_ROOT, issue.file);
      console.log(
        `${relativeFile}:${issue.line}:${issue.column} - import "${issue.importPath}" casing differs from disk path ${path.relative(
          FRONTEND_ROOT,
          issue.diskPath,
        )}`,
      );
    }
  }

  if (totalIssues > 0) {
    console.error(`Found ${totalIssues} import casing issue(s).`);
    process.exitCode = 1;
  } else {
    console.log("No import casing issues found.");
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});

