import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";
import { Badge } from "@/components/ui/badge";
import { Code } from "@/components/ui/code";
import { journey, journeySteps, type JourneyStep } from "@/content/journey";
import { roadmap } from "@/content/roadmap";
import { JourneyExplorer } from "./journey-explorer";
import styles from "./journey.module.css";

function StageBody({ step }: { step: JourneyStep }) {
  return (
    <div className={styles.stageBody}>
      {step.status ? <Badge status={step.status} /> : null}
      <p>{step.summary}</p>
      {step.files ? (
        <div className={styles.context}>
          <Code>.project/</Code>
          <ul aria-label="Saved context files">
            {step.files.map((file) => (
              <li key={file}>
                <Code>{file}</Code>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {step.command ? <Code>{step.command}</Code> : null}
    </div>
  );
}

export function OrchestrationJourney() {
  return (
    <Container>
      <Section
        id="how-it-works"
        title={journey.title}
        tabIndex={-1}
        className={styles.journey}
      >
        <div className={styles.introduction}>
          <p className={styles.lead}>{journey.introduction}</p>
          <p className={styles.boundary}>{journey.boundary}</p>
        </div>
        <div className={styles.caption}>
          <span className={styles.available}>{journey.availability}</span>
          <span>Illustrated workflow · no commands run in your browser</span>
        </div>
        <JourneyExplorer
          stages={journeySteps.map((step) => ({
            id: step.id,
            title: step.title,
            kind: step.kind,
            handoff: step.handoff,
            detail: step.detail,
            content: <StageBody step={step} />,
          }))}
        />
        <div className={styles.branches}>
          <div className={styles.build}>
            <div className={styles.branchTitle}>
              <h3>Continue with orchestration</h3>
              <Badge status="available" />
            </div>
            <p>{journey.buildSummary}</p>
            <Code>{journey.buildCommand}</Code>
            <p className={styles.limit}>{journey.buildLimit}</p>
          </div>
          <aside
            className={styles.roadmap}
            aria-labelledby="journey-roadmap-heading"
          >
            <div className={styles.branchTitle}>
              <h3 id="journey-roadmap-heading">More provider choices</h3>
              <Badge status="roadmap" />
            </div>
            <p>
              OpenAI has a live adapter. These adapters have configuration
              boundaries only; live generation is not implemented.
            </p>
            <ul aria-label="Roadmap provider adapters">
              {roadmap.map((item) => (
                <li key={item.id}>{item.title}</li>
              ))}
            </ul>
          </aside>
        </div>
      </Section>
    </Container>
  );
}
