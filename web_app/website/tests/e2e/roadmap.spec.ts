import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { implementedMilestones, roadmap } from "../../content/roadmap";

for (const width of [320, 375, 390, 768, 1024, 1200, 1280, 1440]) {
  test(`roadmap and navigation reflow at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/#roadmap");
    const section = page.locator("#roadmap");
    for (const item of [...implementedMilestones, ...roadmap])
      await expect(
        section.getByRole("heading", { name: item.title, exact: true }),
      ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    if (width >= 1200) {
      const nav = page.getByRole("navigation", { name: "Primary" });
      const brand = await page
        .getByRole("link", { name: "Omnix home" })
        .boundingBox();
      const box = await nav.boundingBox();
      expect(box!.x).toBeGreaterThan(brand!.x + brand!.width);
      expect(box!.x + box!.width).toBeLessThanOrEqual(width);
    }
    if (width === 390 || width === 1440)
      await section.screenshot({
        path: test.info().outputPath(`roadmap-${width}.png`),
      });
  });
}

test("Roadmap navigation supports keyboard activation and destination focus", async ({
  page,
}) => {
  await page.goto("/");
  const menu = page.getByRole("button", { name: "Menu", exact: true });
  const mobile = await menu.isVisible();
  if (mobile) {
    await menu.focus();
    await page.keyboard.press("Enter");
  } else await page.keyboard.press("Tab");
  const nav = page.getByRole("navigation", {
    name: mobile ? "Mobile" : "Primary",
  });
  const link = nav.getByRole("link", { name: "Roadmap", exact: true });
  await link.focus();
  await expect(link).toHaveCSS("outline-style", "solid");
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/#roadmap$/);
  await expect(page.locator("#roadmap")).toBeFocused();
  if (mobile) await expect(nav).toBeHidden();
});

test("roadmap status is explicit and accessible with reduced motion and forced colors", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/#roadmap");
  const section = page.locator("#roadmap");
  await expect(section.getByText("Available", { exact: true })).toHaveCount(
    implementedMilestones.length,
  );
  await expect(section.getByText("Roadmap", { exact: true })).toHaveCount(
    roadmap.length,
  );
  expect(
    await section.evaluate(
      (node) => node.getAnimations({ subtree: true }).length,
    ),
  ).toBe(0);
  expect(
    (
      await new AxeBuilder({ page })
        .include("#roadmap")
        .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.emulateMedia({ forcedColors: "active" });
  for (const badge of await section.getByText("Roadmap", { exact: true }).all())
    await expect(badge).toHaveCSS("border-top-style", "dashed");
  await section.getByRole("link").first().focus();
  await expect(section.getByRole("link").first()).toHaveCSS(
    "outline-style",
    "solid",
  );
});

test("the complete roadmap remains readable without JavaScript", async ({
  browser,
}) => {
  const context = await browser.newContext({
    javaScriptEnabled: false,
    viewport: { width: 320, height: 900 },
  });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:3100/#roadmap");
  const section = page.locator("#roadmap");
  await expect(section.getByRole("listitem")).toHaveCount(
    implementedMilestones.length + roadmap.length,
  );
  await expect(
    section.getByText(/Source availability does not establish/),
  ).toBeVisible();
  await expect(
    page
      .getByRole("navigation", { name: "Mobile" })
      .getByRole("link", { name: "Roadmap", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await context.close();
});
