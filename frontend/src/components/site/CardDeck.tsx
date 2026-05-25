"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import type { Article } from "@/types";
import { BiasBadge } from "./BiasBadge";
import { cn } from "@/lib/utils";

interface CardDeckProps {
  articles: Article[];
  autoCycleMs?: number;
}

function safeImageSrc(src: string, seed: string): string {
  const trimmed = src?.trim() ?? "";
  if (!trimmed || trimmed === "undefined") {
    let hash = 0;
    for (let i = 0; i < seed.length; i += 1) {
      hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
    }
    return `/images/article-placeholder-${(hash % 4) + 1}.svg`;
  }
  if (
    trimmed.startsWith("/") ||
    trimmed.startsWith("http://") ||
    trimmed.startsWith("https://")
  ) {
    return trimmed;
  }
  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) {
    hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
  }
  return `/images/article-placeholder-${(hash % 4) + 1}.svg`;
}

function CardBody({
  article,
  priority,
  showMeta,
}: {
  article: Article;
  priority?: boolean;
  showMeta: boolean;
}) {
  return (
    <>
      <div className="relative aspect-[16/10] w-full overflow-hidden bg-[var(--color-paper-3)]">
        <Image
          src={safeImageSrc(article.image, article.id)}
          alt=""
          fill
          sizes="(min-width: 1024px) 640px, 100vw"
          className="object-cover"
          priority={priority}
        />
      </div>
      {showMeta && (
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
      )}
    </>
  );
}

const SLOT_STYLE: Array<{ transform: string; opacity: number; zIndex: number }> = [
  { transform: "translate3d(0,0,0) scale(1)", opacity: 1, zIndex: 30 },
  { transform: "translate3d(10px,14px,0) scale(0.97)", opacity: 0.7, zIndex: 20 },
  { transform: "translate3d(20px,28px,0) scale(0.94)", opacity: 0.5, zIndex: 10 },
];

const FADE_OUT_MS = 100;
const SLIDE_MS = 1220;
const FADE_IN_MS = 1000;

export function CardDeck({ articles, autoCycleMs }: CardDeckProps) {
  const [order, setOrder] = useState<string[]>(() => articles.map((a) => a.id));
  const [exitingId, setExitingId] = useState<string | null>(null);
  const [snappingId, setSnappingId] = useState<string | null>(null);
  const [paused, setPaused] = useState(false);
  const animatingRef = useRef(false);
  const exitNodeRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    setOrder(articles.map((a) => a.id));
    setExitingId(null);
    setSnappingId(null);
    animatingRef.current = false;
  }, [articles]);

  // Finish the cycle when the front card's opacity transition actually ends,
  // not after a `setTimeout` that drifts off frame boundaries.
  useEffect(() => {
    if (!exitingId) return;
    const node = exitNodeRef.current;
    if (!node) return;

    let done = false;

    const finish = () => {
      if (done) return;
      done = true;
      node.removeEventListener("transitionend", onTransitionEnd);
      node.removeEventListener("transitioncancel", onTransitionEnd);

      const exited = exitingId;
      setSnappingId(exited);
      setExitingId(null);
      setOrder((cur) => {
        if (cur.length < 2 || cur[0] !== exited) return cur;
        return [...cur.slice(1), cur[0]];
      });
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          setSnappingId(null);
          animatingRef.current = false;
        });
      });
    };

    const onTransitionEnd = (event: TransitionEvent) => {
      if (event.target !== node) return;
      if (event.propertyName !== "opacity") return;
      finish();
    };

    node.addEventListener("transitionend", onTransitionEnd);
    node.addEventListener("transitioncancel", onTransitionEnd);

    // Safety net in case the transitionend never fires (tab background,
    // reduced motion preference suppressing the event, etc.).
    const fallback = window.setTimeout(finish, FADE_OUT_MS + 120);

    return () => {
      window.clearTimeout(fallback);
      node.removeEventListener("transitionend", onTransitionEnd);
      node.removeEventListener("transitioncancel", onTransitionEnd);
    };
  }, [exitingId]);

  const cycle = useCallback(() => {
    if (animatingRef.current) return;
    setOrder((prev) => {
      if (prev.length < 2) return prev;
      const front = prev[0];
      animatingRef.current = true;
      // Use rAF so the new style is committed on a fresh frame boundary;
      // setting it synchronously in the same tick can collide with React's
      // commit and skip the transition's first frame.
      requestAnimationFrame(() => setExitingId(front));
      return prev;
    });
  }, []);

  const promote = useCallback((id: string) => {
    if (animatingRef.current) return;
    setOrder((prev) => {
      if (prev[0] === id) return prev;
      return [id, ...prev.filter((x) => x !== id)];
    });
  }, []);

  useEffect(() => {
    if (!autoCycleMs || autoCycleMs <= 0) return;
    if (paused) return;
    if (articles.length < 2) return;
    const handle = window.setInterval(cycle, autoCycleMs);
    return () => window.clearInterval(handle);
  }, [autoCycleMs, paused, articles.length, cycle]);

  const slots = order
    .slice(0, 3)
    .map((id) => articles.find((a) => a.id === id))
    .filter((a): a is Article => Boolean(a));

  if (slots.length === 0) return null;

  const front = slots[0];

  return (
    <div
      className="relative mx-auto w-full max-w-2xl"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      {/* invisible sentinel anchors the container height */}
      <div aria-hidden className="invisible">
        <div className="card overflow-hidden">
          <CardBody article={front} showMeta />
        </div>
      </div>

      {slots.map((article, i) => {
        const isExiting = article.id === exitingId;
        const isSnapping = article.id === snappingId;
        const isFront = i === 0 && !isExiting;
        const slot = SLOT_STYLE[i] ?? SLOT_STYLE[2];

        const opacityDuration = isExiting
          ? FADE_OUT_MS
          : isSnapping
            ? 0
            : FADE_IN_MS;

        const style: React.CSSProperties = {
          transform: slot.transform,
          opacity: isExiting || isSnapping ? 0 : slot.opacity,
          zIndex: isExiting ? 40 : slot.zIndex,
          transitionProperty: isSnapping ? "transform" : "opacity, transform",
          transitionDuration: isSnapping
            ? "0ms"
            : `${opacityDuration}ms, ${SLIDE_MS}ms`,
          transitionTimingFunction:
            "cubic-bezier(0.4, 0, 0.2, 1), cubic-bezier(0.22, 1, 0.36, 1)",
          willChange: "transform, opacity",
          backfaceVisibility: "hidden",
          transformOrigin: "center",
          isolation: "isolate",
          contain: "layout paint",
          pointerEvents: isExiting ? "none" : undefined,
        };

        const assignRef = (node: HTMLAnchorElement | null) => {
          if (isExiting) exitNodeRef.current = node;
        };

        const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
          if (isFront) return; // let the Link navigate
          e.preventDefault();
          promote(article.id);
        };

        return (
          <Link
            key={article.id}
            ref={assignRef}
            href={article.href}
            onClick={handleClick}
            aria-label={isFront ? `Read: ${article.title}` : `Bring forward: ${article.title}`}
            aria-hidden={isExiting}
            tabIndex={isExiting ? -1 : 0}
            style={style}
            className={cn(
              "absolute inset-0 card overflow-hidden block",
              !isFront &&
                "hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]",
            )}
          >
            <CardBody article={article} priority showMeta={i === 0} />
          </Link>
        );
      })}
    </div>
  );
}
