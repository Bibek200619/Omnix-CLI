import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { sourceSetup } from "../../content/install";

for (const width of [320, 375, 390, 768, 1024, 1280, 1440]) {
  test(`source setup reflows at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/#download");
    const section = page.locator("#download");
    await expect(
      section.getByRole("heading", { name: "Try the source preview." }),
    ).toBeVisible();
    await expect(
      section.getByRole("figure", { name: sourceSetup.label }),
    ).toContainText(sourceSetup.command);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    if (width === 390 || width === 1440)
      await section.screenshot({
        path: test.info().outputPath(`install-${width}.png`),
      });
  });
}

test("preview navigation reaches setup and keyboard copying preserves exact commands", async ({
  page,
  context,
}) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto("/");
  await page.getByRole("link", { name: "Preview installation" }).focus();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/#download$/);
  await expect(page.locator("#download")).toBeFocused();
  const setup = page.getByRole("figure", { name: sourceSetup.label });
  const copy = setup.getByRole("button", { name: "Copy setup commands" });
  await copy.focus();
  await page.keyboard.press("Enter");
  await expect(setup.getByRole("status")).toHaveText("Copied to clipboard.");
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(
    sourceSetup.command,
  );
});

test("setup help is accessible with reduced motion and has recovery links", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/#download");
  const section = page.locator("#download");
  const help = section.getByText("Setup help", { exact: true });
  await help.focus();
  await page.keyboard.press("Enter");
  await expect(
    section.getByRole("link", { name: "open a GitHub issue" }),
  ).toBeVisible();
  expect(
    (
      await new AxeBuilder({ page })
        .include("#download")
        .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
});

test("source setup and help remain usable without JavaScript", async ({
  browser,
}) => {
  const context = await browser.newContext({
    javaScriptEnabled: false,
    viewport: { width: 375, height: 812 },
  });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:3100/#download");
  const section = page.locator("#download");
  await expect(
    section.getByRole("figure", { name: sourceSetup.label }),
  ).toContainText(sourceSetup.command);
  await section.getByText("Setup help", { exact: true }).click();
  await expect(
    section.getByRole("link", { name: "open a GitHub issue" }),
  ).toBeVisible();
  await context.close();
});
