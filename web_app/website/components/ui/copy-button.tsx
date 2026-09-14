"use client";

import { useEffect, useId, useRef, useState } from "react";
import { Button } from "./button";
import styles from "./primitives.module.css";

type CopyButtonProps = { text: string; label?: string };
type CopyStatus = "idle" | "copying" | "copied" | "manual";

export function CopyButton({ text, label = "Copy command" }: CopyButtonProps) {
  // A changed command gets fresh state rather than retaining stale success feedback.
  return <CopyControl key={text} text={text} label={label} />;
}

function CopyControl({ text, label }: Required<CopyButtonProps>) {
  const [status, setStatus] = useState<CopyStatus>("idle");
  const busy = useRef(false);
  const manualText = useRef<HTMLTextAreaElement>(null);
  const id = useId();

  useEffect(() => {
    if (status === "manual") {
      manualText.current?.focus();
      manualText.current?.select();
    }
  }, [status]);

  async function copy() {
    if (busy.current) return;
    busy.current = true;
    setStatus("copying");
    try {
      if (!navigator.clipboard?.writeText)
        throw new Error("Clipboard unavailable");
      await navigator.clipboard.writeText(text);
      setStatus("copied");
    } catch {
      setStatus("manual");
    } finally {
      busy.current = false;
    }
  }

  const message =
    status === "copied"
      ? "Copied to clipboard."
      : status === "manual"
        ? "Automatic copy is unavailable. Press Ctrl+C or ⌘C, or touch and hold the selected text to copy."
        : "";

  return (
    <div className={styles.copyControl}>
      <Button
        variant="secondary"
        onClick={copy}
        loading={status === "copying"}
        loadingLabel="Copying…"
        aria-describedby={`${id}-status`}
      >
        {label}
      </Button>
      <p
        id={`${id}-status`}
        role="status"
        aria-atomic="true"
        className={styles.copyStatus}
      >
        {message}
      </p>
      {status === "manual" ? (
        <div className={styles.manualCopy}>
          <label htmlFor={`${id}-text`}>Text to copy manually</label>
          <textarea
            id={`${id}-text`}
            ref={manualText}
            readOnly
            value={text}
            rows={3}
            spellCheck={false}
            aria-describedby={`${id}-status`}
          />
        </div>
      ) : null}
    </div>
  );
}
