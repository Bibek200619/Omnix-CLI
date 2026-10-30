"use client";

import { useEffect, useId, useRef, useSyncExternalStore } from "react";
import { Button } from "@/components/ui/button";
import { Link } from "@/components/ui/link";
import styles from "./download.module.css";

const subscribe = () => () => {};
const clientSnapshot = () => true;
const serverSnapshot = () => false;

export function DownloadAction({ className = "" }: { className?: string }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const restoreFocus = useRef(true);
  const id = useId();
  const ready = useSyncExternalStore(subscribe, clientSnapshot, serverSnapshot);

  useEffect(() => {
    const desktop = window.matchMedia("(min-width: 75rem)");
    const dismissOnLayoutChange = () => {
      if (dialog.current?.open) dialog.current.close();
    };
    desktop.addEventListener("change", dismissOnLayoutChange);
    return () => desktop.removeEventListener("change", dismissOnLayoutChange);
  }, []);

  return (
    <>
      <Button
        ref={trigger}
        className={`${styles.trigger} download-enhanced ${className}`}
        data-ready={ready}
        aria-haspopup="dialog"
        onClick={() => {
          restoreFocus.current = true;
          dialog.current?.showModal();
          dialog.current
            ?.querySelector<HTMLAnchorElement>("[data-install-action]")
            ?.focus();
        }}
      >
        Download Omnix <span aria-hidden="true">→</span>
      </Button>
      <dialog
        ref={dialog}
        data-theme="dark"
        className={styles.dialog}
        aria-labelledby={`${id}-title`}
        aria-describedby={`${id}-description`}
        onClose={() => {
          if (!restoreFocus.current) return;
          const opener = trigger.current;
          const target =
            opener?.checkVisibility?.() === false
              ? document.querySelector<HTMLAnchorElement>(
                  'a[aria-label="Omnix home"]',
                )
              : opener;
          target?.focus({ preventScroll: true });
        }}
        onKeyDown={(event) => {
          if (event.key !== "Tab") return;
          const controls = event.currentTarget.querySelectorAll<HTMLElement>(
            "button:not(:disabled), a[href]",
          );
          const first = controls[0];
          const last = controls[controls.length - 1];
          if (!first || !last) return;
          if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
          } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
          }
        }}
        onClick={(event) => {
          if (event.target !== event.currentTarget) return;
          const bounds = event.currentTarget.getBoundingClientRect();
          if (
            event.clientX < bounds.left ||
            event.clientX > bounds.right ||
            event.clientY < bounds.top ||
            event.clientY > bounds.bottom
          )
            dialog.current?.close();
        }}
      >
        <div className={styles.top}>
          <div>
            <p className={styles.eyebrow}>Availability</p>
            <h2 id={`${id}-title`}>Get Omnix</h2>
          </div>
          <Button variant="secondary" onClick={() => dialog.current?.close()}>
            Close
          </Button>
        </div>
        <p id={`${id}-description`} className={styles.intro}>
          CLI setup is available now. The Omnix app is planned.
        </p>
        <section className={styles.option} aria-labelledby={`${id}-cli`}>
          <div className={styles.optionHeading}>
            <h3 id={`${id}-cli`}>Omnix CLI</h3>
            <span className={styles.preview}>Source preview</span>
          </div>
          <p>Run Omnix in your terminal. Install from source.</p>
          <Link
            href="#download"
            variant="primary"
            data-install-action
            onClick={(event) => {
              if (
                event.metaKey ||
                event.ctrlKey ||
                event.shiftKey ||
                event.altKey
              )
                return;
              restoreFocus.current = false;
              dialog.current?.close();
              document
                .getElementById("download")
                ?.focus({ preventScroll: true });
            }}
          >
            View CLI setup <span aria-hidden="true">→</span>
          </Link>
        </section>
        <section className={styles.option} aria-labelledby={`${id}-app`}>
          <div className={styles.optionHeading}>
            <h3 id={`${id}-app`}>Omnix app</h3>
            <span className={styles.future}>Coming later</span>
          </div>
          <p>A dedicated Omnix app is planned.</p>
          <Button variant="secondary" disabled>
            Coming later
          </Button>
        </section>
        <p className={styles.note}>
          The CLI is a source preview. No app binary is available.
        </p>
      </dialog>
      <noscript>
        <style>{".download-enhanced { display: none !important; }"}</style>
        <Link href="#download" variant="primary">
          Download Omnix
        </Link>
      </noscript>
    </>
  );
}
