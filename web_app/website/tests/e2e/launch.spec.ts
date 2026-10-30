import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const sections = [
  "product",
  "how-it-works",
  "memory",
  "providers",
  "cli",
  "architect",
  "roadmap",
  "download",
];

for (const width of [320, 375, 390, 768, 1024, 1280, 1440]) {
  test(`complete page remains readable at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    for (const id of sections)
      await expect(page.locator(`#${id}`)).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    if (width === 390 || width === 1440)
      await page.screenshot({
        fullPage: true,
        path: test.info().outputPath(`complete-${width}.png`),
      });
    if (width === 1440)
      await page.screenshot({
        path: test.info().outputPath("final-desktop.png"),
      });
  });
}

test("all sections and controls remain available with enlarged text", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/");
  await page.addStyleTag({ content: "html { font-size: 200%; }" });
  for (const id of sections) await expect(page.locator(`#${id}`)).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.getByRole("link", { name: "Preview installation" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#download")).toBeFocused();
});

test("browser accessibility tree exposes the complete story and state", async ({
  page,
}, testInfo) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const tree = await page.getByRole("main").ariaSnapshot();
  expect(tree).toContain("Build software with an AI engineering team.");
  expect(tree).toContain("Master Agent");
  expect(tree).toContain("Roadmap");
  expect(tree).toContain("Start with the source.");
  await testInfo.attach("accessibility-tree", {
    body: tree,
    contentType: "text/plain",
  });
  expect(
    (
      await new AxeBuilder({ page })
        .withTags([
          "wcag2a",
          "wcag2aa",
          "wcag21a",
          "wcag21aa",
          "wcag22a",
          "wcag22aa",
        ])
        .analyze()
    ).violations,
  ).toEqual([]);
});

test("production headers restrict resources and preview indexing", async ({
  request,
  page,
}) => {
  const response = await request.get("/");
  const csp = response.headers()["content-security-policy"]!;
  expect(csp).toContain("default-src 'self'");
  expect(csp).toContain("connect-src 'self'");
  expect(csp).toContain("form-action 'none'");
  expect(csp).toContain("frame-ancestors 'none'");
  expect(csp).not.toContain("unsafe-eval");
  expect(response.headers()["x-powered-by"]).toBeUndefined();
  expect(response.headers()["x-robots-tag"]).toBe("noindex, nofollow");
  const fixture = await request.get("/design-system");
  expect(fixture.headers()["x-robots-tag"]).toBe("noindex, nofollow");
  const image = await request.get("/social-preview");
  expect(image.status()).toBe(200);
  expect(image.headers()["content-type"]).toContain("image/png");
  expect((await image.body()).subarray(1, 4).toString()).toBe("PNG");
  await page.goto("/");
  const imageDetails = await page.evaluate(async () => {
    const social = new Image();
    social.src = "/social-preview";
    await social.decode();
    const canvas = document.createElement("canvas");
    canvas.width = social.naturalWidth;
    canvas.height = social.naturalHeight;
    const context = canvas.getContext("2d")!;
    context.drawImage(social, 0, 0);
    const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
    let brandPixels = 0;
    for (let i = 0; i < pixels.length; i += 4)
      if (pixels[i + 2]! > 100 && pixels[i + 2]! > pixels[i]! * 1.3)
        brandPixels++;
    return { width: canvas.width, height: canvas.height, brandPixels };
  });
  expect(imageDetails.width).toBe(1200);
  expect(imageDetails.height).toBe(630);
  // Regression: a valid PNG once rendered text but silently dropped the blue logo.
  expect(imageDetails.brandPixels).toBeGreaterThan(100);
});

test("404 page provides keyboard recovery and remains noindex", async ({
  page,
}) => {
  const response = await page.goto("/this-page-does-not-exist");
  expect(response?.status()).toBe(404);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "That page isn’t here.",
  );
  expect(
    await page.locator('meta[name="robots"]').first().getAttribute("content"),
  ).toContain("noindex");
  await page.getByRole("link", { name: "Return to Omnix" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Build software with an AI engineering team.",
  );
});
