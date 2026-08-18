# Lumenveil

A luminous, responsive Hugo theme with glass surfaces, aurora ambience, automatic light and dark modes, search, galleries, and a reading-first experience for long-form content.

[中文说明](README.zh.md) · [English](#english) · [Screenshots](#screenshots)

## Screenshots

Live preview: <https://blog.hansendong.top>

### Light mode

| Home | Articles |
| --- | --- |
| ![Home hero with aurora background and status chips / 首页：极光背景与状态徽章](docs/screenshots/home.png) | ![Posts archive with localized section title and pagination / 文章归档页：本地化标题与分页](docs/screenshots/posts.png) |

| Article | About |
| --- | --- |
| ![Single post with PhotoSwipe gallery and code copy buttons / 文章页：PhotoSwipe 图集与代码复制](docs/screenshots/post.png) | ![About page rendered with glass surfaces and contact table / 关于页：玻璃表面与联系方式表格](docs/screenshots/about.png) |

### Dark mode

| Home | Articles |
| --- | --- |
| ![Home hero in dark mode with aurora glow / 深色首页：极光辉光](docs/screenshots/home-dark.png) | ![Posts archive in dark mode / 深色文章归档页](docs/screenshots/posts-dark.png) |

| Article | About |
| --- | --- |
| ![Single post in dark mode with PhotoSwipe gallery / 深色文章页：PhotoSwipe 图集](docs/screenshots/post-dark.png) | ![About page in dark mode with glass surfaces / 深色关于页：玻璃表面](docs/screenshots/about-dark.png)

### Mobile

| Home | Articles |
| --- | --- |
| ![Home hero on mobile, light / 移动端首页（浅色）](docs/screenshots/home-mobile.png) | ![Posts archive on mobile, light / 移动端文章列表（浅色）](docs/screenshots/posts-mobile.png) |

| Article | About |
| --- | --- |
| ![Single post on mobile, light / 移动端文章页（浅色）](docs/screenshots/post-mobile.png) | ![About on mobile, light / 移动端关于页（浅色）](docs/screenshots/about-mobile.png) |

| Home (dark) | Articles (dark) |
| --- | --- |
| ![Home hero on mobile, dark / 移动端首页（深色）](docs/screenshots/home-mobile-dark.png) | ![Posts archive on mobile, dark / 移动端文章列表（深色）](docs/screenshots/posts-mobile-dark.png) |

| Article (dark) | About (dark) |
| --- | --- |
| ![Single post on mobile, dark / 移动端文章页（深色）](docs/screenshots/post-mobile-dark.png) | ![About on mobile, dark / 移动端关于页（深色）](docs/screenshots/about-mobile-dark.png) |

## English

### Features

- Responsive home, archive, category, tag, article, gallery, and 404 layouts
- Aurora background, glassmorphism surfaces, and full-bleed cover support
- Automatic light and dark mode with a persistent manual switch
- Client-side search powered by Hugo JSON output
- Categories, tags, pagination, RSS, sitemap, and robots.txt
- Article table of contents, reading time, word count, last modified indicator, and a real-time cross-user page view count via the busuanzi partial (third-party CN service)
- Dynamic copyright range (from `since` to the current year) and CC BY-NC-SA 4.0 license badge in the footer
- Syntax highlighting and one-click code or article-link copy
- PhotoSwipe-powered image gallery shortcode with CSS grid + justified masonry layouts, sortable by name / date / weight prefix
- `douban-card` shortcode for embedding Douban movie / book / music cards — all metadata passed as parameters (no API call, since Douban's public API closed in 2022)
- Markdown image captions via standard `![alt](src "caption")` title syntax — renders a centered `<figcaption>` below the figure and is decoupled from the HTML `title` tooltip (bug fix)
- Optional Artalk comments module — config-driven partial that mirrors the article card style (glass, button--ghost, mono uppercase header) and auto-aligns to `.article-main` via the existing CSS grid, with a per-comment stagger fade-in on list load
- Optional article like button — centered heart CTA at the bottom of the article body, one-way semantics (no cancel after click) with bump animation, pink accent (#ff6b8a) when liked, count synced across devices via a self-hosted `/api/like/*` endpoint (like-server.py, JSON file backend) with `localStorage` fallback for per-user like state; cursor switches to `not-allowed` to signal the action is locked
- Optional `cover` front matter per post — page-bundle image or `static/` asset, used as the archive-page thumbnail
- Open Graph, Twitter Card, canonical URL, and JSON-LD metadata
- Reduced-motion support, keyboard focus states, and mobile navigation
- Hugo Pipes minification and asset fingerprinting

### Requirements

- Hugo Extended `0.146.0` or newer
- Git, if installing as a submodule

### Installation

From the root of your Hugo site:

```bash
git submodule add https://github.com/Hansen1018/hugo-theme-lumenveil.git themes/lumenveil
```

Enable the theme in `hugo.toml`:

```toml
theme = 'lumenveil'
```

Update the theme later with:

```bash
git submodule update --remote --merge
```

### Required configuration

Search requires a JSON output for the home page. Copy the following into your site's `hugo.toml` and adjust the values to match your project:

```toml
locale = 'zh-cn'
defaultContentLanguage = 'zh-cn'
hasCJKLanguage = true
enableRobotsTXT = true

[pagination]
  pagerSize = 8

[taxonomies]
  category = 'categories'
  tag = 'tags'

[outputs]
  home = ['HTML', 'RSS', 'JSON']
  section = ['HTML', 'RSS']
  taxonomy = ['HTML', 'RSS']
  term = ['HTML', 'RSS']

[outputFormats.JSON]
  mediaType = 'application/json'
  baseName = 'index'
  isPlainText = true
  notAlternative = true

[markup]
  [markup.highlight]
    noClasses = false
    guessSyntax = true
  [markup.tableOfContents]
    startLevel = 2
    endLevel = 4
    ordered = false

[params]
  description = 'Notes on technology, life, and long-term thinking.'
  author = 'Your Name'
  initial = 'Y'
  avatar = '/images/avatar.png'
  role = 'Writer · Developer'
  tagline = 'A short sentence about you and your writing.'
  location = 'Your City'
  status = 'Currently writing'
  email = 'you@example.com'
  github = 'https://github.com/yourname'
  twitter = 'https://twitter.com/yourname'
  since = 2024
  mainSections = ['posts']

[menus]
  [[menus.main]]
    name = 'Home'
    pageRef = '/'
    weight = 10
  [[menus.main]]
    name = 'Posts'
    pageRef = '/posts'
    weight = 20
  [[menus.main]]
    name = 'About'
    pageRef = '/about'
    weight = 25
  [[menus.main]]
    name = 'Categories'
    pageRef = '/categories'
    weight = 30
  [[menus.main]]
    name = 'Tags'
    pageRef = '/tags'
    weight = 40
```

### Content structure

```text
content/
├── _index.md
├── about.md
├── posts/
│   ├── _index.md
│   └── hello-world.md
├── categories/
│   └── _index.md
└── tags/
    └── _index.md
```

Example article front matter:

```yaml
---
title: "Hello World"
date: 2026-08-10T10:00:00+08:00
lastmod: 2026-08-15T18:30:00+08:00
draft: false
description: "A short summary displayed in article cards and metadata."
categories: ["Notes"]
tags: ["Hugo", "Writing"]
cover: "images/hello-world.jpg"   # optional; falls back to a static/ asset when no page-bundle image matches
toc: true
---
```

`lastmod` is optional. When present and later than `date`, a "Last updated …" line is rendered in the article header (the template uses a localized label, so the rendered text matches the site's language).

`cover` is optional. When set, it shows up as the post-card thumbnail on the archives page. The value is first looked up as a page-bundle resource, then falls back to a path under `static/` (e.g. `cover: images/foo.png` resolves to `/images/foo.png`).

### Image gallery shortcode

Drop one or more images into a directory, then use the shortcode by folder name:

```md
{{< gallery "gallery/2026-tokyo" >}}
```

The shortcode renders a responsive CSS grid and uses PhotoSwipe for full-screen previews. Images are pulled from the page bundle (`content/posts/.../gallery/2026-tokyo/*.jpg`); they can also be referenced explicitly with `images="a.jpg,b.jpg"`.

#### Layout: `grid` (default) vs `justified`

- `grid` — even CSS Grid columns, `cols` controls column count.
- `justified` — flexbox masonry that respects each image's aspect ratio. Each row fills the container proportionally; image height stays at the row target.

```md
{{< gallery "gallery/2026-tokyo" layout="justified" cols="3" gap="14" >}}
```

#### Sort

- `sort="name"` (default) — alphabetical by filename.
- `sort="date"` — by file modification time (`.Lastmod`).
- `sort="weight"` — by numeric prefix in the filename, e.g. `01-foo.jpg`, `02-bar.jpg` (ascending). Images without a prefix sort last.
- `sort="manual"` — keeps the order images were listed in (no sort).
- `reverse="true"` — flip the chosen order.

```md
{{< gallery "gallery/2026-tokyo" layout="justified" sort="weight" reverse="false" >}}
```

The `weight` strategy is convenient when filenames come from a camera or scanner that doesn't preserve capture order — rename to add a prefix and the gallery reorders.

#### Inline images in markdown

Single images rendered via the standard `![alt](image.jpg)` markdown also join the gallery: the render hook attaches the same `data-flex-grow` / `data-flex-basis` attributes, and a small JS helper in `main.js` groups consecutive figures into a justified masonry container automatically.

### Image captions via markdown title syntax

Use the standard markdown title syntax to add a centered caption below an image:

```md
![Latte art in a glass cup](/coffee.jpg "Morning ritual — a flat white after a 6am run.")
```

When the image's `.Title` is set, the text renders as a centered `<figcaption>` below the figure. When `.Title` is empty, no `<figcaption>` element is emitted — the figure stays clean, with no extra margin or padding from a phantom element.

- **Backward compat** — existing articles without title syntax render unchanged (no figcaption).
- **Forward compat** — works with any Hugo + Goldmark version, no special extensions required.
- **Bug fix** — the title syntax no longer adds an HTML `title=` tooltip on the `<img>`. Previously the same syntax produced both a caption and a tooltip, conflating two semantics.

> Note: Goldmark's `{attr="val"}` syntax (`![alt](src){caption="text"}`) does not populate `.Attributes` in this render-image hook on Hugo 0.146.0+, so `.Title` is the supported path.

### `douban-card` shortcode

Embed a clickable Douban-style card linking to a Douban subject page. Douban closed its public API in 2022, so all metadata is passed as parameters — no auto-fetch, no broken calls.

Supports three types via the `type` parameter:

- `type="movie"` *(default)* — links to `movie.douban.com`, fallback icon is a camera, meta labels are `导演` / `主演`
- `type="book"` — links to `book.douban.com`, fallback icon is books, meta labels are `作者` / `译者`
- `type="music"` — links to `music.douban.com`, fallback icon is music notes, meta labels are `艺术家` / `专辑`

```md
{{< douban-card type="book" id="12345678" title="Sample Title" year="2024"
                director="Sample Author" rating="8.5" cover="cover.jpg" >}}
```

Parameters:

- `id` *(required)* — Douban subject ID, used in the link URL
- `type` — `movie` (default), `book`, or `music`; switches URL subdomain, fallback icon, and meta labels
- `title` — card title (default: `"豆瓣条目"`)
- `year` — release year
- `region` — country / region
- `director` — director (movie) / author (book) / artist (music) name; the label shown next to this value depends on `type`
- `rating` — Douban rating, shown as a star
- `cast` — main cast (movie) / translator (book) / album (music), single string; the label shown next to this value depends on `type`
- `synopsis` — short summary, clamped to 2 lines
- `cover` — path to a cover image inside the page bundle; falls back to a type-specific icon (camera / books / music notes) when omitted

The card uses the theme's glass surface and hover lift, matches the article card aesthetic, and adapts to light / dark via standard CSS variables. The card layout, padding, colors, and hover effect are identical across all three types — only the fallback icon shape and the meta labels differ, keeping the visual style consistent across the `douban-card` family. Drop a demo post into `exampleSite/content/posts/` to see all three types rendered.

### Run locally

```bash
hugo server -D
```

Open `http://localhost:1313/` in your browser.

### CSS component architecture

`main.css` is intentionally deleted. The theme uses Hugo's `resources.Match` + `resources.Concat` to bundle per-component files at build time:

```go
{{ $main := resources.Match "css/components/_*.css" | resources.Concat "main.css" | minify | fingerprint }}
```

Component files live in `assets/css/components/_<name>.css`, one per BEM namespace:

| File | BEM prefix | What |
| --- | --- | --- |
| `_tokens.css` | (root vars) | `:root` custom properties, light theme override |
| `_reset.css` | (global) | `*, html, body, a, button, img, ::selection, :focus-visible, ::-webkit-scrollbar` |
| `_utilities.css` | (global) | `.sr-only, .skip-link, .glass, .glass::before, .site-shell` |
| `_aurora.css` | `.aurora, .aurora__*` | background canvas, blobs, drift animations |
| `_layout.css` | `.section, .page-hero, .breadcrumbs, .empty-state, .eyebrow` | page chrome |
| `_article.css` | `.article, .article-header, .article-cover, .prose, .copy-code` | article body |
| `_comments.css` | `.article-comments` | Artalk comments wrapper |
| `_like.css` | `.article-like, .like-btn, .like-icon, .like-count` | article like CTA |
| `_gallery.css` | `.gallery-image, .pswp__*, .pswp-gallery, .pswp-item` | PhotoSwipe overrides |
| `_search.css` | `.search-dialog, .search-field, .search-result, .search-empty, kbd` | search modal |
| `_term.css` | `.term-grid, .term-card` | taxonomy list |
| `_post.css` | `.post-card, .post-grid, .post-meta, .post-nav, .read-link, .tag-list` | post list + nav |
| `_archive.css` | `.archive-board, .archive-block, .archive-count, .archive-empty` | archive page |
| `_toc.css` | `.toc, .toc__inner` | TOC sidebar |
| `_404.css` | `.not-found, .not-found__*, .suggest-card` | 404 page |
| `_back-to-top.css` | `.back-to-top` | back-to-top button |
| `_douban-card.css` | `.douban-card, .douban-card__*` | douban shortcode |
| `_header.css` | `.site-header, .brand, .main-nav, .icon-button, .menu-toggle, .header-actions` | top nav |
| `_footer.css` | `.site-footer, .footer-inner, .footer-bottom, .footer-links` | footer |
| `_home.css` | `.hero, .hero__*, .chip, .button, .fade-up, .explore-panel, .about-panel` | home/hero page |

The **underscore prefix** on every filename is the key trick: in ASCII sort, `_` (0x5F) comes **before** lowercase letters (0x61+), so `resources.Match "css/components/_*.css"` returns files in an order that matches the intended CSS cascade:

- `_tokens` and `_reset` come first (CSS variables must be defined before use)
- `_aurora` / `_utilities` next (page chrome)
- BEM components in cascade order

At build time, `resources.Concat` bundles them all into a single `main.min.<hash>.css` (no `@import` waterfall, single HTTP request, single cache key).

**To add a new component**:

1. Create `assets/css/components/_<name>.css` with BEM-namespaced styles
2. Filename must start with `_` to sort correctly in the cascade
3. The component is auto-picked-up by `resources.Match "css/components/_*.css"` — no `head.html` edit needed

### Customization

- Edit site identity, social links, and license year under `[params]`.
- Replace `static/favicon.svg` and `static/og.svg` with your own brand assets.
- Override any theme file by creating the same path in your site's `layouts`, `assets`, or `static` directory.
- The theme follows the system color preference by default. A visitor's manual selection is stored locally in the browser.

For the Chinese translation, see [README.zh.md](README.zh.md).

## License

Lumenveil is released under the [GNU General Public License v3.0](LICENSE). The default site footer links to the [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh-hans) license for the site's written content; you can replace it with the license that suits your work.
