import type { Article } from "@/types";
import { MiniArticleCard } from "./MiniArticleCard";

interface RelatedRowProps {
  articles: Article[];
}

export function RelatedRow({ articles }: RelatedRowProps) {
  if (articles.length === 0) return null;

  return (
    <section aria-label="Related stories" className="w-full">
      <div className="mb-4 flex items-end justify-between gap-3">
        <p className="eyebrow">Related</p>
        <div className="hidden h-px flex-1 self-center bg-[var(--color-rule)] sm:block" />
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-6 sm:grid-cols-3 md:grid-cols-4">
        {articles.map((a) => (
          <MiniArticleCard key={a.id} article={a} />
        ))}
      </div>
    </section>
  );
}
