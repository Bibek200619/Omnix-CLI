import type { ComponentPropsWithRef } from "react";
import type { ButtonVariant } from "./button";
import styles from "./primitives.module.css";

type LinkProps = Omit<ComponentPropsWithRef<"a">, "href" | "target"> & {
  href: string;
  variant?: "text" | ButtonVariant;
  newTab?: boolean;
};

export function Link({
  href,
  variant = "text",
  newTab = false,
  rel,
  children,
  className = "",
  ...props
}: LinkProps) {
  // Product links are source-controlled: reject executable or ambiguous URL schemes.
  if (!/^(https:\/\/|\/(?!\/)|#)/.test(href) || /[\s\\]/.test(href)) {
    throw new Error(
      "Link requires an HTTPS URL, root-relative path, or anchor.",
    );
  }
  const external = href.startsWith("https://");
  return (
    <a
      {...props}
      href={href}
      target={newTab ? "_blank" : undefined}
      rel={newTab ? `${rel ?? ""} noopener noreferrer`.trim() : rel}
      data-variant={variant}
      className={`${variant === "text" ? styles.link : styles.control} ${className}`}
    >
      {children}
      {external ? (
        <span aria-hidden="true" className={styles.external}>
          ↗
        </span>
      ) : null}
      {newTab ? (
        <span className={styles.srOnly}> (opens in a new tab)</span>
      ) : null}
    </a>
  );
}
