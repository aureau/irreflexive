"use client";

import { useState } from "react";
import { ARTICLES } from "@/lib/mock-articles";
import type { TimelineBucket } from "@/types";
import { ClockIcon } from "@/components/icons";
import { FeaturedArticle } from "./FeaturedArticle";
import { cn } from "@/lib/utils";

const BUCKETS: TimelineBucket[] = ["Today", "Yesterday", "This Week", "This Month"];

export function ExploreLatest() {
  const [bucket, setBucket] = useState<TimelineBucket>(BUCKETS[0]);

  return (
    <section id="explore" className="py-16 sm:py-20" aria-label="Explore latest">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mb-8 flex items-end justify-between gap-4">
          <h2 className="font-display text-3xl sm:text-4xl">Explore Latest</h2>
          <div className="hidden h-px flex-1 self-center bg-gradient-to-r from-[var(--color-rule)] via-[var(--color-accent)]/40 to-transparent sm:block" />
        </div>

        <div className="grid grid-cols-1 gap-10 lg:grid-cols-[180px_minmax(0,1fr)]">
          <nav aria-label="Timeline" className="relative">
            <ul className="space-y-3">
              {BUCKETS.map((b, i) => {
                const isActive = bucket === b;
                return (
                  <li key={b} className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => setBucket(b)}
                      className={cn(
                        "text-sm transition-colors",
                        isActive
                          ? "font-semibold text-[var(--color-ink)] underline decoration-[var(--color-mark)] decoration-2 underline-offset-4"
                          : "text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]"
                      )}
                    >
                      {b}
                    </button>
                    {i === 0 && (
                      <ClockIcon
                        width={14}
                        height={14}
                        className="text-[var(--color-ink-dim)]"
                      />
                    )}
                  </li>
                );
              })}
            </ul>
          </nav>

          <div className="min-w-0">
            <div className="grid gap-6 sm:grid-cols-2">
              {ARTICLES.slice(0, 4).map((a) => (
                <FeaturedArticle key={a.id} article={a} />
              ))}
            </div>

            <div className="mt-8 flex justify-center">
              <button
                type="button"
                className="pill-link"
                aria-label="Load more articles"
              >
                Load more
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
