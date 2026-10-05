import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { terminalCommands, terminalSteps } from "../../content/hero";

for (const width of [320, 375, 390, 768, 1024, 1280, 1440]) {
  test(`hero reflows at ${width}px with a complete terminal`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    const heading = page.getByRole("heading", { level: 1 });
    await expect(heading).toBeVisible();
    const terminal = page.getByRole("figure", {
      name: "From goal to blueprint",
    });
    for (const step of terminalSteps)
      await expect(terminal.getByText(step.command)).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    const nav = page.getByRole("navigation", { name: "Primary" });
    if (width >= 1200) {
      await expect(nav).toBeVisible();
      await expect(page.getByRole("button", { name: "Menu" })).toBeHidden();
      await nav.getByRole("link", { name: "CLI", exact: true }).click();
      expect(
        (await page.locator("#cli").boundingBox())!.y,
      ).toBeGreaterThanOrEqual(
        (await page.locator("header").boundingBox())!.height,
      );
      await page.goto("/");
    } else {
      await expect(nav).toBeHidden();
      await expect(page.getByRole("button", { name: "Menu" })).toBeVisible();
    }
    await page.screenshot({
      path: test.info().outputPath(`hero-${width}.png`),
      fullPage: true,
    });
  });
}

test("mobile menu supports keyboard, Escape, destination focus and outside tabbing", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  const menu = page.getByRole("button", { name: "Menu", exact: true });
  await menu.focus();
  await page.keyboard.press("Enter");
  const close = page.getByRole("button", { name: "Close menu" });
  await expect(close).toHaveAttribute("aria-expanded", "true");
  await page.keyboard.press("Tab");
  const nav = page.getByRole("navigation", { name: "Mobile" });
  await expect(nav.getByRole("link", { name: "Product" })).toBeFocused();
  await expect(nav.getByRole("link", { name: "Product" })).toHaveCSS(
    "outline-style",
    "solid",
  );
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.screenshot({
    path: test.info().outputPath("menu-open.png"),
    fullPage: true,
  });
  await page.keyboard.press("Escape");
  await expect(menu).toBeFocused();
  await expect(menu).toHaveAttribute("aria-expanded", "false");
  await menu.click();
  await nav.getByRole("link", { name: "CLI", exact: true }).click();
  await expect(page.locator("#cli")).toBeFocused();
  await expect(nav).toBeHidden();
  await menu.click();
  await nav.getByRole("link", { name: "Source preview" }).focus();
  await page.keyboard.press("Tab");
  await expect(nav).toBeHidden();
  await expect(
    page.getByRole("link", { name: "View source preview" }),
  ).toBeFocused();
  await menu.click();
  await close.click();
  await expect(menu).toBeFocused();
});

test("responsive menu resets when switching to desktop", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("button", { name: "Menu" }).click();
  await page.setViewportSize({ width: 1100, height: 900 });
  await expect(page.getByRole("button", { name: "Menu" })).toBeFocused();
  await page.getByRole("button", { name: "Menu" }).click();
  await page
    .getByRole("navigation", { name: "Mobile" })
    .getByRole("link", { name: "Product" })
    .focus();
  await page.setViewportSize({ width: 1280, height: 900 });
  await expect(page.getByRole("link", { name: "Omnix home" })).toBeFocused();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole("button", { name: "Menu" })).toHaveAttribute(
    "aria-expanded",
    "false",
  );
});

test("static reduced-motion workflow copies exact commands and retains source CTAs", async ({
  page,
  context,
}) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const terminal = page.getByRole("figure", { name: "From goal to blueprint" });
  for (const step of terminalSteps)
    await expect(terminal.getByText(step.command)).toBeVisible();
  expect(
    await terminal.evaluate(
      (node) => node.getAnimations({ subtree: true }).length,
    ),
  ).toBe(0);
  await expect(
    page.getByRole("link", { name: /download|install/i }),
  ).toHaveCount(0);
  const copy = page.getByRole("button", { name: "Copy commands" });
  await copy.focus();
  await page.keyboard.press("Enter");
  await expect(terminal.getByRole("status")).toHaveText("Copied to clipboard.");
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(
    terminalCommands,
  );
});

test("mobile navigation and all commands are readable without JavaScript", async ({
  browser,
}) => {
  const context = await browser.newContext({
    javaScriptEnabled: false,
    viewport: { width: 375, height: 812 },
  });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:3100/");
  const nav = page.getByRole("navigation", { name: "Mobile" });
  await expect(
    nav.getByRole("link", { name: "CLI", exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Menu" })).toBeHidden();
  const terminal = page.getByRole("figure", { name: "From goal to blueprint" });
  await expect(terminal.locator("pre code")).toHaveCount(5);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await context.close();
});

test("primary hover and forced-color keyboard focus remain legible", async ({
  page,
}) => {
  await page.goto("/");
  const primary = page.getByRole("link", { name: "View source preview" });
  await primary.hover();
  await expect(primary).toHaveCSS("background-color", "rgb(178, 245, 223)");
  await page.screenshot({
    path: test.info().outputPath("hero-hover.png"),
    fullPage: true,
  });
  await page.emulateMedia({ forcedColors: "active" });
  await primary.focus();
  await expect(primary).toHaveCSS("outline-style", "solid");
  await expect(primary).toHaveCSS("border-top-style", "solid");
});
