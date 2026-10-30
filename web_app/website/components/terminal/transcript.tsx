import type { terminalDemo } from "@/content/terminal-demo";
import styles from "./hero-terminal.module.css";

export function Transcript({
  state,
  excerpt = false,
}: {
  state: (typeof terminalDemo)[number];
  excerpt?: boolean;
}) {
  return (
    <figure data-theme="dark" className={styles.transcript}>
      <figcaption className={styles.chrome}>
        <span aria-hidden="true">›_</span> atlas / local project
      </figcaption>
      <pre
        className={styles.output}
        tabIndex={0}
        role="region"
        aria-label={`${state.label} ${excerpt ? "transcript excerpt" : "terminal transcript"}`}
      >
        <code>
          <span className={styles.prompt} aria-hidden="true">
            ${" "}
          </span>
          {state.command}
          {"\n"}
          {excerpt
            ? state.output.split("\n").slice(0, 10).join("\n")
            : state.output}
        </code>
      </pre>
    </figure>
  );
}
