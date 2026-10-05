import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import Home from "@/app/page";
import { commands } from "@/content/commands";
import { architectFlow, commandGroups } from "@/content/product-proof";
import { providers } from "@/content/providers";

beforeEach(() => {
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({
      matches: true,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  );
});

afterEach(() => vi.unstubAllGlobals());

it("renders all registered commands once in source-backed groups", () => {
  render(<Home />);
  const cli = screen.getByRole("region", {
    name: "The CLI is the product surface.",
  });
  const grouped = commandGroups.flatMap((group) => group.commands);
  expect(grouped.map((command) => command.name).sort()).toEqual(
    commands.map((command) => command.name).sort(),
  );
  expect(within(cli).getAllByRole("listitem")).toHaveLength(commands.length);
  for (const command of commands)
    expect(within(cli).getByText(command.syntax)).toBeInTheDocument();
});

it("keeps live and roadmap provider states explicit in text", () => {
  render(<Home />);
  const section = screen.getByRole("region", {
    name: "Roles choose models through one provider layer.",
  });
  const rows = within(section).getAllByRole("row").slice(1);
  expect(rows).toHaveLength(providers.length);
  for (const provider of providers) {
    const row = rows.find((candidate) =>
      within(candidate).queryByText(provider.name),
    );
    expect(row).toBeDefined();
    expect(
      within(row!).getByText(
        provider.status === "live-adapter" ? "Available" : "Roadmap",
      ),
    ).toBeVisible();
  }
});

it("shows local memory boundaries and the complete Architect process", () => {
  render(<Home />);
  const memory = screen.getByRole("region", {
    name: "Project context lives with the project.",
  });
  expect(within(memory).getByText("project.memory.json")).toBeVisible();
  const memoryFile = within(memory).getByRole("region", {
    name: "project.memory.json",
  });
  expect(within(memoryFile).queryByText("Blueprint")).not.toBeInTheDocument();
  expect(within(memoryFile).getByText(/reports their count/)).toBeVisible();
  expect(
    within(memory).getByRole("region", { name: "project.blueprint.json" }),
  ).toHaveTextContent("omnix blueprint");
  expect(within(memory).getByText(/not a cloud account/i)).toBeVisible();
  expect(within(memory).getByText(/does not automatically/i)).toBeVisible();

  const architect = screen.getByRole("region", {
    name: "The Architect evolves a source of truth.",
  });
  expect(within(architect).getAllByRole("listitem")).toHaveLength(
    architectFlow.length,
  );
  expect(
    within(architect).getByText(/not runtime code validation/i),
  ).toBeVisible();
});

it("copies an exact command through the shared control", async () => {
  const writeText = vi.fn().mockResolvedValue(undefined);
  Object.defineProperty(navigator, "clipboard", {
    configurable: true,
    value: { writeText },
  });
  render(<Home />);
  const cli = screen.getByRole("region", {
    name: "The CLI is the product surface.",
  });
  const firstRow = within(cli).getAllByRole("listitem")[0]!;
  fireEvent.click(
    within(firstRow).getByRole("button", { name: "Copy command" }),
  );
  expect(
    await within(firstRow).findByText("Copied to clipboard."),
  ).toBeVisible();
  expect(writeText).toHaveBeenCalledWith(commands[0].syntax);
});
