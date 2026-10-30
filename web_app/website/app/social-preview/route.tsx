import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { ImageResponse } from "next/og";
import { hero } from "@/content/hero";

export const dynamic = "force-static";

export async function GET() {
  const logo = await readFile(
    join(process.cwd(), "public/brand/omnix-logo.png"),
  );
  // OG rendering has no CSS variables: these mirror the documented brand tokens.
  return new ImageResponse(
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        width: "100%",
        height: "100%",
        padding: 72,
        background:
          "linear-gradient(135deg, #cadbfc 0%, #e8f1fb 65%, #c5dbde 100%)",
        color: "#14233b",
        fontFamily: "sans-serif",
      }}
    >
      <div
        style={{ display: "flex", alignItems: "center", gap: 24, fontSize: 32 }}
      >
        {/* The official PNG is embedded unchanged, with its original aspect ratio. */}
        {/* eslint-disable-next-line @next/next/no-img-element -- ImageResponse requires a native image. */}
        <img
          src={`data:image/png;base64,${logo.toString("base64")}`}
          width={88}
          height={88}
          style={{ width: 88, height: 88, flexShrink: 0 }}
          alt=""
        />
        <span>Omnix CLI</span>
      </div>
      <div
        style={{
          display: "flex",
          maxWidth: 1000,
          fontSize: 72,
          fontWeight: 700,
          lineHeight: 1.1,
          letterSpacing: -3,
        }}
      >
        {hero.headline}
      </div>
      <div style={{ display: "flex", fontSize: 26, color: "#4c6281" }}>
        Source preview · Project memory · Specialist workflows
      </div>
    </div>,
    { width: 1200, height: 630 },
  );
}
