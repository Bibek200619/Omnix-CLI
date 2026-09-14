import { createRef } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CodeBlock } from "@/components/ui/code-block";
import { Container } from "@/components/ui/container";
import { Link } from "@/components/ui/link";
import { Section } from "@/components/ui/section";

describe("native control contracts", () => {
  it("defaults to a non-submit button, forwards refs, and preserves form semantics", () => {
    const submit = vi.fn((event: React.FormEvent) => event.preventDefault());
    const ref = createRef<HTMLButtonElement>();
    render(
      <form onSubmit={submit}>
        <Button ref={ref}>Inspect</Button>
        <Button type="submit">Save</Button>
      </form>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Inspect" }));
    expect(submit).not.toHaveBeenCalled();
    expect(ref.current).toBe(screen.getByRole("button", { name: "Inspect" }));
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(submit).toHaveBeenCalledOnce();
  });

  it.each(["primary", "secondary", "ghost"] as const)(
    "blocks disabled and loading %s actions",
    (variant) => {
      const click = vi.fn();
      const { rerender } = render(
        <Button variant={variant} onClick={click} disabled>
          Save
        </Button>,
      );
      fireEvent.click(screen.getByRole("button"));
      expect(click).not.toHaveBeenCalled();
      rerender(
        <Button variant={variant} onClick={click} loading>
          Save
        </Button>,
      );
      const button = screen.getByRole("button", { name: "Save Working…" });
      expect(button).toBeDisabled();
      expect(button).toHaveAttribute("aria-busy", "true");
      fireEvent.click(button);
      expect(click).not.toHaveBeenCalled();
    },
  );

  it("uses real links and announces new-tab navigation", () => {
    render(
      <>
        <Link href="#code">Read code</Link>
        <Link
          href="https://github.com/Bibek200619/Omnix-CLI"
          newTab
          rel="nofollow"
        >
          Source
        </Link>
      </>,
    );
    expect(screen.getByRole("link", { name: "Read code" })).toHaveAttribute(
      "href",
      "#code",
    );
    expect(screen.getByRole("link", { name: "Read code" })).not.toHaveAttribute(
      "target",
    );
    const source = screen.getByRole("link", {
      name: /Source.*opens in a new tab/,
    });
    expect(source).toHaveAttribute("target", "_blank");
    expect(source).toHaveAttribute("rel", "nofollow noopener noreferrer");
  });

  it.each([
    "javascript:alert(1)",
    "//evil.test",
    "data:text/html,test",
    "/\\evil.test",
    "https://example.com\n/path",
  ])("rejects unsafe navigation %s", (href) => {
    expect(() => render(<Link href={href}>Unsafe</Link>)).toThrow(/HTTPS/);
  });
});

describe("content semantics", () => {
  it("labels sections with their headings and forwards container refs", () => {
    const ref = createRef<HTMLDivElement>();
    render(
      <Container ref={ref} width="prose">
        <Section id="memory" title="Project memory">
          <p>Context persists.</p>
          <Section
            id="decisions"
            title="Decisions"
            headingLevel={3}
            spacing="compact"
          >
            Recorded locally.
          </Section>
        </Section>
      </Container>,
    );
    expect(ref.current).toContainElement(
      screen.getByRole("region", { name: "Project memory" }),
    );
    expect(
      screen.getByRole("heading", { level: 3, name: "Decisions" }),
    ).toBeVisible();
  });

  it("renders status as text, without pretending badges are actions", () => {
    render(
      <>
        <Badge status="available" />
        <Badge status="roadmap" />
        <Badge status="preview" />
        <Badge status="version" version="0.1.0" />
      </>,
    );
    for (const label of ["Available", "Roadmap", "Preview", "Version 0.1.0"])
      expect(screen.getByText(label)).toBeVisible();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("preserves whitespace and treats code as text, not HTML", () => {
    const code = '<script>alert("test")</script>\n  omnix models';
    const { container } = render(<CodeBlock label="Example" code={code} />);
    expect(
      screen.getByRole("region", { name: "Example code" }),
    ).toHaveAttribute("tabindex", "0");
    expect(container.querySelector("pre code")?.textContent).toBe(code);
    expect(container.querySelector("script")).toBeNull();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
