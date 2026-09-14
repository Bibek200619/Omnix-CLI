import type { ComponentPropsWithRef } from "react";
import styles from "./primitives.module.css";

type BadgeProps = Omit<ComponentPropsWithRef<"span">, "children"> &
  (
    | { status: "available" | "roadmap" | "preview"; version?: never }
    | { status: "version"; version: string }
  );

const labels = {
  available: "Available",
  roadmap: "Roadmap",
  preview: "Preview",
  version: "Version",
};

export function Badge({
  status,
  version,
  className = "",
  ...props
}: BadgeProps) {
  return (
    <span
      {...props}
      data-status={status}
      className={`${styles.badge} ${className}`}
    >
      {labels[status]}
      {status === "version" ? ` ${version}` : ""}
    </span>
  );
}
