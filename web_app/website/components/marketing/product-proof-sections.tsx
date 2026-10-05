import { Badge } from "@/components/ui/badge";
import { Code } from "@/components/ui/code";
import { Container } from "@/components/ui/container";
import { CopyButton } from "@/components/ui/copy-button";
import { Section } from "@/components/ui/section";
import { providers } from "@/content/providers";
import {
  architectFlow,
  commandGroups,
  memoryRecords,
} from "@/content/product-proof";
import styles from "./product-proof.module.css";

function CommandRows({ groupId }: { groupId: string }) {
  const group = commandGroups.find((candidate) => candidate.id === groupId);
  if (!group) return null;

  return (
    <ol className={styles.commandList}>
      {group.commands.map((command) => (
        <li key={command.name} className={styles.commandRow}>
          <div className={styles.commandText}>
            <Code>{command.syntax}</Code>
            <p>{command.summary}</p>
          </div>
          <CopyButton
            text={command.syntax}
            label={
              /[A-Z]/.test(command.syntax) ? "Copy syntax" : "Copy command"
            }
          />
        </li>
      ))}
    </ol>
  );
}

export function MemorySection() {
  return (
    <Container>
      <Section
        id="memory"
        title="Project context lives with the project."
        tabIndex={-1}
        className={styles.proofSection}
      >
        <div className={styles.memoryLayout}>
          <div className={styles.sectionIntro}>
            <p className={styles.lead}>
              Omnix stores validated JSON under <Code>.project/</Code>. Master
              adds conversations, goals, and decisions; specialist commands read
              that state when you invoke them.
            </p>
            <p className={styles.caveat}>
              Local files, not a cloud account. Chat records context but does
              not automatically dispatch specialists.
            </p>
          </div>
          <div className={styles.fileLedger}>
            {[...new Set(memoryRecords.map((record) => record.file))].map(
              (file) => (
                <section key={file} aria-label={file}>
                  <h3 className={styles.filePath}>
                    <span>.project/</span>
                    <strong>{file}</strong>
                  </h3>
                  <dl>
                    {memoryRecords
                      .filter((record) => record.file === file)
                      .map((record) => (
                        <div key={record.name} className={styles.record}>
                          <dt>{record.name}</dt>
                          <dd>
                            <span>{record.detail}</span>
                            <Code>{record.command}</Code>
                          </dd>
                        </div>
                      ))}
                  </dl>
                </section>
              ),
            )}
          </div>
        </div>
      </Section>
    </Container>
  );
}

export function ProvidersSection() {
  return (
    <Container>
      <Section
        id="providers"
        title="Roles choose models through one provider layer."
        tabIndex={-1}
        className={styles.proofSection}
      >
        <div className={styles.providerHeader}>
          <p className={styles.lead}>
            Assign a provider and model to each engineering role. The command
            workflow stays consistent while the role configuration changes.
          </p>
          <div className={styles.routing} aria-label="Provider routing model">
            <span>Role</span>
            <span aria-hidden="true">→</span>
            <span>Provider</span>
            <span aria-hidden="true">→</span>
            <span>Model</span>
          </div>
        </div>
        <div
          className={styles.providerTableWrap}
          tabIndex={0}
          role="region"
          aria-label="Provider implementation status"
        >
          <table className={styles.providerTable}>
            <thead>
              <tr>
                <th scope="col">Provider</th>
                <th scope="col">Generation status</th>
                <th scope="col">Source boundary</th>
              </tr>
            </thead>
            <tbody>
              {providers.map((provider) => (
                <tr key={provider.id} data-provider-status={provider.status}>
                  <th scope="row">{provider.name}</th>
                  <td>
                    <Badge
                      status={
                        provider.status === "live-adapter"
                          ? "available"
                          : "roadmap"
                      }
                    />
                  </td>
                  <td>{provider.summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={styles.caveat}>
          <Code>omnix models</Code> displays configured role assignments. It
          does not fetch a provider’s live model catalog.
        </p>
      </Section>
    </Container>
  );
}

export function CliSection() {
  const primaryGroups = commandGroups.filter(
    (group) => "primary" in group && group.primary,
  );
  const orchestration = commandGroups.find(
    (group) => group.id === "orchestration",
  )!;

  return (
    <Container>
      <Section
        id="cli"
        title="The CLI is the product surface."
        tabIndex={-1}
        className={styles.proofSection}
      >
        <div className={styles.commandIntro}>
          <p className={styles.lead}>
            Twenty-six registered commands cover setup, persistent context,
            architecture, and the source-preview orchestration lifecycle.
          </p>
          <p className={styles.commandCount}>
            <span>26</span> registered commands
          </p>
        </div>
        <div className={styles.commandGroups}>
          {primaryGroups.map((group) => (
            <section key={group.id} aria-labelledby={`${group.id}-commands`}>
              <div className={styles.groupHeading}>
                <h3 id={`${group.id}-commands`}>{group.title}</h3>
                <p>{group.description}</p>
              </div>
              <CommandRows groupId={group.id} />
            </section>
          ))}
          <details className={styles.moreCommands}>
            <summary>
              <span>{orchestration.title}</span>
              <span>
                <span className={styles.showLabel}>Show</span>
                <span className={styles.hideLabel}>Hide</span>{" "}
                {orchestration.commands.length} commands
              </span>
            </summary>
            <p>{orchestration.description}</p>
            <CommandRows groupId={orchestration.id} />
          </details>
        </div>
        <p className={styles.caveat}>
          Replace uppercase arguments with your values before running; square
          brackets mark optional arguments. Copying preserves the shown syntax.
          Preview orchestration stores JSON artifacts and model-assisted
          reports; those outputs do not prove an application builds, passes
          tests, or deploys.
        </p>
      </Section>
    </Container>
  );
}

export function ArchitectSection() {
  return (
    <Container>
      <Section
        id="architect"
        title="The Architect evolves a source of truth."
        tabIndex={-1}
        className={styles.proofSection}
      >
        <div className={styles.architectHeader}>
          <p className={styles.lead}>
            Run <Code>omnix architect</Code> explicitly. The agent combines
            saved context with a structured proposal, validates the result, and
            only then saves the blueprint.
          </p>
          <Badge status="available" />
        </div>
        <ol className={styles.architectFlow}>
          {architectFlow.map((step, index) => (
            <li key={step.title}>
              <span className={styles.flowNumber} aria-hidden="true">
                {index + 1}
              </span>
              <div>
                <h3>{step.title}</h3>
                <p>{step.detail}</p>
                <Code>{step.evidence}</Code>
              </div>
            </li>
          ))}
        </ol>
        <div className={styles.architectResult}>
          <div>
            <span>Saved result</span>
            <Code>.project/project.blueprint.json</Code>
          </div>
          <p>
            Blueprint validation checks structure and required architecture
            fields. It is not runtime code validation.
          </p>
        </div>
      </Section>
    </Container>
  );
}
