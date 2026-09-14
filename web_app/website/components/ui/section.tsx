import type { ComponentPropsWithRef } from "react";
import styles from "./primitives.module.css";

type SectionProps = Omit<
  ComponentPropsWithRef<"section">,
  "title" | "aria-label" | "aria-labelledby"
> & {
  id: string;
  title: string;
  headingLevel?: 2 | 3;
  spacing?: "default" | "compact";
};

export function Section({
  id,
  title,
  headingLevel = 2,
  spacing = "default",
  children,
  className = "",
  ...props
}: SectionProps) {
  const Heading = headingLevel === 3 ? "h3" : "h2";
  return (
    <section
      {...props}
      id={id}
      aria-labelledby={`${id}-heading`}
      data-spacing={spacing}
      className={`${styles.section} ${className}`}
    >
      <Heading id={`${id}-heading`} className={styles.sectionTitle}>
        {title}
      </Heading>
      {children}
    </section>
  );
}
