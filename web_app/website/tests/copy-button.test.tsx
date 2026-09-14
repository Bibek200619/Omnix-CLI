import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { CopyButton } from "@/components/ui/copy-button";

const clipboardDescriptor = Object.getOwnPropertyDescriptor(
  navigator,
  "clipboard",
);
afterEach(() => {
  if (clipboardDescriptor)
    Object.defineProperty(navigator, "clipboard", clipboardDescriptor);
  else Reflect.deleteProperty(navigator, "clipboard");
});

function mockClipboard(writeText: ReturnType<typeof vi.fn> | undefined) {
  Object.defineProperty(navigator, "clipboard", {
    configurable: true,
    value: writeText ? { writeText } : undefined,
  });
}

describe("CopyButton", () => {
  it("copies exact text only on activation and announces success", async () => {
    const text = "omnix models\n  omnix blueprint";
    const write = vi.fn().mockResolvedValue(undefined);
    mockClipboard(write);
    render(<CopyButton text={text} />);
    expect(write).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Copy command" }));
    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent(
        "Copied to clipboard.",
      ),
    );
    expect(write).toHaveBeenCalledExactlyOnceWith(text);
    expect(screen.getByRole("button", { name: "Copy command" })).toBeEnabled();
  });

  it("blocks repeated requests while a write is pending", async () => {
    let finish!: () => void;
    const write = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          finish = resolve;
        }),
    );
    mockClipboard(write);
    render(<CopyButton text="omnix models" />);
    const button = screen.getByRole("button");
    fireEvent.click(button);
    fireEvent.click(button);
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
    expect(write).toHaveBeenCalledOnce();
    await act(async () => finish());
    expect(button).toBeEnabled();
  });

  it.each(["denied", "missing"])(
    "offers exact selected manual text when clipboard is %s",
    async (mode) => {
      const text = 'omnix chat "Record this goal"\nomnix goals';
      mockClipboard(
        mode === "missing"
          ? undefined
          : vi
              .fn()
              .mockRejectedValue(new DOMException("Denied", "NotAllowedError")),
      );
      render(<CopyButton text={text} />);
      fireEvent.click(screen.getByRole("button"));
      const field = await screen.findByRole("textbox", {
        name: "Text to copy manually",
      });
      expect(field).toHaveValue(text);
      expect(field).toHaveFocus();
      expect(field).toHaveAttribute("readonly");
      expect((field as HTMLTextAreaElement).selectionStart).toBe(0);
      expect((field as HTMLTextAreaElement).selectionEnd).toBe(text.length);
      expect(screen.getByRole("status")).toHaveTextContent("Ctrl+C or ⌘C");
      expect(screen.getByRole("status")).not.toHaveTextContent(
        "Copied to clipboard.",
      );
    },
  );

  it("recovers from a denied request on retry", async () => {
    const write = vi
      .fn()
      .mockRejectedValueOnce(new Error("Denied"))
      .mockResolvedValue(undefined);
    mockClipboard(write);
    render(<CopyButton text="omnix models" />);
    fireEvent.click(screen.getByRole("button"));
    await screen.findByRole("textbox");
    fireEvent.click(screen.getByRole("button"));
    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent(
        "Copied to clipboard.",
      ),
    );
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(write).toHaveBeenCalledTimes(2);
  });

  it("does not carry success feedback to a different command", async () => {
    mockClipboard(vi.fn().mockResolvedValue(undefined));
    const { rerender } = render(<CopyButton text="omnix models" />);
    fireEvent.click(screen.getByRole("button"));
    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent("Copied"),
    );
    rerender(<CopyButton text="omnix blueprint" />);
    expect(screen.getByRole("status")).toBeEmptyDOMElement();
  });
});
