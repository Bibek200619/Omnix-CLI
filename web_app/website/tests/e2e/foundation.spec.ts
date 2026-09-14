import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("loads the hero, local logo and fonts with a clean console", async ({
  page,
}) => {
  const errors: string[] = [];
  const failures: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type()))
      errors.push(message.text());
  });
  page.on("requestfailed", (request) => failures.push(request.url()));
  const response = await page.goto("/");
  expect(response?.status()).toBe(200);
  await expect(page).toHaveTitle(/Omnix CLI/);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(
    page.getByRole("link", { name: "View on GitHub" }),
  ).toHaveAttribute("href", "https://github.com/Bibek200619/Omnix-CLI");
  const image = page.locator("header img");
  await expect(image).toBeVisible();
  expect(
    await image.evaluate((node) => (node as HTMLImageElement).naturalWidth),
  ).toBeGreaterThan(0);
  await page.evaluate(() => document.fonts.ready);
  expect(
    await page.evaluate(
      () =>
        [...document.fonts].filter((font) => font.status === "loaded").length,
    ),
  ).toBeGreaterThanOrEqual(2);
  expect(errors).toEqual([]);
  expect(failures).toEqual([]);
  await page.screenshot({
    path: test.info().outputPath("foundation.png"),
    fullPage: true,
  });
});

test("supports keyboard focus and skip navigation", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("Tab");
  const skip = page.getByRole("link", { name: "Skip to content" });
  await expect(skip).toBeFocused();
  await expect(skip).toBeInViewport();
  await expect(skip).toHaveCSS("outline-style", "solid");
  await page.keyboard.press("Enter");
  await expect(page.getByRole("main")).toBeFocused();
  await page.keyboard.press("Tab");
  const source = page.getByRole("link", {
    name: "View source preview",
  });
  await expect(source).toBeFocused();
  await expect(source).toHaveCSS("outline-width", "2px");
  expect((await source.boundingBox())?.height).toBeGreaterThanOrEqual(44);
});

test("has no axe WCAG AA violations", async ({ page }) => {
  await page.goto("/");
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(results.violations).toEqual([]);
});

test("reflows at 320px and enlarged text with reduced motion", async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 800 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  // Text enlargement complements the narrow viewport reflow check.
  await page.addStyleTag({ content: "html { font-size: 200%; }" });
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  expect(
    await page.evaluate(() => getComputedStyle(document.body).animationName),
  ).toBe("none");
  await page.screenshot({
    path: test.info().outputPath("reflow.png"),
    fullPage: true,
  });
});

test("preserves navigation in forced colors", async ({ page }) => {
  await page.emulateMedia({ forcedColors: "active" });
  await page.goto("/");
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Skip to content" })).toHaveCSS(
    "outline-style",
    "solid",
  );
});

test("remains readable without JavaScript", async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:3100/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(
    page.getByRole("link", { name: "View on GitHub" }),
  ).toBeVisible();
  await context.close();
});

test("serves metadata and safe crawler defaults", async ({ request }) => {
  const page = await request.get("/");
  expect(page.headers()["x-content-type-options"]).toBe("nosniff");
  expect(page.headers()["x-robots-tag"]).toContain("noindex");
  expect(await page.text()).toContain(
    'name="robots" content="noindex, nofollow"',
  );
  const robots = await request.get("/robots.txt");
  expect(await robots.text()).toContain("Disallow: /");
  const sitemap = await request.get("/sitemap.xml");
  expect(sitemap.ok()).toBe(true);
  expect(await sitemap.text()).not.toContain("localhost");
  const logo = await request.get("/brand/omnix-logo.png");
  expect(logo.ok()).toBe(true);
});
