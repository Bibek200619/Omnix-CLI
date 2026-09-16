import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

export default async function setupBrowserData() {
  if (process.platform !== "darwin") return;

  // macOS 27 protects Firefox's normal app-data directory even with a fresh
  // -profile. Keep test browser metadata separate from personal browser data.
  // https://bugzilla.mozilla.org/show_bug.cgi?id=2060476
  const directory = await mkdtemp(join(tmpdir(), "omnix-firefox-data-"));
  const previous = process.env.MOZ_APP_DATA;
  process.env.MOZ_APP_DATA = directory;

  return async () => {
    if (previous === undefined) delete process.env.MOZ_APP_DATA;
    else process.env.MOZ_APP_DATA = previous;
    await rm(directory, { recursive: true, force: true });
  };
}
