---
title: "Hello, Lumenveil"
date: 2026-08-10T10:00:00+08:00
lastmod: 2026-08-12T18:30:00+08:00
draft: false
description: "A short walkthrough of the Lumenveil theme's main building blocks."
categories: ["Notes"]
tags: ["Hugo", "Lumenveil", "Demo"]
toc: true
cover: "images/cover.jpg"
---

This is the canonical example post for the Lumenveil theme. It exercises every front-matter field the theme cares about — date, lastmod, categories, tags, table of contents, and an optional `cover` thumbnail.

## Sections look like this

`## H2` and `### H3` get picked up by the side-bar table of contents on wide screens.

## Code blocks

```ts
function greet(name: string): string {
  return `Hello, ${name}!`;
}
```

Use the copy button in the top-right of the block to grab it.

## Inline bits

Links open in a new tab when they point off-site. **Bold**, *italic*, and `inline code` all render with the theme's typography stack.

## Images

Drop images into a directory and use the gallery shortcode:

```md
{{< gallery "gallery/sample" >}}
```

A single image also works as a regular Markdown image.