"use client";

import { useState, useSyncExternalStore, type ReactNode } from "react";
import { Button } from "@/components/ui/button";
import styles from "./journey.module.css";

type ExplorerStage = {
  id: string;
  title: string;
  kind: string;
  handoff: string;
  detail: string;
  content: ReactNode;
};

const wideQuery = "(min-width: 75rem)";
function subscribe(onChange: () => void) {
  const media = window.matchMedia(wideQuery);
  media.addEventListener("change", onChange);
  return () => media.removeEventListener("change", onChange);
}
const clientSnapshot = () =>
  window.matchMedia(wideQuery).matches ? "wide" : "vertical";
const serverSnapshot = () => "static";

function Explanation({ stage }: { stage: ExplorerStage }) {
  return (
    <div
      id="journey-explanation"
      className={styles.explanation}
      role="region"
      aria-labelledby="journey-handoff"
    >
      <div key={stage.id} className={styles.detail}>
        <h3 id="journey-handoff">{stage.handoff}</h3>
        <p>{stage.detail}</p>
      </div>
    </div>
  );
}

export function JourneyExplorer({ stages }: { stages: ExplorerStage[] }) {
  const [current, setCurrent] = useState(0);
  const mode = useSyncExternalStore(subscribe, clientSnapshot, serverSnapshot);
  const ready = mode !== "static";
  const selected = stages[current];
  if (!selected) return null;

  return (
    <div>
      <ol className={styles.route} aria-label="From goal to saved blueprint">
        {stages.map((stage, index) => (
          <li
            key={stage.id}
            className={styles.stage}
            data-kind={stage.kind}
            data-current={ready && index === current}
          >
            <h3 className={styles.stageTitle}>
              {ready ? (
                <Button
                  variant="ghost"
                  className={styles.stageButton}
                  aria-current={index === current ? "step" : undefined}
                  aria-controls="journey-explanation"
                  onClick={() => setCurrent(index)}
                >
                  <span className={styles.number} aria-hidden="true">
                    {index + 1}
                  </span>
                  {stage.title}
                </Button>
              ) : (
                <span className={styles.stageLabel}>
                  <span className={styles.number} aria-hidden="true">
                    {index + 1}
                  </span>
                  {stage.title}
                </span>
              )}
            </h3>
            {stage.content}
            {mode === "vertical" && index === current ? (
              <div className={styles.inlineExplanation}>
                <Explanation stage={selected} />
              </div>
            ) : null}
          </li>
        ))}
      </ol>
      {mode !== "vertical" ? (
        <div className={styles.inspector}>
          <div className={styles.controls} data-ready={ready}>
            <p className={styles.position} role="status" aria-atomic="true">
              Stage {current + 1} of {stages.length}: {selected.title}
            </p>
            <div className={styles.actions}>
              <Button
                variant="secondary"
                onClick={() => setCurrent((value) => Math.max(0, value - 1))}
                disabled={current === 0}
              >
                Previous stage
              </Button>
              <Button
                variant="secondary"
                onClick={() =>
                  setCurrent((value) => (value + 1) % stages.length)
                }
              >
                {current === stages.length - 1
                  ? "Restart journey"
                  : "Next stage"}
              </Button>
            </div>
          </div>
          <Explanation stage={selected} />
        </div>
      ) : null}
    </div>
  );
}
