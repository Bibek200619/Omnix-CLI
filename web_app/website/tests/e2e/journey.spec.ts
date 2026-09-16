import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { journey, journeySteps } from "../../content/journey";

for (const width of [320, 375, 390, 768, 1024, 1280, 1440]) {
  test(`journey has a connected readable route at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/#how-it-works");
    const section = page.getByRole("region", { name: journey.title });
    const route = section.getByRole("list", {
      name: "From goal to saved blueprint",
    });
    for (const step of journeySteps)
      await expect(route.getByText(step.summary)).toBeVisible();
    const steps = route.locator(":scope > li");
    const first = (await steps.nth(0).boundingBox())!;
    const second = (await steps.nth(1).boundingBox())!;
    if (width >= 1200) {
      expect(second.y).toBe(first.y);
      expect(second.x).toBeGreaterThan(first.x + first.width);
    } else {
      expect(second.x).toBe(first.x);
      expect(second.y).toBeGreaterThan(first.y);
    }
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await section.screenshot({
      path: test.info().outputPath(`journey-${width}.png`),
    });
  });
}

test("stage controls support keyboard selection, progression, and restart", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/#how-it-works");
  const next = page.getByRole("button", { name: "Next stage" });
  await next.focus();
  await page.keyboard.press("Enter");
  await expect(next).toBeFocused();
  await expect(next).toHaveCSS("outline-style", "solid");
  await expect(
    page.getByRole("button", { name: "Master Agent", exact: true }),
  ).toHaveAttribute("aria-current", "step");
  const architect = page.getByRole("button", {
    name: "Architect Agent",
    exact: true,
  });
  await architect.focus();
  await page.keyboard.press("Space");
  await expect(architect).toBeFocused();
  await expect(architect).toHaveAttribute("aria-current", "step");
  await expect(
    page.getByRole("region", { name: "You explicitly invoke the Architect" }),
  ).toContainText("API key");
  await next.click();
  await expect(
    page.getByRole("region", { name: "Read the saved result" }),
  ).toContainText("does not run, test, or deploy");
  await page.getByRole("button", { name: "Restart journey" }).click();
  await expect(
    page.getByRole("button", { name: "Previous stage" }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Your goal", exact: true }),
  ).toHaveAttribute("aria-current", "step");
  expect((await architect.boundingBox())!.height).toBeGreaterThanOrEqual(44);
});

test("mobile selection places detail beside its node and preserves selection on resize", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/#how-it-works");
  const architect = page.getByRole("button", {
    name: "Architect Agent",
    exact: true,
  });
  await architect.click();
  const explanation = page.getByRole("region", {
    name: "You explicitly invoke the Architect",
  });
  const node = page
    .getByRole("list", { name: "From goal to saved blueprint" })
    .locator(":scope > li")
    .nth(3);
  await expect(node.locator("#journey-explanation")).toBeVisible();
  await expect(explanation).toContainText("API key");
  await expect(page.getByRole("button", { name: "Next stage" })).toHaveCount(0);
  // Safari does not focus buttons on pointer activation. Explicitly establish
  // keyboard focus before verifying that a responsive layout change preserves it.
  await architect.focus();
  await expect(architect).toBeFocused();
  await page.setViewportSize({ width: 1440, height: 900 });
  await expect(architect).toHaveAttribute("aria-current", "step");
  await expect(page.locator("#journey-explanation")).toHaveCount(1);
  await expect(
    page.getByRole("region", { name: journey.title }).getByRole("status"),
  ).toHaveText("Stage 4 of 5: Architect Agent");
  await expect(architect).toBeFocused();
});

test("reduced motion retains all stages, provider states, and accessible selection", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/#how-it-works");
  await page
    .getByRole("button", { name: "Architect Agent", exact: true })
    .click();
  const section = page.getByRole("region", { name: journey.title });
  expect(
    await section.evaluate(
      (node) => node.getAnimations({ subtree: true }).length,
    ),
  ).toBe(0);
  for (const step of journeySteps)
    await expect(section.getByText(step.summary)).toBeVisible();
  const future = section.getByRole("complementary", {
    name: "More provider choices",
  });
  await expect(future).toHaveCSS("border-left-style", "dashed");
  await expect(future.getByText("Roadmap", { exact: true })).toBeVisible();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
});

test("the full story survives no JavaScript at mobile width", async ({
  browser,
}) => {
  const context = await browser.newContext({
    javaScriptEnabled: false,
    viewport: { width: 375, height: 812 },
  });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:3100/#how-it-works");
  const section = page.getByRole("region", { name: journey.title });
  for (const step of journeySteps) {
    await expect(
      section.getByRole("heading", { name: new RegExp(step.title) }),
    ).toBeVisible();
    await expect(section.getByText(step.summary)).toBeVisible();
  }
  await expect(section.getByRole("button")).toHaveCount(0);
  await expect(section.getByText(journey.boundary)).toBeVisible();
  await expect(section.getByText("Roadmap", { exact: true })).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await context.close();
});

test("How it works navigation reaches an unobscured and focused section", async ({
  page,
}) => {
  await page.goto("/");
  const menu = page.getByRole("button", { name: "Menu", exact: true });
  if (await menu.isVisible()) {
    await menu.click();
    await page
      .getByRole("navigation", { name: "Mobile" })
      .getByRole("link", { name: "How it works" })
      .click();
    await expect(page.locator("#how-it-works")).toBeFocused();
    await expect(menu).toHaveAttribute("aria-expanded", "false");
  } else {
    await page
      .getByRole("navigation", { name: "Primary" })
      .getByRole("link", { name: "How it works" })
      .click();
    expect(
      (await page.locator("#how-it-works").boundingBox())!.y,
    ).toBeGreaterThanOrEqual(
      (await page.locator("header").boundingBox())!.height,
    );
  }
  await expect(page).toHaveURL(/#how-it-works$/);
});

test("forced colors retains current-step outlines and dashed roadmap boundaries", async ({
  page,
}) => {
  await page.emulateMedia({ forcedColors: "active" });
  await page.goto("/#how-it-works");
  const stage = page.getByRole("button", {
    name: "Project context",
    exact: true,
  });
  await stage.focus();
  await page.keyboard.press("Enter");
  await expect(stage).toHaveAttribute("aria-current", "step");
  await expect(stage).toHaveCSS("outline-style", "solid");
  await expect(stage.locator("span")).toHaveCSS("outline-width", "2px");
  await expect(
    page.getByRole("complementary", { name: "More provider choices" }),
  ).toHaveCSS("border-left-style", "dashed");
  await page
    .getByRole("region", { name: journey.title })
    .screenshot({ path: test.info().outputPath("journey-forced-colors.png") });
});
