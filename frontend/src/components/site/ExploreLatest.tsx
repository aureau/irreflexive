"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { ClockIcon } from "@/components/icons";

interface LatestArticle {
  outlet: string;
  title: string;
  url: string;
  published_at: string | null;
  summary?: string | null;
  image_url?: string | null;
  scored: boolean;
  label: string | null;
  confidence: number | null;
  model_version: string | null;
  scoring_error: string | null;
}

interface ArticleError {
  outlet: string;
  message: string;
}

interface LatestArticlesResponse {
  articles: LatestArticle[];
  errors: ArticleError[];
  fetched_at: string;
}

type LoadState = "idle" | "loading" | "ready" | "error";

function formatDate(value: string | null): string {
  if (!value) return "No date";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "No date";

  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function stripHtml(value: string): string {
  return value.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}

function groupByOutlet(articles: LatestArticle[]): Array<[string, LatestArticle[]]> {
  const groups = new Map<string, LatestArticle[]>();

  for (const article of articles) {
    const existing = groups.get(article.outlet);
    if (existing) {
      existing.push(article);
    } else {
      groups.set(article.outlet, [article]);
    }
  }

  return Array.from(groups.entries());
}

function placeholderFor(index: number): string {
  return `/images/article-placeholder-${(index % 4) + 1}.svg`;
}

function imageFor(article: LatestArticle, index: number): string {
  return article.image_url ?? placeholderFor(index);
}

export function ExploreLatest() {
  const [data, setData] = useState<LatestArticlesResponse | null>(null);
  const [state, setState] = useState<LoadState>("idle");
  const [message, setMessage] = useState<string | null>(null);

  const loadArticles = useCallback(async () => {
    setState("loading");
    setMessage(null);

    try {
      const response = await fetch("/api/articles/latest", { cache: "no-store" });
      const payload = (await response.json()) as LatestArticlesResponse;

      if (!response.ok) {
        throw new Error(payload.errors?.[0]?.message ?? "Could not load latest articles.");
      }

      setData(payload);
      setState("ready");
    } catch (error) {
      setState("error");
      setMessage(error instanceof Error ? error.message : "Could not load latest articles.");
    }
  }, []);

  useEffect(() => {
    void loadArticles();
  }, [loadArticles]);

  const groupedArticles = useMemo(() => {
    return groupByOutlet(data?.articles ?? []);
  }, [data]);

  return (
    <section id="explore" className="py-16 sm:py-20" aria-label="Explore latest">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="eyebrow">Live RSS</p>
            <h2 className="mt-2 font-display text-3xl sm:text-4xl">Explore Latest</h2>
          </div>
          <div className="flex items-center gap-3">
            {data?.fetched_at && (
              <p className="hidden text-xs text-[var(--color-ink-dim)] sm:block">
                Updated {formatDate(data.fetched_at)}
              </p>
            )}
            <button
              type="button"
              onClick={() => void loadArticles()}
              disabled={state === "loading"}
              className="pill-link disabled:cursor-wait disabled:opacity-60"
              aria-label="Refresh latest articles"
            >
              <ClockIcon width={14} height={14} />
              {state === "loading" ? "Refreshing" : "Refresh"}
            </button>
          </div>
        </div>

        {state === "loading" && !data && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="card h-44 animate-pulse bg-[var(--color-paper-2)]" />
            ))}
          </div>
        )}

        {state === "error" && (
          <div className="card border-[var(--color-bear)]/25 p-6">
            <p className="text-sm font-semibold text-[var(--color-bear)]">Latest articles unavailable</p>
            <p className="mt-2 text-sm text-[var(--color-ink-muted)]">{message}</p>
          </div>
        )}

        {state !== "error" && data?.errors && data.errors.length > 0 && (
          <div className="mb-6 rounded-md border border-[var(--color-mark)]/40 bg-[var(--color-paper-2)] p-4">
            <p className="text-sm font-semibold text-[var(--color-ink)]">Some feeds did not load</p>
            <ul className="mt-2 space-y-1 text-sm text-[var(--color-ink-muted)]">
              {data.errors.map((error) => (
                <li key={`${error.outlet}-${error.message}`}>
                  {error.outlet}: {error.message}
                </li>
              ))}
            </ul>
          </div>
        )}

        {state === "ready" && groupedArticles.length === 0 && (
          <div className="card p-6 text-sm text-[var(--color-ink-muted)]">
            No articles returned from the configured feeds.
          </div>
        )}

        {groupedArticles.length > 0 && (
          <div className="space-y-10">
            {groupedArticles.map(([outlet, articles]) => (
              <section key={outlet} aria-label={`${outlet} latest articles`}>
                <div className="mb-4 flex items-center gap-4">
                  <h3 className="font-display text-2xl">{outlet}</h3>
                  <div className="h-px flex-1 bg-[var(--color-rule)]" />
                </div>

                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {articles.map((article, index) => (
                    <article key={article.url} className="card flex min-h-44 flex-col p-5">
                      <div className="relative mb-4 aspect-[16/9] overflow-hidden rounded-md bg-[var(--color-paper-3)]">
                        <Image
                          src={imageFor(article, index)}
                          alt=""
                          fill
                          sizes="(min-width: 1280px) 380px, (min-width: 768px) 45vw, 90vw"
                          className="object-cover"
                        />
                      </div>

                      <div className="mb-4 flex items-center justify-between gap-3 text-xs text-[var(--color-ink-muted)]">
                        <span>{formatDate(article.published_at)}</span>
                        <span className="inline-flex size-7 shrink-0 items-center justify-center rounded-full bg-[var(--color-paper-3)] text-[10px] font-semibold uppercase">
                          {article.outlet.slice(0, 1)}
                        </span>
                      </div>

                      <h4 className="line-clamp-3 text-base font-semibold leading-snug text-[var(--color-ink)]">
                        <Link
                          href={article.url}
                          target="_blank"
                          rel="noreferrer"
                          className="hover:text-[var(--color-accent)]"
                        >
                          {article.title}
                        </Link>
                      </h4>

                      {article.summary && (
                        <p className="mt-3 line-clamp-3 text-sm leading-6 text-[var(--color-ink-muted)]">
                          {stripHtml(article.summary)}
                        </p>
                      )}

                      <div className="mt-auto pt-5">
                        <Link
                          href={article.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-sm font-medium text-[var(--color-accent)] hover:underline"
                        >
                          Open article
                        </Link>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
