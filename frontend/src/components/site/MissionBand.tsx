export function MissionBand() {
  return (
    <section
      id="mission"
      className="border-t border-[var(--color-rule)] bg-[var(--color-paper)] py-16 sm:py-24"
      aria-label="Our mission"
    >
      <div className="mx-auto max-w-4xl px-6 text-center">
        <p className="eyebrow">Our Mission</p>
        <h2 className="mt-3 font-display text-3xl leading-tight sm:text-5xl">
          read the news, then read the lean.
        </h2>
        <p className="mx-auto mt-5 max-w-2xl text-base text-[var(--color-ink-muted)] sm:text-lg">
          Irreflexive scores political bias in news articles using calibrated
          embeddings against a balanced corpus. The goal isn&apos;t to tell you
          what to think — it&apos;s to surface where a story leans so you can
          decide for yourself.
        </p>

        <dl className="mx-auto mt-10 grid max-w-3xl grid-cols-3 gap-6 text-left">
          {[
            { k: "topics", v: "10" },
            { k: "baseline articles", v: "60+" },
            { k: "classes", v: "2 + center" },
          ].map((stat) => (
            <div
              key={stat.k}
              className="border-l-2 border-[var(--color-rule-strong)] pl-4"
            >
              <dt className="text-xs uppercase tracking-widest text-[var(--color-ink-dim)]">
                {stat.k}
              </dt>
              <dd className="mt-1 font-display text-3xl">{stat.v}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
