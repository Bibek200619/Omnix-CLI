import type { Metadata } from "next";
import { Container } from "@/components/ui/container";
import { Link } from "@/components/ui/link";
import { links } from "@/lib/constants";
import styles from "./not-found.module.css";

export const metadata: Metadata = {
  title: "Page not found",
  robots: { index: false, follow: false },
};

export default function NotFound() {
  return (
    <main id="main" tabIndex={-1}>
      <Container className={styles.content} width="prose">
        <p>Omnix CLI · 404</p>
        <h1>That page isn’t here.</h1>
        <p>Return to the product overview or open the CLI documentation.</p>
        <div className={styles.actions}>
          <Link href="/" variant="primary">
            Return to Omnix
          </Link>
          <Link href={links.cliDocs} variant="secondary">
            CLI documentation
          </Link>
        </div>
      </Container>
    </main>
  );
}
