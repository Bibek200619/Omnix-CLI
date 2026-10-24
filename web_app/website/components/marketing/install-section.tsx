import { Badge } from "@/components/ui/badge";
import { Code } from "@/components/ui/code";
import { CodeBlock } from "@/components/ui/code-block";
import { Container } from "@/components/ui/container";
import { Link } from "@/components/ui/link";
import { Section } from "@/components/ui/section";
import { sourceSetup } from "@/content/install";
import { links, product } from "@/lib/constants";
import type { ReleaseState } from "@/lib/release";
import styles from "./install.module.css";

function ReleaseNotice({ state }: { state: ReleaseState }) {
  switch (state.kind) {
    case "stable":
    case "prerelease":
      return (
        <div className={styles.releaseNotice}>
          <h3>
            {state.kind === "stable"
              ? "Stable release published"
              : "Prerelease published"}{" "}
            <Code>{state.release.tag}</Code>
          </h3>
          <p>
            Review the release notes on GitHub. A packaged installation method
            has not been verified for this release; source setup remains
            available below.
          </p>
          <Link href={state.release.url}>Review release</Link>
        </div>
      );
    case "none":
      return (
        <div className={styles.releaseNotice}>
          <h3>No published release is listed.</h3>
          <p>
            Start from the Python source preview. Package version{" "}
            {product.version} identifies the source, not a stable distribution.
          </p>
          <Link href={links.releases}>Check GitHub Releases</Link>
        </div>
      );
    case "unavailable":
      return (
        <div className={styles.releaseNotice}>
          <h3>Release information is unavailable.</h3>
          <p>
            Source setup remains available. Check GitHub for the current release
            status.
          </p>
          <Link href={links.releases}>Check GitHub Releases</Link>
        </div>
      );
  }
}

export function InstallSection({
  releaseState,
}: {
  releaseState: ReleaseState;
}) {
  return (
    <Container>
      <Section
        id="download"
        title="Try the source preview."
        tabIndex={-1}
        className={styles.section}
      >
        <p className={styles.intro}>
          Clone the Python CLI and run it in a local virtual environment.
          Provider-backed workflows use your own API key.
        </p>
        <div className={styles.layout}>
          <div className={styles.requirements}>
            <Badge status="preview" />
            <ReleaseNotice state={releaseState} />
            <dl className={styles.facts}>
              <div>
                <dt>Source package</dt>
                <dd>
                  <Code>{product.version}</Code>
                </dd>
              </div>
              <div>
                <dt>Python</dt>
                <dd>{product.minimumPython} or newer</dd>
              </div>
              <div>
                <dt>Tools</dt>
                <dd>
                  Git and <Link href={sourceSetup.uvDocs}>uv</Link>
                </dd>
              </div>
            </dl>
            <Link href={links.cliDocs}>Read the CLI documentation</Link>
          </div>
          <div className={styles.setup}>
            <CodeBlock
              label={sourceSetup.label}
              code={sourceSetup.command}
              copyable
              copyLabel="Copy setup commands"
            />
            <p className={styles.note}>
              Run these commands from a directory where you want a new checkout.
              Stay in <Code>ai-cli/</Code> and use{" "}
              <Code>uv run --frozen omnix</Code> for subsequent commands. Setup
              does not add a global <Code>omnix</Code> command.
            </p>
            <details className={styles.help}>
              <summary>Setup help</summary>
              <ul>
                <li>
                  If Git reports that the destination exists, use a fresh
                  directory or your existing checkout.
                </li>
                <li>
                  If <Code>uv</Code> is not found, follow the{" "}
                  <Link href={sourceSetup.uvDocs}>
                    uv installation instructions
                  </Link>{" "}
                  and reopen your terminal.
                </li>
                <li>
                  Confirm Python {product.minimumPython}+ is available. Run the
                  shown uv commands from <Code>Omnix-CLI/ai-cli</Code> so they
                  use its project environment.
                </li>
                <li>
                  See the <Link href="#cli">CLI commands</Link> for the next
                  steps. For setup errors,{" "}
                  <Link href={links.issues}>open a GitHub issue</Link>.
                </li>
              </ul>
            </details>
          </div>
        </div>
      </Section>
    </Container>
  );
}
