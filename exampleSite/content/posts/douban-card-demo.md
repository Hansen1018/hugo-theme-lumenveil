---
title: "Douban Card Shortcode"
date: 2026-08-18T16:28:00+08:00
draft: false
description: "How to embed a Douban movie/book review card in any post."
categories: ["Shortcodes"]
tags: ["Douban", "Card", "Demo"]
---

The `douban-card` shortcode renders a clickable card linking to a Douban subject page — useful for film or book reviews.

## Parameters

Douban's public API was closed in 2022, so all metadata is passed as parameters (no auto-fetch).

- **id** *(required)* — Douban subject ID, used in the link URL
- **title** — card title (default: `"豆瓣条目"`)
- **year** — release year
- **region** — country / region
- **director** — director name
- **rating** — Douban rating (shown as a star)
- **cast** — main cast (single string)
- **synopsis** — short summary, clamped to 2 lines
- **cover** — path to a cover image inside the page bundle; falls back to a green video-camera icon when omitted

## Examples

### Minimal — ID only

{{< douban-card id="36154853" title="好东西" >}}

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
- The card itself is a single `<a>` tag — accessible by keyboard, no JS required.
- The `synopsis` field is clamped to 2 lines via `-webkit-line-clamp`; longer summaries get an ellipsis.
- The "豆瓣" badge sits in the top-right corner (absolute positioned); the `→` arrow on the right edge is the visual affordance for "click to follow".
