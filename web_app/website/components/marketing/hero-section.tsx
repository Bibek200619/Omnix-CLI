import { Container } from "@/components/ui/container";
import { Link } from "@/components/ui/link";
import { hero } from "@/content/hero";
import { product } from "@/lib/constants";
import { HeroTerminal } from "@/components/terminal/hero-terminal";
import styles from "./hero.module.css";

export function HeroSection() {
  return (
    <section
      id="product"
      aria-labelledby="hero-heading"
      tabIndex={-1}
      className={styles.hero}
    >
      <Container className={styles.layout}>
        <div className={styles.message}>
          <p className={styles.eyebrow}>{hero.eyebrow}</p>
          <h1 id="hero-heading">{hero.headline}</h1>
          <p className={styles.supporting}>{hero.supporting}</p>
          <div className={styles.actions}>
            <Link variant="primary" href={hero.primary.href}>
              {hero.primary.label}
            </Link>
            <Link variant="secondary" href={hero.secondary.href}>
              {hero.secondary.label}
            </Link>
          </div>
          <p className={styles.release}>
            Source preview v{product.version}. Python {product.minimumPython}+.
            <br />
            Specialist workflows produce blueprints, artifacts, and reports.
          </p>
        </div>
        <HeroTerminal />
      </Container>
    </section>
  );
}
