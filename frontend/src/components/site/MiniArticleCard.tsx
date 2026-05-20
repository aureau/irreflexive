import Image from "next/image";
import Link from "next/link";
import type { Article } from "@/types";
import { BiasBadge } from "./BiasBadge";

interface MiniArticleCardProps {
  article: Article;
}

export function MiniArticleCard({ article }: MiniArticleCardProps) {
  return (
    <Link
      href={article.href}
      className="group flex flex-col gap-3 rounded-md transition-colors"
    >
      <div className="relative aspect-[4/3] w-full overflow-hidden rounded-md bg-[var(--color-paper-3)]">
        <Image
          src={article.image}
          alt=""
          fill
          sizes="(min-width: 1024px) 220px, (min-width: 640px) 33vw, 50vw"
          className="object-cover transition-transform duration-500 group-hover:scale-[1.02]"
        />
      </div>

      <div className="space-y-1.5">
        <h4 className="line-clamp-2 text-sm font-semibold leading-snug text-[var(--color-ink)] group-hover:text-[var(--color-ink-2)]">
          {article.title}.
        </h4>
        <div className="flex items-center justify-between text-xs text-[var(--color-ink-muted)]">
          <span>{article.date}</span>
          <BiasBadge value={article.bias} />
        </div>
      </div>
    </Link>
  );
}
