import Image from "next/image";
import { brand, links, product } from "@/lib/constants";

export default function Home() {
  return (
    <div className="foundation">
      <header className="foundation-brand">
        <Image
          src={brand.logo}
          width={brand.width}
          height={brand.height}
          alt=""
          preload
        />
        <span>{product.name}</span>
      </header>
      <main id="main" tabIndex={-1} className="foundation-main">
        <h1>Omnix CLI is taking shape.</h1>
        <p>
          Project conversations, persistent memory, and specialized engineering
          workflows in your terminal. Explore the source preview while the
          website takes shape.
        </p>
        <a className="foundation-link" href={links.source}>
          Explore the source on GitHub
        </a>
      </main>
      <footer className="foundation-meta">
        <p>
          {product.availability} <code>v{product.version}</code>
          <br />
          Python {product.minimumPython}+ required
        </p>
      </footer>
    </div>
  );
}
