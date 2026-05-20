"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import type { Article } from "@/types";
import { BiasBadge } from "./BiasBadge";
import { cn } from "@/lib/utils";

interface CardDeckProps {
  articles: Article[];
}

function CardBody({ article }: { article: Article }) {
  return (
    <>
      <div className="relative aspect-[16/10] w-full overflow-hidden bg-[var(--color-paper-3)]">
        <Image
          src={article.image}
          alt=""
          fill
          sizes="(min-width: 1024px) 640px, 100vw"
          className="object-cover"
        />
      </div>
      <div className="space-y-4 p-5 sm:p-6">
        <h3 className="lede line-clamp-2 font-medium">{article.title}.</h3>
        <div className="flex items-center justify-between gap-3 text-sm">
          <div className="flex min-w-0 items-center gap-2 text-[var(--color-ink-muted)]">
            <span className="inline-flex size-6 shrink-0 items-center justify-center rounded-full bg-[var(--color-paper-3)] text-[10px] font-semibold uppercase">
              {article.source.slice(0, 1)}
            </span>
            <span className="truncate">
              {article.source}
              <span className="mx-2 text-[var(--color-rule-strong)]">|</span>
              {article.date}
            </span>
          </div>
          <BiasBadge value={article.bias} size="md" />
        </div>
      </div>
    </>
  );
}

const SLOT_CLASSES: string[] = [
  "translate-x-0 translate-y-0 scale-100 opacity-100 z-30",
  "translate-x-2.5 translate-y-3.5 scale-[0.97] opacity-70 z-20",
  "translate-x-5 translate-y-7 scale-[0.94] opacity-50 z-10",
];

export function CardDeck({ articles }: CardDeckProps) {
  const [order, setOrder] = useState<string[]>(() => articles.map((a) => a.id));

  useEffect(() => {
    setOrder(articles.map((a) => a.id));
  }, [articles]);

  const promote = (id: string) =>
    setOrder((prev) => [id, ...prev.filter((x) => x !== id)]);

  const slots = order
    .slice(0, 3)
    .map((id) => articles.find((a) => a.id === id))
    .filter((a): a is Article => Boolean(a));

  if (slots.length === 0) return null;

  const front = slots[0];

  return (
    <div className="relative mx-auto w-full max-w-2xl">
      {/* invisible sentinel anchors the container height so peeks bleed
          outside without causing layout shifts when promoting cards */}
      <div aria-hidden className="invisible">
        <div className="card overflow-hidden">
          <CardBody article={front} />
        </div>
      </div>

      {slots.map((article, i) => {
        const positionClass = SLOT_CLASSES[i] ?? SLOT_CLASSES[2];
        const baseClass =
          "absolute inset-0 card overflow-hidden transition-[transform,opacity] duration-500 ease-[cubic-bezier(0.2,0.8,0.2,1)] will-change-transform";

        if (i === 0) {
          return (
            <Link
              key={article.id}
              href={article.href}
              aria-label={`Read: ${article.title}`}
              className={cn(baseClass, positionClass, "block")}
            >
              <CardBody article={article} />
            </Link>
          );
        }

        return (
          <button
            key={article.id}
            type="button"
            onClick={() => promote(article.id)}
            aria-label={`Bring forward: ${article.title}`}
            className={cn(
              baseClass,
              positionClass,
              "block w-full text-left hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]"
            )}
          >
            <CardBody article={article} />
          </button>
        );
      })}
    </div>
  );
}
