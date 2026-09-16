import { fireEvent, render, screen, within } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { OrchestrationJourney } from "@/components/orchestration/orchestration-journey";
import { journey, journeySteps } from "@/content/journey";
import { roadmap } from "@/content/roadmap";

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

it("keeps the complete ordered story readable while visitors select a stage", () => {
  render(<OrchestrationJourney />);
  const route = screen.getByRole("list", {
    name: "From goal to saved blueprint",
  });
  const titles = within(route).getAllByRole("heading", { level: 3 });
  expect(titles.map((heading) => heading.textContent?.slice(1))).toEqual(
    journeySteps.map((step) => step.title),
  );
  fireEvent.click(screen.getByRole("button", { name: "Architect Agent" }));
  expect(
    screen.getByRole("button", { name: "Architect Agent" }),
  ).toHaveAttribute("aria-current", "step");
  expect(screen.getByRole("status")).toHaveTextContent(
    "Stage 4 of 5: Architect Agent",
  );
  expect(
    screen.getByRole("region", { name: "You explicitly invoke the Architect" }),
  ).toHaveTextContent(journeySteps[3].detail);
  for (const step of journeySteps)
    expect(screen.getByText(step.summary)).toBeVisible();
  expect(screen.getAllByRole("button", { current: "step" })).toHaveLength(1);
});

it("moves forward, back, and restarts without treating exploration as execution", () => {
  render(<OrchestrationJourney />);
  expect(screen.getByRole("button", { name: "Previous stage" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Next stage" }));
  expect(screen.getByRole("status")).toHaveTextContent(
    "Stage 2 of 5: Master Agent",
  );
  fireEvent.click(screen.getByRole("button", { name: "Previous stage" }));
  expect(screen.getByRole("status")).toHaveTextContent(
    "Stage 1 of 5: Your goal",
  );
  fireEvent.click(screen.getByRole("button", { name: "Validated blueprint" }));
  fireEvent.click(screen.getByRole("button", { name: "Restart journey" }));
  expect(screen.getByRole("status")).toHaveTextContent(
    "Stage 1 of 5: Your goal",
  );
  expect(screen.getByText(/no commands run in your browser/)).toBeVisible();
});

it("separates available source workflows from unimplemented provider adapters", () => {
  render(<OrchestrationJourney />);
  expect(screen.getByText(journey.availability)).toBeVisible();
  expect(screen.getByText(journey.boundary)).toBeVisible();
  expect(screen.getByText(journey.buildLimit)).toBeVisible();
  const future = screen.getByRole("complementary", {
    name: "More provider choices",
  });
  expect(within(future).getByText("Roadmap")).toBeVisible();
  expect(within(future).queryByText("Available")).not.toBeInTheDocument();
  expect(
    within(future)
      .getAllByRole("listitem")
      .map((item) => item.textContent),
  ).toEqual(roadmap.map((item) => item.title));
  expect(
    screen.queryByRole("link", { name: /download|install/i }),
  ).not.toBeInTheDocument();
});

it("links narrative claims to actual source files and command handlers", () => {
  const root = resolve(process.cwd(), "../..");
  for (const step of journeySteps) {
    expect(
      readFileSync(resolve(root, step.evidence), "utf8").length,
    ).toBeGreaterThan(0);
  }
  const master = readFileSync(resolve(root, journeySteps[1].evidence), "utf8");
  expect(master).toContain("record_agent_output");
  expect(master).not.toContain("ArchitectAgent");
  const architect = readFileSync(
    resolve(root, journeySteps[3].evidence),
    "utf8",
  );
  expect(architect).toContain(
    "validate_architecture_blueprint(evolved_blueprint)",
  );
  expect(architect).toContain("save_blueprint(evolved_blueprint)");
  expect(
    architect.indexOf("validate_architecture_blueprint(evolved_blueprint)"),
  ).toBeLessThan(architect.indexOf("save_blueprint(evolved_blueprint)"));
  const build = readFileSync(resolve(root, journey.buildEvidence), "utf8");
  for (const phase of [
    "architect",
    "planner",
    "execution",
    "integration",
    "qa",
    "repair",
  ]) {
    expect(build).toContain(`run_${phase}`);
  }
});
