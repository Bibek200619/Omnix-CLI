"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { Button } from "@/components/ui/button";
import { Link } from "@/components/ui/link";
import { hero, navigation } from "@/content/hero";
import styles from "./header.module.css";

const subscribe = () => () => {};
const hydratedSnapshot = () => true;
const serverSnapshot = () => false;

export function MobileNav() {
  const [open, setOpen] = useState(false);
  const openRef = useRef(false);
  const restoreFocusRef = useRef(false);
  const focusTargetRef = useRef<"trigger" | "brand">("trigger");
  const trigger = useRef<HTMLButtonElement>(null);
  const root = useRef<HTMLDivElement>(null);
  const hydrated = useSyncExternalStore(
    subscribe,
    hydratedSnapshot,
    serverSnapshot,
  );

  useEffect(() => {
    const desktop = window.matchMedia("(min-width: 75rem)");
    const reset = () => {
      const shouldRestoreFocus =
        openRef.current || root.current?.contains(document.activeElement);
      openRef.current = false;
      restoreFocusRef.current = Boolean(shouldRestoreFocus);
      focusTargetRef.current = desktop.matches ? "brand" : "trigger";
      setOpen(false);
      if (desktop.matches && shouldRestoreFocus)
        window.requestAnimationFrame(() => {
          document
            .querySelector<HTMLAnchorElement>('a[aria-label="Omnix home"]')
            ?.focus();
        });
    };
    desktop.addEventListener("change", reset);
    window.addEventListener("resize", reset);
    return () => {
      desktop.removeEventListener("change", reset);
      window.removeEventListener("resize", reset);
    };
  }, []);

  useEffect(() => {
    if (!open) return;
    const closeOnFocusOutside = (event: FocusEvent) => {
      if (root.current?.contains(event.target as Node)) return;
      openRef.current = false;
      restoreFocusRef.current = false;
      setOpen(false);
    };
    document.addEventListener("focusin", closeOnFocusOutside);
    return () => document.removeEventListener("focusin", closeOnFocusOutside);
  }, [open]);

  useEffect(() => {
    if (!open && restoreFocusRef.current) {
      restoreFocusRef.current = false;
      if (focusTargetRef.current === "brand") {
        document
          .querySelector<HTMLAnchorElement>('a[aria-label="Omnix home"]')
          ?.focus();
      } else trigger.current?.focus();
    }
  }, [open]);

  function close() {
    openRef.current = false;
    restoreFocusRef.current = true;
    focusTargetRef.current = "trigger";
    setOpen(false);
  }

  return (
    <div
      ref={root}
      className={styles.mobile}
      onKeyDown={(event) => {
        if (event.key === "Escape" && open) {
          event.preventDefault();
          close();
        }
      }}
    >
      <Button
        ref={trigger}
        variant="secondary"
        className={styles.trigger}
        data-ready={hydrated}
        aria-expanded={open}
        aria-controls="mobile-navigation"
        onClick={() => {
          if (open) close();
          else {
            openRef.current = true;
            setOpen(true);
          }
        }}
      >
        {open ? "Close menu" : "Menu"}
        <span aria-hidden="true">{open ? "−" : "+"}</span>
      </Button>
      <nav
        id="mobile-navigation"
        aria-label="Mobile"
        hidden={!open}
        className={styles.panel}
      >
        {[
          ...navigation,
          { label: "Source preview", href: hero.primary.href },
        ].map((item) => (
          <Link
            key={item.href}
            href={item.href}
            variant="ghost"
            onClick={(event) => {
              if (
                event.metaKey ||
                event.ctrlKey ||
                event.shiftKey ||
                event.altKey
              )
                return;
              openRef.current = false;
              restoreFocusRef.current = false;
              setOpen(false);
              if (item.href.startsWith("#")) {
                document
                  .getElementById(item.href.slice(1))
                  ?.focus({ preventScroll: true });
              }
            }}
          >
            {item.label}
          </Link>
        ))}
      </nav>
      <noscript>
        <nav aria-label="Mobile" className={styles.fallback}>
          {navigation.map((item) => (
            <Link key={item.href} href={item.href}>
              {item.label}
            </Link>
          ))}
          <Link href={hero.primary.href}>Source preview</Link>
        </nav>
      </noscript>
    </div>
  );
}
