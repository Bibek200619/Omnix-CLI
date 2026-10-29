import { spawnSync } from "node:child_process";

const npm = process.env.npm_execpath;
if (!npm) throw new Error("Run this rehearsal with npm run test:subpath.");

const env = {
  ...process.env,
  NEXT_PUBLIC_BASE_PATH: "/cli",
  SITE_URL: "https://www.omni-x.co.in",
  SITE_INDEXABLE: "false",
};

for (const args of [
  ["run", "build"],
  ["exec", "--", "playwright", "test", "--config=playwright.subpath.config.ts"],
]) {
  const result = spawnSync(process.execPath, [npm, ...args], {
    env,
    stdio: "inherit",
  });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status ?? 1);
}
