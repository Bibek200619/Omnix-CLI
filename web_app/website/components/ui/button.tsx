import type { ComponentPropsWithRef } from "react";
import styles from "./primitives.module.css";

export type ButtonVariant = "primary" | "secondary" | "ghost";
export type ButtonProps = ComponentPropsWithRef<"button"> & {
  variant?: ButtonVariant;
  loading?: boolean;
  loadingLabel?: string;
};

export function Button({
  variant = "primary",
  loading = false,
  loadingLabel = "Working…",
  disabled,
  type = "button",
  children,
  className = "",
  ...props
}: ButtonProps) {
  return (
    <button
      {...props}
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      data-variant={variant}
      className={`${styles.control} ${className}`}
    >
      {children}
      {loading ? (
        <>
          {" "}
          <span className={styles.progress}>{loadingLabel}</span>
        </>
      ) : null}
    </button>
  );
}
