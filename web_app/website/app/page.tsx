import Image from "next/image";
import { brand, links, product } from "@/lib/constants";
import { Container } from "@/components/ui/container";
import { Link } from "@/components/ui/link";
import { Code } from "@/components/ui/code";

export default function Home() {
  return (
    <Container className="foundation">
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
        <Link className="foundation-link" href={links.source}>
          Explore the source on GitHub
        </Link>
      </main>
      <footer className="foundation-meta">
        <p>
          {product.availability} <Code>v{product.version}</Code>
          <br />
          Python {product.minimumPython}+ required
        </p>
      </footer>
    </Container>
  );
}
