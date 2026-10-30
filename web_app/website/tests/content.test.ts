import { existsSync, readFileSync } from "node:fs";
import { createHash } from "node:crypto";
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
    const registered = [...main.matchAll(/^app\.command\("([^"]+)"\)/gm)].map(
      (match) => match[1],
    );
    for (const [, appName, groupName] of main.matchAll(
      /^app\.add_typer\((\w+), name="([^"]+)"\)/gm,
    )) {
      const subcommands = new RegExp(
        `^${appName}\\.command\\("([^"]+)"\\)`,
        "gm",
      );
      for (const [, name] of main.matchAll(subcommands))
        registered.push(`${groupName} ${name}`);
    }
    expect(commands.map((command) => command.name).sort()).toEqual(
      registered.sort(),
    );
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

  it("preserves the official logo checksum and local reference when available", () => {
    const reference = resolve(process.cwd(), "../ref /logo/img.png");
    const copy = readFileSync(
      resolve(process.cwd(), "public/brand/omnix-logo.png"),
    );
    // Digest verified against the untouched official reference during discovery.
    expect(createHash("sha256").update(copy).digest("hex")).toBe(
      "0af83834b37d5f54cd88a0703d9d3077f7ae909b5b0136be5fd3802d0ddd5115",
    );
    if (existsSync(reference))
      expect(copy.equals(readFileSync(reference))).toBe(true);
  });
});
