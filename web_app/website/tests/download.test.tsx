import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { DownloadAction } from "@/components/marketing/download-action";

const originalShow = Object.getOwnPropertyDescriptor(
  HTMLDialogElement.prototype,
  "showModal",
);
const originalClose = Object.getOwnPropertyDescriptor(
  HTMLDialogElement.prototype,
  "close",
);

beforeEach(() => {
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({ addEventListener: vi.fn(), removeEventListener: vi.fn() })),
  );
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", {
    configurable: true,
    value: vi.fn(function (this: HTMLDialogElement) {
      this.setAttribute("open", "");
    }),
  });
  Object.defineProperty(HTMLDialogElement.prototype, "close", {
    configurable: true,
    value: vi.fn(function (this: HTMLDialogElement) {
      this.removeAttribute("open");
      this.dispatchEvent(new Event("close"));
    }),
  });
});
afterEach(() => {
  vi.unstubAllGlobals();
  for (const [name, descriptor] of [
    ["showModal", originalShow],
    ["close", originalClose],
  ] as const) {
    if (descriptor)
      Object.defineProperty(HTMLDialogElement.prototype, name, descriptor);
    else Reflect.deleteProperty(HTMLDialogElement.prototype, name);
  }
});

it("offers CLI source setup and a disabled planned app, then returns focus on close", () => {
  render(<DownloadAction />);
  const trigger = screen.getByRole("button", { name: "Download Omnix" });
  expect(trigger).toHaveAttribute("aria-haspopup", "dialog");
  fireEvent.click(trigger);
  const dialog = screen.getByRole("dialog", { name: "Get Omnix" });
  expect(dialog).toHaveTextContent("The Omnix app is planned.");
  expect(within(dialog).getByText("Source preview")).toBeVisible();
  expect(
    within(dialog).getByRole("button", { name: "Coming later" }),
  ).toBeDisabled();
  expect(
    within(dialog).getByRole("link", { name: "View CLI setup" }),
  ).toHaveFocus();
  expect(within(dialog).getAllByRole("link")).toHaveLength(1);
  fireEvent.keyDown(dialog, { key: "Tab" });
  expect(within(dialog).getByRole("button", { name: "Close" })).toHaveFocus();
  fireEvent.keyDown(dialog, { key: "Tab", shiftKey: true });
  expect(
    within(dialog).getByRole("link", { name: "View CLI setup" }),
  ).toHaveFocus();
  fireEvent.click(within(dialog).getByRole("button", { name: "Close" }));
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(trigger).toHaveFocus();
});

it("closes and focuses real source setup rather than offering an app binary", () => {
  render(
    <>
      <DownloadAction />
      <section id="download" tabIndex={-1}>
        Source setup
      </section>
    </>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Download Omnix" }));
  const dialog = screen.getByRole("dialog", { name: "Get Omnix" });
  const setup = within(dialog).getByRole("link", { name: "View CLI setup" });
  expect(setup).toHaveAttribute("href", "#download");
  fireEvent.click(setup);
  expect(document.getElementById("download")).toHaveFocus();
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});
