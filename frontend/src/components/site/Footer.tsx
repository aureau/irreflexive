import Link from "next/link";
import type { FooterSection } from "@/types";

const SECTIONS: FooterSection[] = [
  {
    title: "Read",
    links: [
      { label: "Trending", href: "#trending" },
      { label: "Explore Latest", href: "#explore" },
      { label: "Topics", href: "#trending" },
    ],
  },
  {
    title: "Project",
    links: [
      { label: "Mission", href: "#mission" },
      { label: "Method", href: "#" },
      { label: "Notes", href: "#" },
    ],
  },
  {
    title: "Build",
    links: [
      { label: "GitHub", href: "#" },
      { label: "API", href: "#" },
      { label: "Changelog", href: "#" },
    ],
  },
  {
    title: "Legal",
    links: [
      { label: "Privacy", href: "#" },
      { label: "Terms", href: "#" },
      { label: "Contact", href: "#" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="border-t border-[var(--color-rule)] bg-[var(--color-paper-2)]">
      <div className="mx-auto max-w-7xl px-6 py-14">
        <div className="grid gap-10 md:grid-cols-[1.5fr_repeat(4,1fr)]">
          <div className="space-y-4">
            <Link href="/" className="flex items-center gap-2">
              <span
                aria-hidden
                className="h-7 w-px bg-[var(--color-rule-strong)]"
              />
              <span className="masthead-title text-[1.05rem] leading-tight">
                Irreflexive
              </span>
            </Link>
            <p className="max-w-sm text-sm text-[var(--color-ink-muted)]">
              A reading tool that surfaces political lean in news articles —
              calibrated against a balanced corpus, transparent about the math.
            </p>
          </div>

          {SECTIONS.map((s) => (
            <div key={s.title}>
              <p className="eyebrow mb-3">{s.title}</p>
              <ul className="space-y-2 text-sm text-[var(--color-ink-muted)]">
                {s.links.map((l) => (
                  <li key={l.label}>
                    <Link
                      href={l.href}
                      className="transition-colors hover:text-[var(--color-ink)]"
                    >
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="rule-line mt-12 flex flex-col items-start justify-between gap-2 pt-6 text-xs text-[var(--color-ink-dim)] sm:flex-row sm:items-center">
          <p>© {new Date().getFullYear()} Irreflexive. Built in the open.</p>
          <p>v0 · mock data · no backend connected</p>
        </div>
      </div>
    </footer>
  );
}
