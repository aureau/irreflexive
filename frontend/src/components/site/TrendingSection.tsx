"use client";

import { useMemo, useState } from "react";
import { HASHTAGS, articlesByTag } from "@/lib/mock-articles";
import type { HashTag } from "@/types";
import { DotIcon, StarIcon } from "@/components/icons";
import { CardDeck } from "./CardDeck";
import { RelatedRow } from "./RelatedRow";

export function TrendingSection() {
  const [active, setActive] = useState<HashTag>(HASHTAGS[0]);

  const { deck, related } = useMemo(() => {
    const pool = articlesByTag(active);
    return {
      deck: pool.slice(0, 3),
      related: pool.slice(1, 5),
    };
  }, [active]);

  return (
    <section
      id="trending"
      className="section-band relative py-14 sm:py-20"
      aria-label="Trending stories"
    >
      <div className="mx-auto flex max-w-5xl flex-col items-center gap-8 px-6 sm:gap-10">
        {/* hashtag pills row */}
        <nav aria-label="Topics" className="w-full">
          <ul className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2">
            {HASHTAGS.map((tag) => {
              const isActive = active === tag;
              return (
                <li key={tag} className="flex items-center gap-1.5">
                  <button
                    type="button"
                    data-active={isActive}
                    onClick={() => setActive(tag)}
                    className="hash-pill"
                  >
                    #{tag}
                  </button>
                  {isActive && (
                    <DotIcon
                      width={8}
                      height={8}
                      className="text-[var(--color-accent)]"
                    />
                  )}
                </li>
              );
            })}
          </ul>
        </nav>

        {/* hero deck */}
        <div className="w-full">
          <p className="eyebrow mb-3 text-center">Trending</p>
          <CardDeck articles={deck} />
        </div>

        {/* follow row */}
        <div className="flex w-full max-w-2xl flex-wrap items-center justify-between gap-3 text-sm text-[var(--color-ink-muted)]">
          <p>
            Seeing news on{" "}
            <span className="font-semibold text-[var(--color-ink)]">
              #{active}
            </span>
          </p>
          <button
            type="button"
            className="inline-flex items-center gap-1.5 rounded-full border border-[var(--color-rule)] bg-[var(--color-paper)] px-3 py-1 text-xs font-medium text-[var(--color-ink)] transition-colors hover:border-[var(--color-rule-strong)]"
          >
            <StarIcon
              width={12}
              height={12}
              className="text-[var(--color-mark)]"
            />
            Follow
          </button>
        </div>

        {/* related row */}
        <div className="mt-2 w-full">
          <RelatedRow articles={related} />
        </div>
      </div>
    </section>
  );
}
