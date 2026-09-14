import Image from "next/image";
import { Container } from "@/components/ui/container";
import { Link } from "@/components/ui/link";
import { hero, navigation } from "@/content/hero";
import { brand } from "@/lib/constants";
import { MobileNav } from "./mobile-nav";
import styles from "./header.module.css";

export function SiteHeader() {
  return (
    <header className={styles.header}>
      <Container className={styles.inner}>
        <Link
          href="/"
          aria-label="Omnix home"
          aria-current="page"
          className={styles.brand}
        >
          <Image
            src={brand.logo}
            width={brand.width}
            height={brand.height}
            alt=""
          />
          <span>Omnix</span>
        </Link>
        <nav aria-label="Primary" className={styles.desktop}>
          {navigation.map((item) => (
            <Link key={item.href} href={item.href} variant="ghost">
              {item.label}
            </Link>
          ))}
          <Link href={hero.primary.href} variant="secondary">
            Source preview
          </Link>
        </nav>
        <MobileNav />
      </Container>
    </header>
  );
}
