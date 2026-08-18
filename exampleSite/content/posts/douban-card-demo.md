---
title: "Douban Card Shortcode"
date: 2026-08-18T16:28:00+08:00
draft: false
description: "How to embed a Douban movie/book/music review card in any post."
categories: ["Shortcodes"]
tags: ["Douban", "Card", "Demo"]
---

The `douban-card` shortcode renders a clickable card linking to a Douban subject page — useful for film, book, or music reviews. Supports three `type` values (`movie` / `book` / `music`); each switches the URL subdomain, the fallback icon, and the meta labels while keeping the card layout, padding, hover lift, and accent color identical across types.

## Parameters

Douban's public API was closed in 2022, so all metadata is passed as parameters (no auto-fetch).

- **id** *(required)* — Douban subject ID, used in the link URL
- **type** — `movie` (default), `book`, or `music`. Switches the URL subdomain (`movie.douban.com` / `book.douban.com` / `music.douban.com`), the fallback icon (camera / books / music notes), and the meta labels (`导演` / `主演` vs `作者` / `译者` vs `艺术家` / `专辑`).
- **title** — card title (default: `"豆瓣条目"`)
- **year** — release year
- **region** — country / region
- **director** — director (movie) / author (book) / artist (music) name. The label shown next to this value depends on `type`.
- **rating** — Douban rating (shown as a star)
- **cast** — main cast (movie) / translator (book) / album (music), single string. The label shown next to this value depends on `type`.
- **synopsis** — short summary, clamped to 2 lines
- **cover** — path to a cover image inside the page bundle; falls back to a type-specific icon (camera / books / music notes) when omitted

## Examples

### Movie — type defaults to "movie" if omitted

{{< douban-card id="36154853" title="好东西" >}}

### Book — type="book", labels switch to 作者 / 译者

{{< douban-card type="book" id="1082150" title="活着" year="1993" director="余华" rating="9.4" synopsis="一个普通中国人在动荡年代的一生。" >}}

### Music — type="music", labels switch to 艺术家 / 专辑

{{< douban-card type="music" id="1393778" title="杀死那个石家庄人" year="2010" director="万能青年旅店" rating="9.4" >}}

### With metadata, no cover (icon fallback)

{{< douban-card id="36154853" title="好东西" year="2024" region="中国大陆" director="邵艺辉" rating="8.9" cast="宋佳、钟楚曦、赵又廷" synopsis="失婚的中年女人王铁梅独立抚养女儿，与邻居女孩小叶成为挚友，两人以及身边一群都市女性在日常中相互扶持。" >}}

### Full — with cover from page bundle

If a `cover.jpg` lives next to this `index.md`, reference it by filename:

```go-html-template
{{< douban-card id="36154853" title="好东西" year="2024"
                 director="邵艺辉" rating="8.9"
                 cover="cover.jpg" >}}
```

## Style notes

- Card uses theme tokens (`--glass-bg`, `--line`, `--ink-2`, `--font-sans`) so light and dark mode adapt automatically.
- All three types share the same card layout, padding, border-radius, glass effect, and hover lift. Only the fallback icon shape and the meta label text differ between types — the visual style stays consistent across the whole `douban-card` family.
- The green accent (`#2e8b57`) is identical for all three types. Type-specific colors were intentionally avoided to keep the family visually unified.
- The card itself is a single `<a>` tag — accessible by keyboard, no JS required.
- The `synopsis` field is clamped to 2 lines via `-webkit-line-clamp`; longer summaries get an ellipsis.
- The "豆瓣" badge sits in the top-right corner (absolute positioned); the `→` arrow on the right edge is the visual affordance for "click to follow".
