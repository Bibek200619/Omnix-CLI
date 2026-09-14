import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { agents } from "@/content/agents";
import { commands } from "@/content/commands";
import { providers } from "@/content/providers";
import { roadmap } from "@/content/roadmap";
import { product } from "@/lib/constants";
import { releaseSnapshot } from "@/lib/release";

describe("product truth against the repository", () => {
  const readCli = (path: string) =>
    readFileSync(resolve(process.cwd(), "../../ai-cli", path), "utf8");

  it("contains exactly the registered CLI commands", () => {
    const main = readCli("omnix_cli/cli/main.py");
    const registered = [...main.matchAll(/app\.command\("([^"]+)"\)/g)]
      .map((match) => match[1])
      .sort();
    expect(commands.map((command) => command.name).sort()).toEqual(registered);
  });

  it("uses package version and Python requirement without claiming a stable release", () => {
    const packageInfo = readCli("pyproject.toml");
    expect(packageInfo).toContain(`version = "${product.version}"`);
    expect(packageInfo).toContain(
      `requires-python = ">=${product.minimumPython}"`,
    );
    expect(releaseSnapshot.state.kind).toBe("none");
  });

  it("backs each available preview agent with an implementation", () => {
    for (const agent of agents) {
      expect(agent.status).toBe("available");
      expect(agent.scope).toBe("source-preview");
      expect(readCli(`omnix_cli/agents/${agent.id}/agent.py`)).toMatch(
        /async def (handle_message|run|execute_task|integrate|evaluate|repair)\(/,
      );
    }
  });

  it("keeps unimplemented provider generation on the roadmap", () => {
    expect(
      providers
        .filter((provider) => provider.status === "live-adapter")
        .map((provider) => provider.id),
    ).toEqual(["openai"]);
    for (const provider of providers.filter(
      (provider) => provider.status === "boundary-only",
    )) {
      expect(readCli(`omnix_cli/providers/${provider.id}.py`)).toContain(
        "live generation is not implemented",
      );
      expect(
        roadmap.find((item) => item.id === `${provider.id}-generation`)?.status,
      ).toBe("roadmap");
    }
  });

  it("preserves the official logo byte-for-byte", () => {
    const original = readFileSync(
      resolve(process.cwd(), "../ref /logo/img.png"),
    );
    const copy = readFileSync(
      resolve(process.cwd(), "public/brand/omnix-logo.png"),
    );
    expect(copy.equals(original)).toBe(true);
  });
});
