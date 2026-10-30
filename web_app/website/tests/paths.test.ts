import { expect, it } from "vitest";
import { appPath, resolveBasePath } from "@/lib/paths";

it("supports standalone development and a clean deployment prefix", () => {
  expect(resolveBasePath(undefined)).toBe("");
  expect(resolveBasePath("")).toBe("");
  expect(resolveBasePath("/cli")).toBe("/cli");
  expect(appPath("/", "")).toBe("/");
  expect(appPath("/", "/cli")).toBe("/cli");
  expect(appPath("/brand/omnix-logo.png", "/cli")).toBe(
    "/cli/brand/omnix-logo.png",
  );
  expect(appPath("#download", "/cli")).toBe("#download");
  expect(appPath("https://github.com/Bibek200619/Omnix-CLI", "/cli")).toBe(
    "https://github.com/Bibek200619/Omnix-CLI",
  );
});

it.each([
  "/",
  "cli",
  "/cli/",
  "//evil.test",
  "/cli/../app",
  "/cli?x=1",
  "/cli#test",
  "/cli%2fapp",
  " /cli",
  "/cli\\app",
])("rejects an ambiguous deployment prefix: %s", (value) => {
  expect(() => resolveBasePath(value)).toThrow(/NEXT_PUBLIC_BASE_PATH/);
});
