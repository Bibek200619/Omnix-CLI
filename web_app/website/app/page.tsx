import { links, product } from "@/lib/constants";
import { Container } from "@/components/ui/container";
import { Link } from "@/components/ui/link";
import { Code } from "@/components/ui/code";
import { SiteHeader } from "@/components/marketing/site-header";
import { HeroSection } from "@/components/marketing/hero-section";
import { OrchestrationJourney } from "@/components/orchestration/orchestration-journey";
import {
  ArchitectSection,
  CliSection,
  MemorySection,
  ProvidersSection,
} from "@/components/marketing/product-proof-sections";

export default function Home() {
  return (
    <>
      <SiteHeader />
      <main id="main" tabIndex={-1}>
        <HeroSection />
        <OrchestrationJourney />
        <MemorySection />
        <ProvidersSection />
        <CliSection />
        <ArchitectSection />
      </main>
      <Container>
        <footer className="site-meta">
          <p>
            {product.availability} <Code>v{product.version}</Code>
            <br />
            Python {product.minimumPython}+ required
          </p>
          <Link href={links.source}>GitHub source</Link>
        </footer>
      </Container>
    </>
  );
}
