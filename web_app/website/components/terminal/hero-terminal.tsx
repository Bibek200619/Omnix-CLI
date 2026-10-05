import { CopyButton } from "@/components/ui/copy-button";
import { terminalCommands, terminalSteps } from "@/content/hero";
import styles from "./hero-terminal.module.css";

export function HeroTerminal() {
  return (
    <figure
      id="hero-cli"
      tabIndex={-1}
      aria-labelledby="terminal-title"
      aria-describedby="terminal-description"
      className={styles.terminal}
    >
      <figcaption className={styles.caption}>
        <span id="terminal-title">From goal to blueprint</span>
        <span className={styles.kind}>Command walkthrough</span>
      </figcaption>
      <p id="terminal-description" className={styles.description}>
        Real commands. Notes below are website narration, not CLI output.
      </p>
      <ol className={styles.steps}>
        {terminalSteps.map((step, index) => (
          <li key={step.command}>
            <span className={styles.number} aria-hidden="true">
              {String(index + 1).padStart(2, "0")}
            </span>
            <div className={styles.step}>
              <pre className={styles.command}>
                <span aria-hidden="true" className={styles.prompt}>
                  ${" "}
                </span>
                <code>{step.command}</code>
              </pre>
              <p className={styles.note}>{step.note}</p>
            </div>
          </li>
        ))}
      </ol>
      <div className={styles.setup}>
        <p>
          Requires source setup and an OpenAI API key with access to the example
          model. Run in a fresh project directory. Copying does not execute
          commands.
        </p>
        <CopyButton text={terminalCommands} label="Copy commands" />
      </div>
    </figure>
  );
}
