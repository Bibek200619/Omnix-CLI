import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";
import { terminalDemo } from "../../content/terminal-demo";

test("download dialog contains focus, dismisses, and reaches real CLI setup", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  const trigger = page
    .getByRole("navigation", { name: "Primary" })
    .getByRole("button", { name: "Download Omnix" });
  await trigger.focus();
  await page.keyboard.press("Enter");
  const dialog = page.getByRole("dialog", { name: "Get Omnix" });
  await expect(page.locator("dialog:modal")).toHaveCount(1);
  const setup = dialog.getByRole("link", { name: "View CLI setup" });
  const close = dialog.getByRole("button", { name: "Close", exact: true });
  await expect(setup).toBeFocused();
  await expect(setup).toHaveAttribute("href", "#download");
  await expect(
    dialog.getByRole("button", { name: "Coming later" }),
  ).toBeDisabled();
  await expect(dialog).toContainText("The Omnix app is planned.");
  await expect(dialog.getByRole("link")).toHaveCount(1);
  await page.keyboard.press("Tab");
  await expect(close).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(setup).toBeFocused();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(trigger).toBeFocused();
  await trigger.click();
  await close.click();
  await expect(trigger).toBeFocused();
  await trigger.click();
  await setup.click();
  await expect(dialog).toBeHidden();
  await expect(page).toHaveURL(/#download$/);
  await expect(page.locator("#download")).toBeFocused();
  await expect(page.locator("#download")).toContainText("uv sync --frozen");
});

test("mobile download remains distinct from the navigation disclosure", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  const menu = page.locator('button[aria-controls="mobile-navigation"]');
  await menu.click();
  const nav = page.getByRole("navigation", { name: "Mobile", exact: true });
  const trigger = nav.getByRole("button", { name: "Download Omnix" });
  await trigger.click();
  const dialog = page.getByRole("dialog", { name: "Get Omnix" });
  await expect(dialog).toBeVisible();
  expect((await dialog.boundingBox())!.width).toBeLessThanOrEqual(390);
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(trigger).toBeFocused();
  await expect(menu).toHaveAttribute("aria-expanded", "true");
  await trigger.click();
  await dialog.getByRole("link", { name: "View CLI setup" }).click();
  await expect(page.locator("#download")).toBeFocused();
  await expect(menu).toHaveAttribute("aria-expanded", "false");
});

test("terminal tabs expose source-verified output with keyboard and reduced motion", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const demo = page.locator("#hero-cli");
  await demo.getByRole("tab", { name: "Initialize" }).focus();
  await page.keyboard.press("ArrowRight");
  await expect(demo.getByRole("tab", { name: "Assign models" })).toBeFocused();
  const models = demo.getByRole("tabpanel", { name: "Assign models" });
  await expect(models).toContainText(terminalDemo[1].output);
  await expect(models).toContainText("<unset>");
  await page.keyboard.press("End");
  await expect(
    demo.getByRole("tab", { name: "Inspect blueprint" }),
  ).toHaveAttribute("aria-selected", "true");
  await expect(
    demo.getByRole("tabpanel", { name: "Inspect blueprint" }),
  ).toContainText(terminalDemo[2].output);
  await page.keyboard.press("ArrowRight");
  await expect(demo.getByRole("tab", { name: "Initialize" })).toBeFocused();
  expect(
    await page
      .locator("#product")
      .evaluate((element) => element.getAnimations({ subtree: true }).length),
  ).toBe(0);
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
});

for (const [from, to] of [
  [390, 768],
  [390, 1440],
  [1440, 390],
] as const) {
  test(`header dialogs release the page when their responsive trigger disappears: ${from} to ${to}`, async ({
    page,
  }) => {
    await page.setViewportSize({ width: from, height: 900 });
    await page.goto("/");
    if (from < 1200)
      await page.getByRole("button", { name: "Menu", exact: true }).click();
    const nav = page.getByRole("navigation", {
      name: from < 1200 ? "Mobile" : "Primary",
      exact: true,
    });
    await nav.getByRole("button", { name: "Download Omnix" }).click();
    await expect(page.getByRole("dialog", { name: "Get Omnix" })).toBeVisible();
    await page.setViewportSize({ width: to, height: 900 });
    await expect(page.locator("dialog[open]")).toHaveCount(0);
    const focusTarget =
      from < 1200 && to < 1200
        ? page.getByRole("button", { name: "Menu", exact: true })
        : page.getByRole("link", { name: "Omnix home" });
    await expect(focusTarget).toBeFocused();
    expect(
      await page
        .locator("html")
        .evaluate((element) => getComputedStyle(element).overflow),
    ).not.toBe("hidden");
  });
}

test("download source fallback works without JavaScript", async ({
  browser,
}) => {
  const context = await browser.newContext({
    javaScriptEnabled: false,
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:3100/");
  const fallback = page
    .getByRole("navigation", { name: "Primary" })
    .getByRole("link", { name: "Download Omnix" });
  await fallback.click();
  await expect(page).toHaveURL(/#download$/);
  await expect(page.locator("#download")).toContainText("uv sync --frozen");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await context.close();
});

test("approved opening, progression and availability produce reviewable browser views", async ({
  page,
}, testInfo) => {
  test.skip(
    testInfo.project.name !== "chromium",
    "One artifact set; interaction tests run in every engine.",
  );
  const output = resolve("output/playwright");
  await mkdir(output, { recursive: true });
  for (const width of [320, 375, 390, 768, 1024, 1280, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    await page.evaluate(() => document.fonts.ready);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    if (width === 1440 || width === 390) {
      await page.screenshot({
        path: resolve(output, `omnix-${width}-opening.png`),
      });
      await page.screenshot({
        path: resolve(output, `omnix-${width}-full.png`),
        fullPage: true,
      });
      if (width === 390)
        await page.getByRole("button", { name: "Menu", exact: true }).click();
      const nav = page.getByRole("navigation", {
        name: width === 390 ? "Mobile" : "Primary",
        exact: true,
      });
      await nav.getByRole("button", { name: "Download Omnix" }).click();
      await page.screenshot({
        path: resolve(output, `omnix-${width}-download.png`),
      });
      await page.keyboard.press("Escape");
    }
  }
});
