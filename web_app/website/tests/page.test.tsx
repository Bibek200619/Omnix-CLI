import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import Home from "@/app/page";
import { links } from "@/lib/constants";
import { hero, terminalCommands, terminalSteps } from "@/content/hero";

beforeEach(() => {
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({ addEventListener: vi.fn(), removeEventListener: vi.fn() })),
  );
});
afterEach(() => vi.unstubAllGlobals());

it("renders a semantic source preview without a download claim", () => {
  render(<Home />);
  expect(screen.getByRole("main")).toHaveAttribute("id", "main");
  expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
    hero.headline,
  );
  expect(screen.getByRole("link", { name: "View on GitHub" })).toHaveAttribute(
    "href",
    links.source,
  );
  expect(
    screen.getByRole("link", { name: "View source preview" }),
  ).toHaveAttribute("href", links.cliDocs);
  expect(screen.getAllByText(/Python 3.12/).length).toBeGreaterThan(0);
  expect(
    screen.queryByRole("link", { name: /download|install/i }),
  ).not.toBeInTheDocument();
});

it("only publishes navigation anchors that have real destinations", () => {
  render(<Home />);
  const nav = screen.getByRole("navigation", { name: "Primary" });
  for (const link of within(nav).getAllByRole("link")) {
    const href = link.getAttribute("href")!;
    if (href.startsWith("#"))
      expect(document.getElementById(href.slice(1))).not.toBeNull();
  }
  expect(screen.getByRole("link", { name: "Omnix home" })).toHaveAttribute(
    "aria-current",
    "page",
  );
});

it("opens and closes the mobile disclosure and restores focus on Escape", () => {
  render(<Home />);
  const menu = screen.getByRole("button", { name: "Menu" });
  expect(menu).toHaveAttribute("aria-expanded", "false");
  fireEvent.click(menu);
  expect(menu).toHaveAttribute("aria-expanded", "true");
  const nav = screen.getByRole("navigation", { name: "Mobile" });
  within(nav).getByRole("link", { name: "Product" }).focus();
  fireEvent.keyDown(nav, { key: "Escape" });
  expect(menu).toHaveAttribute("aria-expanded", "false");
  expect(menu).toHaveFocus();
  fireEvent.click(menu);
  fireEvent.click(screen.getByRole("button", { name: "Close menu" }));
  expect(menu).toHaveAttribute("aria-expanded", "false");
});

it("closes navigation and focuses the chosen anchor", () => {
  render(<Home />);
  fireEvent.click(screen.getByRole("button", { name: "Menu" }));
  fireEvent.click(
    within(screen.getByRole("navigation", { name: "Mobile" })).getByRole(
      "link",
      { name: "CLI" },
    ),
  );
  expect(document.getElementById("cli")).toHaveFocus();
  expect(screen.getByRole("button", { name: "Menu" })).toHaveAttribute(
    "aria-expanded",
    "false",
  );
});

it("renders the complete annotated workflow without invented CLI output", () => {
  render(<Home />);
  const terminal = screen.getByRole("figure", {
    name: "From goal to blueprint",
  });
  expect(within(terminal).getAllByRole("listitem")).toHaveLength(5);
  for (const step of terminalSteps)
    expect(within(terminal).getByText(step.command)).toBeVisible();
  expect(
    within(terminal).getByText(/website narration, not CLI output/),
  ).toBeVisible();
  expect(within(terminal).getByText(/OpenAI API key/)).toBeVisible();
  expect(terminalCommands).not.toMatch(
    /\$|Blueprint updated|Initialized Omnix/,
  );
  expect(terminal).not.toHaveAttribute("aria-live");
});
