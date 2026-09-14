import type { Metadata } from "next";
import Image from "next/image";
import { Badge } from "@/components/ui/badge";
import { Code } from "@/components/ui/code";
import { CodeBlock } from "@/components/ui/code-block";
import { Container } from "@/components/ui/container";
import { Link } from "@/components/ui/link";
import { Section } from "@/components/ui/section";
import { brand, links, product } from "@/lib/constants";
import { ActionExamples } from "./action-examples";
import styles from "./review.module.css";

export const metadata: Metadata = {
  title: "Design system review",
  robots: { index: false, follow: false },
  alternates: { canonical: null },
};

export default function DesignSystemPage() {
  return (
    <Container className={styles.review}>
      <header className={styles.header}>
        <div className={styles.brand}>
          <Image
            src={brand.logo}
            width={brand.width}
            height={brand.height}
            alt=""
          />
          <span>{product.name}</span>
        </div>
        <Link href="/" variant="ghost">
          Back to preview
        </Link>
      </header>
      <main id="main" tabIndex={-1}>
        <div className={styles.intro}>
          <h1>Design system review</h1>
          <p>
            Reusable controls, readable code, and clear state. This page is a
            working reference for the Omnix website.
          </p>
        </div>
        <Section
          id="controls"
          title="Actions and navigation"
          className={styles.specimen}
        >
          <p className={styles.description}>
            Use one primary action per context. Try the enabled buttons with a
            pointer, Enter, or Space. The two final examples show disabled and
            loading states.
          </p>
          <ActionExamples />
          <div className={styles.links}>
            <Link href="#code">Jump to code examples</Link>
            <Link href={links.source} newTab>
              Inspect the source
            </Link>
            <Link href="/" variant="secondary">
              Open website preview
            </Link>
          </div>
        </Section>
        <Section
          id="states"
          title="State in plain sight"
          className={styles.specimen}
        >
          <p className={styles.description}>
            Status labels carry the meaning. Border styles and color reinforce
            it. “Available” refers to implemented source-preview behavior.
          </p>
          <ul className={styles.stateList}>
            <li>
              <span>Architect Agent</span>
              <Badge status="available" />
            </li>
            <li>
              <span>Anthropic live generation</span>
              <Badge status="roadmap" />
            </li>
            <li>
              <span>Distribution</span>
              <Badge status="preview" />
            </li>
            <li>
              <span>Source package</span>
              <Badge status="version" version={product.version} />
            </li>
          </ul>
        </Section>
        <Section
          id="type"
          title="Type and surfaces"
          className={styles.specimen}
        >
          <p className={styles.description}>
            Geist carries the interface. Geist Mono distinguishes commands and
            file paths, such as <Code>.project/project.blueprint.json</Code>.
          </p>
          <div className={styles.surfaces}>
            <div className={styles.surfaceOne}>
              <strong>Surface 1</strong>
              <span>Quiet grouping</span>
            </div>
            <div className={styles.surfaceTwo}>
              <strong>Surface 2</strong>
              <span>Code and nested content</span>
            </div>
            <div className={styles.surfaceThree}>
              <strong>Surface 3</strong>
              <span>Control emphasis</span>
            </div>
          </div>
        </Section>
        <Section
          id="code"
          title="Code you can select"
          className={styles.specimen}
        >
          <p className={styles.description}>
            These are existing CLI commands. Copying does not run them. Long
            lines stay inside their own keyboard-scrollable region.
          </p>
          <div className={styles.stack}>
            <CodeBlock
              label="Inspect a project"
              code={"omnix models\nomnix blueprint"}
              copyable
            />
            <CodeBlock
              label="Explicit workspace"
              code={
                'omnix init --project-name "Architecture review" --description "A source preview workspace for reviewing project state" --workspace /path/to/project'
              }
            />
          </div>
        </Section>
      </main>
      <footer className={styles.footer}>
        Phase 2 component reference. Product sections follow in later phases.
      </footer>
    </Container>
  );
}
