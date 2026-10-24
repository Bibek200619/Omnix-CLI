import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { render, screen, within } from "@testing-library/react";
import { expect, it } from "vitest";
import { RoadmapSection } from "@/components/marketing/roadmap-section";
import { agents } from "@/content/agents";
import { implementedMilestones, roadmap } from "@/content/roadmap";
import { repository } from "@/lib/constants";

it("keeps implemented agents in the source-preview timeline, separate from future adapters", () => {
  render(<RoadmapSection />);
  const [implemented, future] = screen.getAllByRole("list");
  const implementedRows = within(implemented!).getAllByRole("listitem");
  expect(implementedRows).toHaveLength(implementedMilestones.length);
  for (const row of implementedRows) {
    expect(within(row).getByText("Available")).toBeVisible();
    expect(within(row).queryByText("Roadmap")).not.toBeInTheDocument();
  }
  const futureRows = within(future!).getAllByRole("listitem");
  expect(futureRows).toHaveLength(roadmap.length);
  for (const item of roadmap) {
    const row = futureRows.find((row) => within(row).queryByText(item.title));
    expect(within(row!).getByText("Roadmap")).toBeVisible();
    expect(within(row!).queryByText("Available")).not.toBeInTheDocument();
  }
  expect(screen.getByText(/Available means implemented/)).toBeVisible();
  expect(screen.getByText(/do not prove that an application/)).toBeVisible();
  expect(screen.getByText("No delivery dates are announced.")).toBeVisible();

  const evidence = implementedMilestones.flatMap((item) => [...item.evidence]);
  for (const agent of agents)
    expect(evidence).toContain(`agents/${agent.id}/agent.py`);
  for (const file of evidence)
    expect(
      readFileSync(
        resolve(process.cwd(), "../../ai-cli/omnix_cli", file),
        "utf8",
      ),
    ).not.toHaveLength(0);
});

it("links each implemented milestone to its canonical source", () => {
  render(<RoadmapSection />);
  for (const milestone of implementedMilestones) {
    expect(
      screen.getByRole("link", { name: `${milestone.title} implementation` }),
    ).toHaveAttribute(
      "href",
      `${repository.url}/blob/main/ai-cli/omnix_cli/${milestone.evidence[0]}`,
    );
  }
});
