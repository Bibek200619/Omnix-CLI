import type { ComponentPropsWithRef } from "react";
import styles from "./primitives.module.css";

export function Code({
  className = "",
  ...props
}: ComponentPropsWithRef<"code">) {
  return <code {...props} className={`${styles.inlineCode} ${className}`} />;
}
