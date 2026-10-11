---
title: "Douban Card Shortcode"
date: 2026-08-18T16:28:00+08:00
draft: false
description: "How to embed a Douban movie/book review card in any post."
categories: ["Shortcodes"]
tags: ["Douban", "Card", "Demo"]
---

The `douban-card` shortcode renders a clickable card linking to a Douban subject page — useful for film or book reviews.

The cover image is resolved automatically from
[NeoDB](https://neodb.social/), which mirrors Douban's catalogue. Pass `id`
only and the artwork appears. Every other field is still yours to pass.

## Parameters

Douban's public API was closed in 2022, so all **metadata** is passed as parameters. The **cover** is the one exception — see below.

- **id** *(required)* — Douban subject ID. Used for the link URL, and to look up the cover on NeoDB.
- **title** — card title (default: `"豆瓣条目"`)
- **year** — release year
- **region** — country / region
- **director** — director name
- **rating** — Douban rating (shown as a star)
- **cast** — main cast (single string). Separators are normalised to `、`, so
  `A / B / C`, `A, B, C` and `A、B、C` all render identically. A future call
  site is therefore consistent whichever separator its author typed.
- **synopsis** — short summary, clamped to 3 lines
- **cover** — path to a local cover image. **Overrides the NeoDB lookup** and skips the network entirely.
- **alt** — alt text for the cover (default: `"<title> 封面"`)

## How the cover is resolved

Three steps, first hit wins:

1. **`cover=` given** → that image, no network access at all.
2. **NeoDB** → `https://neodb.social/api/catalog/fetch?url=<douban subject url>`,
   then the artwork is downloaded, resized to 184px wide and written into your
   own output. Readers never contact NeoDB, and repeat builds hit Hugo's cache.
3. **Type icon** → the previous green video-camera/book/music icon, when
   NeoDB has no entry for that subject or the network is unavailable.

A failed lookup degrades to step 3; it never fails the build. If you need
builds to work with no network at all, pass `cover=` — that skips the lookup
entirely.

## Examples

### Minimal — ID and title only

Cover is fetched from NeoDB at build time.

{{< douban-card id="36154853" title="好东西" >}}

### With full metadata

{{< douban-card id="36154853" title="好东西" year="2024" region="中国大陆" director="邵艺辉" rating="8.9" cast="宋佳、钟楚曦、赵又廷" synopsis="失婚的中年女人王铁梅独立抚养女儿，与邻居女孩小叶成为挚友，两人以及身边一群都市女性在日常中相互扶持。" >}}

### Opting out of the network

A build with no route to NeoDB — air-gapped, or CI where a third-party
dependency would make the build non-hermetic — can skip the lookup
entirely without touching a single call site:

```toml
[params.douban]
  offline = true
```

The `[params]` prefix is required. A bare `[douban]` table is valid Hugo
config but lands in `site.Config`, not `site.Params`, so the switch silently
does nothing — the build still reaches for NeoDB and still prints the credit.

or per-build:

```bash
HUGO_DOUBANCARD_OFFLINE=1 hugo
```

Cards then fall back to the type icon, exactly as they do when NeoDB is
simply unreachable.
Note that the lookup is ON by default: a site that uses this shortcode makes
two HTTP requests per card at build time. A build with no route out attempts
them, times out on each, and renders the type icon instead — slower, but not
a failure. Set the flag above if you need a build that never touches the
network.

### Fully offline — cover from the page bundle

If a `cover.jpg` lives next to this `index.md`, reference it by filename. No
network call is made:

```go-html-template
{{</* douban-card id="36154853" title="好东西" year="2024"
                 director="邵艺辉" rating="8.9"
                 cover="cover.jpg" */>}}
```

## Style notes

- Card uses theme tokens (`--glass-bg`, `--line`, `--ink-2`, `--font-sans`) so light and dark mode adapt automatically.
- The card itself is a single `<a>` tag — accessible by keyboard, no JS required.
- The `synopsis` field is clamped to 3 lines via `-webkit-line-clamp`; longer summaries get an ellipsis.
- The medium label (`Movie` / `Book` / `Music`) sits at the top-right of the body, opposite the title. It replaces the old "豆瓣" badge: that printed the same word on every card while the one thing that actually differs — what kind of thing this is — went unlabelled.
- The rating renders in the credits block, below 导演 / 主演, as one more labelled fact about the work rather than a sticker over the artwork.
- The NeoDB attribution ("Cover from NeoDB") sits directly under the artwork, inside the card's anchor, so it is reachable by keyboard and announced as part of the link.
- The right-edge chevron is the "click to follow" affordance, and is hidden below 480px where the artwork already carries the cue.
- `prefers-reduced-motion` disables the hover lift and slide.
