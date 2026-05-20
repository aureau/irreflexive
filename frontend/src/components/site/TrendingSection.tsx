"use client";

import { useMemo } from "react";
import { HASHTAGS, articlesByTag } from "@/lib/mock-articles";
import { StarIcon } from "@/components/icons";
import { CardDeck } from "./CardDeck";
import { RelatedRow } from "./RelatedRow";

export function TrendingSection() {
  const active = HASHTAGS[0];

  const { deck, related } = useMemo(() => {
    const pool = articlesByTag(active);
    const deckSlice = pool.slice(0, 3);
    const deckIds = new Set(deckSlice.map((a) => a.id));
    return {
      deck: deckSlice,
      related: pool.filter((a) => !deckIds.has(a.id)).slice(0, 4),
    };
  }, [active]);

  return (
    <section
      id="trending"
      className="section-band relative py-14 sm:py-20"
      aria-label="Trending stories"
    >
      <div className="mx-auto flex max-w-5xl flex-col items-center gap-8 px-6 sm:gap-10">
        {/* hero deck */}
        <div className="w-full">
          <p className="eyebrow mb-3 text-center">Trending</p>
          <CardDeck articles={deck} />
        </div>

        {/* follow row */}
        <div className="flex w-full max-w-2xl flex-wrap items-center justify-between gap-3 text-sm text-[var(--color-ink-muted)]">
          <p>Seeing news in the current topic set</p>
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
