import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("review controls have native keyboard behavior and readable state", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (["warning", "error"].includes(message.type()))
      errors.push(message.text());
  });
  await page.goto("/design-system");
  const primary = page.getByRole("button", { name: "Primary action" });
  await primary.focus();
  await expect(primary).toHaveCSS("outline-style", "solid");
  await page.keyboard.press("Enter");
  await expect(page.getByText("Primary action activated.")).toBeVisible();
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("button", { name: "Secondary action" }),
  ).toBeFocused();
  await page.keyboard.press("Space");
  await expect(page.getByText("Secondary action activated.")).toBeVisible();
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("button", { name: "Ghost action" }),
  ).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Jump to code examples" }),
  ).toBeFocused();
  await expect(
    page.getByRole("button", { name: "Disabled action" }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: /Loading example/ }),
  ).toHaveAttribute("aria-busy", "true");
  await expect(page.getByText("Roadmap", { exact: true })).toHaveCSS(
    "border-top-style",
    "dashed",
  );
  for (const button of await page.getByRole("button").all())
    expect((await button.boundingBox())?.height).toBeGreaterThanOrEqual(44);
  expect(errors).toEqual([]);
  await page.screenshot({
    path: test.info().outputPath("primitives.png"),
    fullPage: true,
  });
});

test("copies exact code using the real browser clipboard", async ({
  page,
  context,
}) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto("/design-system");
  const button = page.getByRole("button", { name: "Copy command" });
  await button.focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByText("Copied to clipboard.", { exact: true }),
  ).toBeVisible();
  // Read only the test value just written by this isolated test browser.
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(
    "omnix models\nomnix blueprint",
  );
});

test("clipboard denial selects manual text and permits retry", async ({
  page,
}) => {
  await page.addInitScript(() => {
    let calls = 0;
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: async () => {
          if (++calls === 1) throw new Error("Test denial");
        },
      },
    });
  });
  await page.goto("/design-system");
  const copy = page.getByRole("button", { name: "Copy command" });
  await copy.click();
  const manual = page.getByRole("textbox", { name: "Text to copy manually" });
  await expect(manual).toBeFocused();
  await expect(manual).toHaveValue("omnix models\nomnix blueprint");
  expect(
    await manual.evaluate((node) => (node as HTMLTextAreaElement).selectionEnd),
  ).toBe("omnix models\nomnix blueprint".length);
  await expect(page.getByText(/Automatic copy is unavailable/)).toBeVisible();
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(results.violations).toEqual([]);
  await page.screenshot({
    path: test.info().outputPath("copy-fallback.png"),
    fullPage: true,
  });
  await copy.click();
  await expect(
    page.getByText("Copied to clipboard.", { exact: true }),
  ).toBeVisible();
  await expect(manual).toHaveCount(0);
});

test("code scrolls by keyboard while narrow text reflows", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/design-system");
  const code = page.getByRole("region", { name: "Explicit workspace code" });
  await code.focus();
  await page.keyboard.press("ArrowRight");
  await expect
    .poll(() => code.evaluate((node) => node.scrollLeft))
    .toBeGreaterThan(0);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.addStyleTag({ content: "html { font-size: 200%; }" });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await page.screenshot({
    path: test.info().outputPath("primitives-reflow.png"),
    fullPage: true,
  });
});

test("review passes axe and keeps control focus in forced colors", async ({
  page,
}) => {
  await page.goto("/design-system");
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.emulateMedia({ forcedColors: "active" });
  const button = page.getByRole("button", { name: "Primary action" });
  await button.focus();
  await expect(button).toHaveCSS("outline-style", "solid");
  await expect(button).toHaveCSS("border-top-style", "solid");
});

test("code and status remain readable without JavaScript", async ({
  browser,
}) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:3100/design-system");
  await expect(
    page.getByRole("region", { name: "Inspect a project code" }),
  ).toHaveText("omnix models\nomnix blueprint");
  await expect(page.getByText("Roadmap", { exact: true })).toBeVisible();
  await context.close();
});
