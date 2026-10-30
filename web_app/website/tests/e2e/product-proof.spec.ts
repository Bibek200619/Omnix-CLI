import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { commands } from "../../content/commands";

for (const width of [320, 390, 768, 1024, 1280, 1440]) {
  test(`product proof reflows without page overflow at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/#memory");
    for (const id of ["memory", "providers", "cli", "architect"])
      await expect(page.locator(`#${id}`)).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    if (width === 390 || width === 1440) {
      await page.screenshot({
        fullPage: true,
        path: test.info().outputPath(`product-proof-${width}.png`),
      });
      for (const id of ["memory", "providers", "cli", "architect"]) {
        await page.locator(`#${id}`).screenshot({
          path: test.info().outputPath(`${id}-${width}.png`),
        });
      }
    }
  });
}

test("command explorer exposes all commands and copies exact syntax", async ({
  page,
  context,
}) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto("/#cli");
  const cli = page.getByRole("region", {
    name: "Command explorer.",
  });
  await cli.getByText("Preview orchestration commands").click();
  await expect(cli.getByText("omnix build GOAL")).toBeVisible();
  await expect(cli.getByRole("listitem")).toHaveCount(commands.length);
  await expect(
    cli.getByText("registered commands", { exact: false }),
  ).toHaveText(`${commands.length} registered commands`);
  const firstRow = cli.getByRole("listitem").first();
  await firstRow.getByRole("button", { name: "Copy command" }).click();
  await expect(firstRow.getByRole("status")).toHaveText("Copied to clipboard.");
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(
    commands[0].syntax,
  );
  const history = commands.find(
    (command) => command.name === "sessions history",
  )!;
  const historyRow = cli
    .getByRole("listitem")
    .filter({ hasText: history.syntax });
  await expect(historyRow).toContainText("offline");
  await historyRow.getByRole("button", { name: "Copy syntax" }).click();
  await expect(historyRow.getByRole("status")).toHaveText(
    "Copied to clipboard.",
  );
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(
    history.syntax,
  );
  await expect(cli).toContainText("compatible server with sessions enabled");
});

test("provider and Architect claims remain accessible and explicit", async ({
  page,
}) => {
  await page.goto("/#providers");
  const providers = page.getByRole("region", {
    name: "Know what each role is configured to use.",
  });
  await expect(providers.getByText("Available", { exact: true })).toHaveCount(
    1,
  );
  await expect(providers.getByText("Roadmap", { exact: true })).toHaveCount(4);
  await expect(
    page.getByRole("region", {
      name: "Architecture you explicitly ask for.",
    }),
  ).toContainText("not runtime code validation");
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
});

test("CLI navigation reaches the command explorer", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  await page
    .getByRole("navigation", { name: "Primary" })
    .getByRole("link", { name: "CLI", exact: true })
    .click();
  await expect(page).toHaveURL(/#cli$/);
  await expect(page.locator("#cli")).toBeFocused();
});

test("command disclosure works without JavaScript", async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:3100/#cli");
  const disclosure = page.locator("#cli details").filter({
    has: page.getByText("Preview orchestration commands", { exact: true }),
  });
  await disclosure.locator("summary").focus();
  await page.keyboard.press("Enter");
  await expect(disclosure.getByText("omnix build GOAL")).toBeVisible();
  await page.keyboard.press("Enter");
  await expect(disclosure.getByText("omnix build GOAL")).toBeHidden();
  await context.close();
});
