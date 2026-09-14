"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import styles from "./review.module.css";

export function ActionExamples() {
  const [message, setMessage] = useState("");
  return (
    <div>
      <div className={styles.row}>
        <Button onClick={() => setMessage("Primary action activated.")}>
          Primary action
        </Button>
        <Button
          variant="secondary"
          onClick={() => setMessage("Secondary action activated.")}
        >
          Secondary action
        </Button>
        <Button
          variant="ghost"
          onClick={() => setMessage("Ghost action activated.")}
        >
          Ghost action
        </Button>
      </div>
      <p role="status" className={styles.feedback}>
        {message}
      </p>
      <div className={styles.row}>
        <Button disabled>Disabled action</Button>
        <Button variant="secondary" loading loadingLabel="Working…">
          Loading example
        </Button>
      </div>
    </div>
  );
}
