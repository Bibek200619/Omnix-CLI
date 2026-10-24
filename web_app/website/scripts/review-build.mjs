import { readFile, readdir } from "node:fs/promises";
import { join } from "node:path";
import { gzipSync } from "node:zlib";

async function filesIn(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  return (
    await Promise.all(
      entries.map((entry) => {
        const path = join(directory, entry.name);
        return entry.isDirectory() ? filesIn(path) : [path];
      }),
    )
  ).flat();
}

// Only high-confidence credential shapes; never print matching values.
const credentials = [
  /\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,})\b/,
  /\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{40,}\b/,
  /\bAKIA[0-9A-Z]{16}\b/,
  /-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----/,
  /(?:postgres(?:ql)?|mongodb(?:\+srv)?|mysql):\/\/[^\s/:]+:[^\s/@]+@/,
];
const sourceFiles = (
  await Promise.all(["app", "components", "content", "lib"].map(filesIn))
).flat();
const browserFiles = await filesIn(".next/static");
const textFiles = [...sourceFiles, ...browserFiles].filter((path) =>
  /\.(?:[cm]?[jt]sx?|css|json)$/.test(path),
);
const findings = [];
let javascriptBytes = 0;
let javascriptGzipBytes = 0;
for (const path of textFiles) {
  const data = await readFile(path);
  if (credentials.some((pattern) => pattern.test(data.toString("utf8"))))
    findings.push(path);
  if (path.startsWith(".next/static/") && path.endsWith(".js")) {
    javascriptBytes += data.length;
    javascriptGzipBytes += gzipSync(data).length;
  }
}
console.log(
  JSON.stringify(
    {
      scannedTextFiles: textFiles.length,
      credentialPatternMatches: findings.length,
      matchingFiles: findings,
      allRouteJavascriptBytes: javascriptBytes,
      allRouteJavascriptGzipBytes: javascriptGzipBytes,
      scope:
        "First-party source and all generated browser assets; gzip sums are not per-page transfer size.",
    },
    null,
    2,
  ),
);
if (findings.length) process.exitCode = 1;
