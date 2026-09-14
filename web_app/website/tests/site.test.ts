import { expect, it } from "vitest";
import { resolveSiteUrl } from "@/lib/site";

it("does not invent a canonical domain", () => {
  expect(resolveSiteUrl(undefined)).toBeUndefined();
  expect(resolveSiteUrl("")).toBeUndefined();
  expect(resolveSiteUrl("https://example.com")?.href).toBe(
    "https://example.com/",
  );
});

it.each([
  "http://example.com",
  "https://user:secret@example.com",
  "https://example.com/path",
  "https://example.com/?test=1",
  "invalid",
])("rejects an invalid deployment origin: %s", (value) => {
  expect(() => resolveSiteUrl(value)).toThrow();
});
