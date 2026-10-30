import { expect, test } from "@playwright/test";

test("loads prefixed assets and canonical metadata without browser errors", async ({
  page,
}) => {
  const errors: string[] = [];
  const assets: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type()))
      errors.push(message.text());
  });
  page.on("response", (response) => {
    if (response.request().resourceType() === "document") return;
    assets.push(new URL(response.url()).pathname);
    if (!response.ok()) errors.push(`${response.status()} ${response.url()}`);
  });
  await page.goto("/cli");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Build software with an AI engineering team.",
  );
  const logo = page.getByRole("link", { name: "Omnix home" }).locator("img");
  await expect(logo).toBeVisible();
  expect(
    await logo.evaluate(
      (image: HTMLImageElement) => image.complete && image.naturalWidth > 0,
    ),
  ).toBe(true);
  await page.evaluate(() => document.fonts.ready);
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
    "href",
    "https://www.omni-x.co.in/cli",
  );
  await expect(page.locator('meta[property="og:url"]')).toHaveAttribute(
    "content",
    "https://www.omni-x.co.in/cli",
  );
  await expect(page.locator('meta[property="og:image"]')).toHaveAttribute(
    "content",
    "https://www.omni-x.co.in/cli/social-preview",
  );
  await expect(page.locator('meta[name="twitter:image"]')).toHaveAttribute(
    "content",
    "https://www.omni-x.co.in/cli/social-preview",
  );
  expect(
    await page.locator('link[rel="icon"]').first().getAttribute("href"),
  ).toContain("/cli/brand/omnix-logo.png");
  expect(assets.length).toBeGreaterThan(3);
  expect(assets.every((path) => path.startsWith("/cli/"))).toBe(true);
  expect(errors).toEqual([]);
});

test("keeps mobile navigation and installation anchors inside the CLI zone", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/cli");
  const trigger = page.locator('button[aria-controls="mobile-navigation"]');
  await trigger.click();
  await expect(trigger).toHaveAttribute("aria-expanded", "true");
  await page.keyboard.press("Escape");
  await expect(trigger).toBeFocused();
  await expect(trigger).toHaveAttribute("aria-expanded", "false");
  await page.getByRole("link", { name: "Preview installation" }).click();
  await expect(page).toHaveURL(/\/cli#download$/);
  await expect(page.locator("#download")).toBeFocused();
  await expect(page.getByRole("link", { name: "Omnix home" })).toHaveAttribute(
    "href",
    "/cli",
  );
});

test("serves scoped metadata, brand, and review headers with preview indexing", async ({
  request,
}) => {
  const home = await request.get("/cli");
  expect(home.status()).toBe(200);
  expect(home.headers()["x-robots-tag"]).toBe("noindex, nofollow");
  expect(home.headers()["content-security-policy"]).toContain(
    "default-src 'self'",
  );
  const review = await request.get("/cli/design-system");
  expect(review.status()).toBe(200);
  expect(review.headers()["x-robots-tag"]).toBe("noindex, nofollow");
  const robots = await request.get("/cli/robots.txt");
  expect(robots.status()).toBe(200);
  expect(await robots.text()).toContain("Disallow: /cli$");
  expect(await robots.text()).toContain("Disallow: /cli/");
  const sitemap = await request.get("/cli/sitemap.xml");
  expect(sitemap.status()).toBe(200);
  expect(await sitemap.text()).not.toContain("<loc>");
  for (const path of ["/cli/brand/omnix-logo.png", "/cli/social-preview"]) {
    const image = await request.get(path);
    expect(image.status()).toBe(200);
    expect(image.headers()["content-type"]).toContain("image/png");
  }
});

test("404 recovery returns to the CLI zone instead of the parent app", async ({
  page,
}) => {
  const response = await page.goto("/cli/this-page-does-not-exist");
  expect(response?.status()).toBe(404);
  await expect(page.locator('meta[name="robots"]').first()).toHaveAttribute(
    "content",
    /noindex/,
  );
  const recovery = page.getByRole("link", { name: "Return to Omnix" });
  await expect(recovery).toHaveAttribute("href", "/cli");
  await recovery.focus();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/cli$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Build software with an AI engineering team.",
  );
});

test("does not claim the parent site's root routes", async ({ request }) => {
  for (const path of [
    "/",
    "/design-system",
    "/brand/omnix-logo.png",
    "/social-preview",
  ])
    expect((await request.get(path)).status()).toBe(404);
});
