import Image from "next/image";
import Link from "next/link";
import type { Article } from "@/types";
import { BiasBadge } from "./BiasBadge";

interface FeaturedArticleProps {
  article: Article;
}

export function FeaturedArticle({ article }: FeaturedArticleProps) {
  return (
    <article className="card overflow-hidden">
      <Link href={article.href} className="block">
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
          <h3 className="lede font-medium">
            {article.title}.
          </h3>

          <div className="flex items-center justify-between gap-3 text-sm">
            <div className="flex items-center gap-2 text-[var(--color-ink-muted)]">
              <span className="inline-flex size-6 items-center justify-center rounded-full bg-[var(--color-paper-3)] text-[10px] font-semibold uppercase text-[var(--color-ink-muted)]">
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
      </Link>
    </article>
  );
}
