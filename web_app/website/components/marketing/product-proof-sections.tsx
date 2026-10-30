import { Badge } from "@/components/ui/badge";
import { Code } from "@/components/ui/code";
import { CodeBlock } from "@/components/ui/code-block";
import { Container } from "@/components/ui/container";
import { CopyButton } from "@/components/ui/copy-button";
import { Section } from "@/components/ui/section";
import { Transcript } from "@/components/terminal/transcript";
import { providers } from "@/content/providers";
import { commands } from "@/content/commands";
import { exampleAssignments, terminalDemo } from "@/content/terminal-demo";
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
        title="Context is a file. Not a fleeting tab."
        eyebrow="02 / A project that remembers"
        tabIndex={-1}
        className={styles.proofSection}
      >
        <div className={styles.sectionIntro}>
          <p className={styles.lead}>
            Keep conversations, goals, and decisions with the project. The
            planning result lives in a separate blueprint, so memory and
            architecture stay distinct.
          </p>
          <p className={styles.caveat}>
            Local files, not a cloud account. Chat records context but does not
            automatically dispatch specialists.
          </p>
        </div>
        <div className={styles.memoryLayout}>
          <div className={styles.fileLedger} data-theme="light">
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
          <aside
            className={styles.evidence}
            aria-label="Project memory workflow"
          >
            <p className="section-label">Same project, next command</p>
            <h3>Pick up where the conversation left off.</h3>
            <CodeBlock
              label="Inspect local project memory"
              code={"omnix memory\nomnix goals\nomnix decisions"}
              copyable
            />
            <p>
              These commands inspect the local record. The memory summary
              reports stored-message counts; your conversation stays in the
              project file.
            </p>
          </aside>
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
        title="Know what each role is configured to use."
        eyebrow="03 / Roles, not a model mixer"
        tabIndex={-1}
        className={styles.proofSection}
      >
        <p className={styles.lead}>
          One role, one configured provider, one selected model. Configuration
          explains the relationship; it is not evidence of successful inference.
        </p>
        <div className={styles.providerLayout}>
          <div
            className={styles.assignments}
            role="group"
            aria-label="Example local model assignments"
          >
            <div className={styles.routing} aria-hidden="true">
              <span>Role</span>
              <span>Provider</span>
              <span>Model</span>
            </div>
            {exampleAssignments.map((assignment) => (
              <dl key={assignment.role} className={styles.assignment}>
                <div data-theme="light">
                  <dt>Role</dt>
                  <dd>{assignment.role}</dd>
                </div>
                <div data-theme="light">
                  <dt>Provider</dt>
                  <dd>{assignment.provider}</dd>
                </div>
                <div data-theme="light">
                  <dt>Model</dt>
                  <dd>{assignment.model}</dd>
                </div>
              </dl>
            ))}
            <p>
              Example assignments from the CLI demonstration. You choose your
              model; this is not a default or a live routing result.
            </p>
          </div>
          <aside
            className={styles.evidence}
            aria-label="Model configuration transcript"
          >
            <h3>Related to the terminal evidence</h3>
            <Transcript state={terminalDemo[1]} />
            <p>{terminalDemo[1].caption}</p>
          </aside>
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
        title="Command explorer."
        eyebrow="04 / An explicit command surface"
        tabIndex={-1}
        className={styles.proofSection}
      >
        <div className={styles.commandLayout}>
          <div className={styles.commandIntro}>
            <p className={styles.commandCount}>
              <span>{commands.length}</span> registered commands
            </p>
            <p className={styles.lead}>
              Setup, conversation, architecture, and the next engineering step.
              Explore the groups or use the CLI help for the full executable
              catalog.
            </p>
            <Code>omnix --help</Code>
            <p className={styles.caveat}>
              Omnix account linking is optional. Remote sessions require an
              authorized, linked device, a compatible server with sessions
              enabled, and local confirmation. History reads local outcomes
              offline.
            </p>
          </div>
          <div className={styles.commandGroups}>
            {primaryGroups.map((group) => (
              <details key={group.id} open className={styles.commandGroup}>
                <summary>
                  <h3>{group.title}</h3>
                  <span>{group.commands.length} commands</span>
                </summary>
                <p>{group.description}</p>
                <CommandRows groupId={group.id} />
              </details>
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
        title="Architecture you explicitly ask for."
        eyebrow="05 / From context to structure"
        tabIndex={-1}
        className={styles.proofSection}
      >
        <div className={styles.architectHeader}>
          <p className={styles.lead}>
            Run <Code>omnix architect</Code> explicitly. Saved context informs
            the Architect. The result is a validated blueprint you can inspect.
          </p>
          <Badge status="available" />
        </div>
        <div className={styles.architectLayout}>
          <ol className={styles.architectFlow}>
            {architectFlow.map((step, index) => (
              <li key={step.title}>
                <span className={styles.flowNumber} aria-hidden="true">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div>
                  <h3>{step.title}</h3>
                  <p>{step.detail}</p>
                  <Code>{step.evidence}</Code>
                </div>
              </li>
            ))}
          </ol>
          <aside
            className={styles.evidence}
            aria-label="Explicit workflow invocation"
          >
            <CodeBlock
              label="You invoke the specialist"
              code="omnix architect"
              copyable
            />
            <p>
              Command reference. This is a separate invocation, not a hidden
              action triggered by chat.
            </p>
            <h3>New project transcript excerpt</h3>
            <Transcript state={terminalDemo[2]} excerpt />
            <p>
              The captured Atlas blueprint is newly initialized. It has not been
              generated by an Architect run.
            </p>
          </aside>
        </div>
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
