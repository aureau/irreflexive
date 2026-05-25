# structure

news-outlet feel, inspired by `theequidistantproject/frontend`. white paper bg, centered serif masthead, hashtag pills row above an interactive card deck, related row of compact cards below, then explore + mission.

```
frontend/
├── package.json, tsconfig.json, next.config.ts, postcss.config.mjs, eslint.config.mjs, .gitignore
├── STRUCTURE.md              # this file
├── public/
│   └── images/               # placeholder svg article art (until real assets land)
└── src/
    ├── app/
    │   ├── layout.tsx        # fonts (Inter + Instrument Serif), metadata
    │   ├── page.tsx          # composes all sections, mounts hidden hero <video>
    │   ├── globals.css       # tailwind v4 + newsprint tokens (paper / ink / accent)
    │   └── health/route.ts   # GET /health → { status: "ok" } (static)
    ├── components/
    │   ├── icons.tsx         # inline svg icons (no lucide dep yet)
    │   └── site/
    │       ├── Navbar.tsx            # sticky masthead — menu · "Irreflexive" · search
    │       ├── TrendingSection.tsx   # client comp — pills row · card deck · related row
    │       ├── CardDeck.tsx          # client comp — 1 front + up to 2 peek cards, clickable to promote
    │       ├── FeaturedArticle.tsx   # standalone big card (used by ExploreLatest)
    │       ├── MiniArticleCard.tsx   # compact card — image top, 2-line headline, date · bias
    │       ├── RelatedRow.tsx        # eyebrow + horizontal grid of MiniArticleCards
    │       ├── BiasBadge.tsx         # ↑/↓ + % with bull/bear color
    │       ├── ExploreLatest.tsx     # client comp — Today/Yesterday/Week/Month + grid
    │       ├── MissionBand.tsx       # short editorial "our mission" block + stats
    │       └── Footer.tsx            # 4-col footer + legal row
    ├── lib/
    │   ├── utils.ts          # cn() helper
    │   └── mock-articles.ts  # ARTICLES[] (5 per tag), HASHTAGS[], articlesByTag()
    └── types/
        └── index.ts          # Article, HashTag, BiasLean, TimelineBucket, NavItem, FooterSection
```

## layout (top → bottom)

1. **Navbar** — sticky, white w/ blur. menu icon left · serif "Irreflexive" centered · search right. (icon buttons are visual placeholders for now)
2. **hidden hero `<video id="hero-demo-video">`** — kept mounted (`className="hidden"`) so the dom slot is reserved for a future demo clip. `<source>` commented out.
3. **TrendingSection** (band w/ subtle gray bg) — centered hero stack inside `max-w-5xl`:
   - `#politics #conflict #environment #finance #sports` pill row, centered, with blue active dot
   - "Trending" eyebrow + `CardDeck` (front card + 2 stacked peeks offset / scaled / faded behind)
     - clicking a peek calls `promote(id)` and slides it to the front
     - the front card is a `<Link>` to the article; peeks are `<button>`s
     - a hidden sentinel card anchors container height so the layout doesn't jump
   - "Seeing news on #tag" + ⭐ Follow pill
   - `RelatedRow` — horizontal grid of `MiniArticleCard` (2 / 3 / 4 cols at sm / md+)
4. **ExploreLatest** — Today/Yesterday/This Week/This Month timeline rail + 2x2 article grid + load more.
5. **MissionBand** — short editorial pitch (mission statement + 3 stats).
6. **Footer** — masthead repeat, 4 link columns (read / project / build / legal), legal row.

## card deck mechanics

`CardDeck.tsx` is the only stateful piece worth calling out:

- props: `articles: Article[]` (the pool for the active tag).
- internal state: `order: string[]` — ordered list of article ids; `order[0]` is the front card.
- on tag change (parent passes a new `articles` array), a `useEffect` resets `order` to match.
- `promote(id)` lifts the clicked peek to the front: `setOrder(prev => [id, ...prev.filter(x => x !== id)])`.
- visuals: slot 0 has no offset, slot 1 is `translate-x-2.5 translate-y-3.5 scale-[0.97] opacity-70`, slot 2 is `translate-x-5 translate-y-7 scale-[0.94] opacity-50`. All slots transition over 500ms with a custom easing.
- a final invisible "sentinel" card sits inside the container so its measured height matches a real card — keeps the deck from collapsing or shifting between tag swaps.

## design tokens

defined in `globals.css` as `@theme { ... }`:

- **paper**: `#ffffff` / `#f6f7fb` / `#eef1f7`
- **ink**: `#0f1115` / `#1f2430` / muted `#5b6473` / dim `#8a93a3`
- **rule**: `#e5e7ec` / strong `#c9cdd6`
- **accent**: `#2f6fed` (blue dot + underline gradient)
- **bull/bear**: green `#16a34a` / red `#dc2626` (used by `BiasBadge`)
- **mark**: `#f5b400` (follow star + active timeline underline)
- **fonts**: Instrument Serif (display) + Inter (body)

## state & data flow

- everything is local. no api calls, no fetch, no client state beyond per-section `useState` (active tag, deck order, timeline bucket).
- mock data lives in `src/lib/mock-articles.ts` and is typed by `src/types/index.ts`.
- when the api is ready: replace `articlesByTag()` with a server call (or pass `articles` in as props from a server component), keep `CardDeck` / `BiasBadge` / `MiniArticleCard` / `FeaturedArticle` untouched.

## adding a new section

1. add a component in `src/components/site/NewSection.tsx`
2. import + drop into `src/app/page.tsx` between the existing bands
3. if it needs new data shapes, add types in `src/types/index.ts` first, then mock data in `src/lib/`
