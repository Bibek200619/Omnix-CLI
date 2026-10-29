/** Next.js embeds the public prefix at build time in server and client code. */
export function resolveBasePath(value: string | undefined): string {
  if (!value) return "";
  if (!/^(?:\/[a-z0-9]+(?:-[a-z0-9]+)*)+$/.test(value))
    throw new Error(
      "NEXT_PUBLIC_BASE_PATH must be a clean path such as /cli, without a trailing slash.",
    );
  return value;
}

export const basePath = resolveBasePath(process.env.NEXT_PUBLIC_BASE_PATH);

export function appPath(path: string, prefix = basePath): string {
  if (!path.startsWith("/") || path.startsWith("//")) return path;
  return `${prefix}${prefix && path === "/" ? "" : path}`;
}
