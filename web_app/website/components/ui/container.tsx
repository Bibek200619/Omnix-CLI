import type { ComponentPropsWithRef } from "react";
import styles from "./primitives.module.css";

type ContainerProps = ComponentPropsWithRef<"div"> & {
  width?: "page" | "prose";
};

export function Container({
  width = "page",
  className = "",
  ...props
}: ContainerProps) {
  return (
    <div
      {...props}
      className={`${styles.container} ${className}`}
      data-width={width}
    />
  );
}
