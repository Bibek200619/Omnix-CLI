"use client";

import { useRef, useState, useSyncExternalStore } from "react";
import { Button } from "@/components/ui/button";
import { CopyButton } from "@/components/ui/copy-button";
import { demoCommands, terminalDemo } from "@/content/terminal-demo";
import { Transcript } from "./transcript";
import styles from "./hero-terminal.module.css";

const subscribe = () => () => {};
const clientSnapshot = () => true;
const serverSnapshot = () => false;

export function HeroTerminal() {
  const [current, setCurrent] = useState(0);
  const [terminalTheme, setTerminalTheme] = useState<
    "black" | "blue" | "light"
  >("black");
  const tabs = useRef<(HTMLButtonElement | null)[]>([]);
  const ready = useSyncExternalStore(subscribe, clientSnapshot, serverSnapshot);

  return (
    <div
      id="hero-cli"
      role="region"
      aria-labelledby="terminal-title"
      tabIndex={-1}
      className={styles.demo}
    >
      <div className={styles.heading}>
        <h2 id="terminal-title">A real starting point.</h2>
        <span aria-hidden="true">0{current + 1} / 03</span>
      </div>
      <label className={styles.themePicker}>
        Terminal appearance
        <select
          value={terminalTheme}
          onChange={(event) => {
            const value = event.currentTarget.value;
            if (value === "black" || value === "blue" || value === "light") {
              setTerminalTheme(value);
            }
          }}
        >
          <option value="black">Black</option>
          <option value="blue">Blue</option>
          <option value="light">White</option>
        </select>
      </label>
      <div
        className={styles.tabs}
        role="tablist"
        aria-label="CLI demonstration"
        data-ready={ready}
      >
        {terminalDemo.map((state, index) => (
          <Button
            key={state.id}
            ref={(element) => {
              tabs.current[index] = element;
            }}
            variant={current === index ? "primary" : "ghost"}
            role="tab"
            id={`demo-tab-${state.id}`}
            aria-controls={`demo-panel-${state.id}`}
            aria-selected={current === index}
            tabIndex={current === index ? 0 : -1}
            onClick={() => setCurrent(index)}
            onKeyDown={(event) => {
              let next: number;
              if (event.key === "ArrowRight")
                next = (index + 1) % terminalDemo.length;
              else if (event.key === "ArrowLeft")
                next = (index + terminalDemo.length - 1) % terminalDemo.length;
              else if (event.key === "Home") next = 0;
              else if (event.key === "End") next = terminalDemo.length - 1;
              else return;
              event.preventDefault();
              setCurrent(next);
              tabs.current[next]?.focus();
            }}
          >
            {state.label}
          </Button>
        ))}
      </div>
      {terminalDemo.map((state, index) => (
        <div
          key={state.id}
          id={`demo-panel-${state.id}`}
          role="tabpanel"
          aria-label={state.label}
          aria-labelledby={`demo-tab-${state.id}`}
          hidden={current !== index}
          className={styles.panel}
        >
          <Transcript state={state} theme={terminalTheme} />
          <p data-theme="dark" className={styles.caption}>
            {state.caption}
          </p>
        </div>
      ))}
      <div data-theme="dark" className={styles.notes}>
        <p>
          Source-verified transcript. Executed locally in a scratch project; no
          model API calls. These controls belong to the website. In a source
          checkout, prefix each command with <code>uv run --frozen</code>.
        </p>
        <CopyButton text={demoCommands} label="Copy demo commands" />
      </div>
      <noscript>
        <div data-theme="dark" className={styles.fallback}>
          {terminalDemo.slice(1).map((state) => (
            <details key={state.id}>
              <summary>{state.label}</summary>
              <Transcript state={state} />
              <p>{state.caption}</p>
            </details>
          ))}
        </div>
      </noscript>
    </div>
  );
}
