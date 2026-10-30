import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import Home from "@/components/marketing/home-page";
import { links } from "@/lib/constants";
import { hero } from "@/content/hero";
import { terminalDemo } from "@/content/terminal-demo";

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
    screen.getByRole("link", { name: "Preview installation" }),
  ).toHaveAttribute("href", "#download");
  expect(screen.getAllByText(/Python 3.12/).length).toBeGreaterThan(0);
  expect(
    screen.queryByRole("link", { name: /^(download|install) omnix$/i }),
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

it("renders the source-verified terminal and selects every real transcript", () => {
  render(<Home />);
  const terminal = screen.getByRole("region", {
    name: "A real starting point.",
  });
  for (const state of terminalDemo) {
    const tab = within(terminal).getByRole("tab", { name: state.label });
    fireEvent.click(tab);
    expect(tab).toHaveAttribute("aria-selected", "true");
    const panel = within(terminal).getByRole("tabpanel", { name: state.label });
    expect(panel.querySelector("code")?.textContent).toBe(
      `$ ${state.command}\n${state.output}`,
    );
    expect(within(panel).getByText(state.caption)).toBeVisible();
  }
  expect(
    within(terminal).getByText(/Source-verified transcript/),
  ).toBeVisible();
  expect(terminal).not.toHaveAttribute("aria-live");
});

it("supports tab keyboard progression, wrapping and Home/End", () => {
  render(<Home />);
  const terminal = screen.getByRole("region", {
    name: "A real starting point.",
  });
  const tabs = within(terminal).getAllByRole("tab");
  tabs[0]!.focus();
  fireEvent.keyDown(tabs[0]!, { key: "ArrowRight" });
  expect(tabs[1]).toHaveFocus();
  expect(tabs[1]).toHaveAttribute("aria-selected", "true");
  fireEvent.keyDown(tabs[1]!, { key: "End" });
  expect(tabs[2]).toHaveFocus();
  fireEvent.keyDown(tabs[2]!, { key: "ArrowRight" });
  expect(tabs[0]).toHaveFocus();
  fireEvent.keyDown(tabs[0]!, { key: "ArrowLeft" });
  expect(tabs[2]).toHaveFocus();
  fireEvent.keyDown(tabs[2]!, { key: "Home" });
  expect(tabs[0]).toHaveFocus();
});
