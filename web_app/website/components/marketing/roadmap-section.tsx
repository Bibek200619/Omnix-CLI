import { Badge } from "@/components/ui/badge";
import { Container } from "@/components/ui/container";
import { Link } from "@/components/ui/link";
import { Section } from "@/components/ui/section";
import { implementedMilestones, roadmap } from "@/content/roadmap";
import { repository } from "@/lib/constants";
import styles from "./roadmap.module.css";

export function RoadmapSection() {
  return (
    <Container>
      <Section
        id="roadmap"
        title="The engineering workflow, stage by stage."
        tabIndex={-1}
        className={styles.section}
      >
        <p className={styles.intro}>
          From local project state to coordinated builds. Available means
          implemented in the source preview.
        </p>
        <div className={styles.layout}>
          <div>
            <h3 className={styles.groupTitle}>Implemented in source preview</h3>
            <ol className={styles.timeline}>
              {implementedMilestones.map((milestone, index) => (
                <li key={milestone.id}>
                  <span className={styles.marker} aria-hidden="true">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <div className={styles.milestone}>
                    <div className={styles.rowHeading}>
                      <h4>{milestone.title}</h4>
                      <Badge status={milestone.status} />
                    </div>
                    <p>{milestone.summary}</p>
                    <Link
                      href={`${repository.url}/blob/main/ai-cli/omnix_cli/${milestone.evidence[0]}`}
                      aria-label={`${milestone.title} implementation`}
                    >
                      View implementation
                    </Link>
                  </div>
                </li>
              ))}
            </ol>
          </div>
          <div className={styles.future}>
            <h3 className={styles.groupTitle}>Future provider adapters</h3>
            <p className={styles.futureIntro}>
              Configuration boundaries exist. Live generation remains to be
              implemented for these providers.
            </p>
            <ul className={styles.futureList}>
              {roadmap.map((item) => (
                <li key={item.id}>
                  <h4>{item.title}</h4>
                  <Badge status={item.status} />
                </li>
              ))}
            </ul>
            <p className={styles.note}>No delivery dates are announced.</p>
          </div>
        </div>
        <p className={styles.boundary}>
          Source availability does not establish a stable release. Generated
          artifacts and model-assisted reports do not prove that an application
          builds, passes tests, or deploys.
        </p>
      </Section>
    </Container>
  );
}
