"use client";

import { useEffect, useState } from "react";
import type { Article, BiasLean, HashTag } from "@/types";
import { HASHTAGS, articlesByTag } from "@/lib/mock-articles";
import { StarIcon } from "@/components/icons";
import { CardDeck } from "./CardDeck";
import { RelatedRow } from "./RelatedRow";

interface LatestArticle {
  outlet_id: string;
  outlet: string;
  title: string;
  url: string;
  published_at: string | null;
  summary?: string | null;
  image_url?: string | null;
  scored: boolean;
  label: string | null;
  confidence: number | null;
}

interface LatestArticlesResponse {
  articles: LatestArticle[];
}

const DECK_SIZE = 3;
const RELATED_SIZE = 4;
const FALLBACK_TAG: HashTag = HASHTAGS[0];
const EXCLUDED_OUTLET_IDS = new Set(["bbc_world"]);

const MOCK_POOL = articlesByTag(FALLBACK_TAG);

function placeholderImage(seed: string): string {
  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) {
    hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
  }
  return `/images/article-placeholder-${(hash % 4) + 1}.svg`;
}

function resolveImageUrl(imageUrl: string | null | undefined, seed: string): string {
  if (!imageUrl) return placeholderImage(seed);
  const trimmed = imageUrl.trim();
  if (!trimmed || trimmed === "undefined") return placeholderImage(seed);
  if (
    trimmed.startsWith("/") ||
    trimmed.startsWith("http://") ||
    trimmed.startsWith("https://")
  ) {
    return trimmed;
  }
  return placeholderImage(seed);
}

function leanFromLabel(label: string | null): BiasLean {
  if (label === "left" || label === "right" || label === "center") return label;
  return "center";
}

function biasFromConfidence(label: string | null, confidence: number | null): number {
  if (confidence === null) return 0;
  if (label === "left") return -confidence;
  if (label === "right") return confidence;
  return 0;
}

function formatDate(value: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toISOString().slice(0, 10);
}

function toArticle(item: LatestArticle): Article {
  return {
    id: item.url,
    title: item.title,
    source: item.outlet,
    date: formatDate(item.published_at),
    tag: FALLBACK_TAG,
    image: resolveImageUrl(item.image_url, item.url),
    bias: biasFromConfidence(item.label, item.confidence),
    lean: leanFromLabel(item.label),
    href: item.url,
  };
}

function sampleDistinct<T>(pool: T[], count: number): T[] {
  const copy = [...pool];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy.slice(0, count);
}

function initialSelection(): { deck: Article[]; related: Article[] } {
  return {
    deck: MOCK_POOL.slice(0, DECK_SIZE),
    related: MOCK_POOL.slice(DECK_SIZE, DECK_SIZE + RELATED_SIZE),
  };
}

export function TrendingSection() {
  const [articles, setArticles] = useState<Article[] | null>(null);
  const [errored, setErrored] = useState(false);
  const [{ deck, related }, setSelection] = useState(initialSelection);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const response = await fetch("/api/articles/latest", { cache: "no-store" });
        const payload = (await response.json()) as LatestArticlesResponse;
        if (cancelled) return;
        const mapped = (payload.articles ?? [])
          .filter((a) => a.title && a.url && !EXCLUDED_OUTLET_IDS.has(a.outlet_id))
          .map(toArticle);
        setArticles(mapped);
      } catch {
        if (!cancelled) setErrored(true);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  // Random sampling only after mount so SSR and first client paint match.
  useEffect(() => {
    const pool = articles && articles.length > 0 ? articles : MOCK_POOL;
    const picked = sampleDistinct(pool, DECK_SIZE + RELATED_SIZE);
    setSelection({
      deck: picked.slice(0, DECK_SIZE),
      related: picked.slice(DECK_SIZE, DECK_SIZE + RELATED_SIZE),
    });
  }, [articles]);

  return (
    <section
      id="trending"
      className="section-band relative py-14 sm:py-20"
      aria-label="Trending stories"
    >
      <div className="mx-auto flex max-w-5xl flex-col items-center gap-8 px-6 sm:gap-10">
        <div className="w-full">
          <p className="eyebrow mb-3 text-center">Trending</p>
          <CardDeck articles={deck} autoCycleMs={5000} />
        </div>

        <div className="flex w-full max-w-2xl flex-wrap items-center justify-between gap-3 text-sm text-[var(--color-ink-muted)]">
          <p>
            {errored
              ? "Showing sample stories while the live feed reconnects"
              : ""}
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

        <div className="mt-2 w-full">
          <RelatedRow articles={related} />
        </div>
      </div>
    </section>
  );
}
