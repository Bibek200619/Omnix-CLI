import { CopyButton } from "./copy-button";
import styles from "./primitives.module.css";

type CodeBlockProps = {
  code: string;
  label: string;
  copyable?: boolean;
  copyLabel?: string;
  className?: string;
};

export function CodeBlock({
  code,
  label,
  copyable = false,
  copyLabel,
  className = "",
}: CodeBlockProps) {
  return (
    <figure aria-label={label} className={`${styles.codeBlock} ${className}`}>
      <figcaption className={styles.codeCaption}>{label}</figcaption>
      <pre
        tabIndex={0}
        role="region"
        aria-label={`${label} code`}
        className={styles.codeContent}
      >
        <code>{code}</code>
      </pre>
      {copyable ? (
        <div className={styles.codeActions}>
          <CopyButton text={code} label={copyLabel} />
        </div>
      ) : null}
    </figure>
  );
}
