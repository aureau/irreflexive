import Link from "next/link";
import { MenuIcon, SearchIcon } from "@/components/icons";

export function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-[var(--color-rule)] bg-[var(--color-paper)]/85 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <button
          type="button"
          aria-label="Open menu"
          className="text-[var(--color-ink-muted)] transition-colors hover:text-[var(--color-ink)]"
        >
          <MenuIcon width={20} height={20} />
        </button>

        <Link href="/" aria-label="Irreflexive home" className="flex items-center gap-2">
          <span aria-hidden className="h-7 w-px bg-[var(--color-rule-strong)]" />
          <span className="masthead-title text-[1.05rem] leading-tight">
            Irreflexive
          </span>
        </Link>

        <button
          type="button"
          aria-label="Search"
          className="text-[var(--color-ink-muted)] transition-colors hover:text-[var(--color-ink)]"
        >
          <SearchIcon width={18} height={18} />
        </button>
      </div>
    </header>
  );
}
