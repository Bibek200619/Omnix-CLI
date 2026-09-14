import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import Home from "@/app/page";
import { links } from "@/lib/constants";

it("renders a semantic source preview without a download claim", () => {
  render(<Home />);
  expect(screen.getByRole("main")).toHaveAttribute("id", "main");
  expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
    "Omnix CLI is taking shape.",
  );
  expect(
    screen.getByRole("link", { name: "Explore the source on GitHub" }),
  ).toHaveAttribute("href", links.source);
  expect(screen.getByText(/Python 3.12/)).toBeVisible();
  expect(
    screen.queryByRole("link", { name: /download|install/i }),
  ).not.toBeInTheDocument();
});
