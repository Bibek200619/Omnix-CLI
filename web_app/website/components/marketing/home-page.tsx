import Image from "next/image";
import { brand, links, product } from "@/lib/constants";
import { Container } from "@/components/ui/container";
import { Link } from "@/components/ui/link";
import { Code } from "@/components/ui/code";
import { SiteHeader } from "@/components/marketing/site-header";
import { HeroSection } from "@/components/marketing/hero-section";
import { OrchestrationJourney } from "@/components/orchestration/orchestration-journey";
import { RoadmapSection } from "@/components/marketing/roadmap-section";
import { InstallSection } from "@/components/marketing/install-section";
import { releaseSnapshot, type ReleaseState } from "@/lib/release";
import {
  ArchitectSection,
  CliSection,
  MemorySection,
  ProvidersSection,
} from "@/components/marketing/product-proof-sections";
import styles from "./experience.module.css";

export default function HomePage({
  releaseState = releaseSnapshot.state,
}: {
  releaseState?: ReleaseState;
}) {
  return (
    <>
      <SiteHeader />
      <main id="main" tabIndex={-1}>
        <HeroSection />
        <div className={styles.narrative}>
          <OrchestrationJourney />
          <MemorySection />
          <ProvidersSection />
          <CliSection />
          <ArchitectSection />
          <RoadmapSection />
          <InstallSection releaseState={releaseState} />
        </div>
      </main>
      <div className={styles.footer}>
        <Container>
          <footer className="site-meta">
            <div>
              <div className="footer-brand">
                <Image src={brand.logo} width={32} height={32} alt="" />
                Omnix CLI
              </div>
              <p>
                {product.availability} <Code>v{product.version}</Code>
                <br />
                Python {product.minimumPython}+ required
              </p>
            </div>
            <nav aria-label="Footer">
              <Link href={links.source}>GitHub source</Link>
              <Link href={links.cliDocs}>CLI documentation</Link>
              <Link href={links.issues}>GitHub issues</Link>
            </nav>
          </footer>
        </Container>
      </div>
    </>
  );
}
