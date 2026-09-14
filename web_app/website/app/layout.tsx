import type { Metadata } from "next";
import localFont from "next/font/local";
import { brand, product } from "@/lib/constants";
import { resolveSiteUrl } from "@/lib/site";
import "./globals.css";

const sans = localFont({
  src: "../node_modules/@fontsource-variable/geist/files/geist-latin-wght-normal.woff2",
  variable: "--font-geist",
  display: "swap",
});
const mono = localFont({
  src: "../node_modules/@fontsource-variable/geist-mono/files/geist-mono-latin-wght-normal.woff2",
  variable: "--font-geist-mono",
  display: "swap",
});
const siteUrl = resolveSiteUrl(process.env.SITE_URL);

export const metadata: Metadata = {
  title: { default: "Omnix CLI — Source preview", template: "%s | Omnix CLI" },
  description: product.description,
  ...(siteUrl ? { metadataBase: siteUrl, alternates: { canonical: "/" } } : {}),
  robots: { index: false, follow: false },
  icons: {
    icon: { url: brand.logo, type: "image/png", sizes: "180x180" },
    apple: brand.logo,
  },
  openGraph: {
    title: product.name,
    description: product.description,
    type: "website",
    siteName: product.name,
    ...(siteUrl
      ? {
          url: siteUrl,
          images: [
            {
              url: brand.logo,
              width: brand.width,
              height: brand.height,
              alt: "Omnix",
            },
          ],
        }
      : {}),
  },
  twitter: {
    card: "summary",
    title: product.name,
    description: product.description,
    ...(siteUrl ? { images: [new URL(brand.logo, siteUrl).href] } : {}),
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable}`}>
      <body>
        <a className="skip-link" href="#main">
          Skip to content
        </a>
        {children}
      </body>
    </html>
  );
}
