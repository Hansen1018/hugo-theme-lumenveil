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
- **Categories alongside tags in the article header** — Category and tag pills render side by side; categories resolve their display label from the term page's `.Title` (e.g. `建站` for slug `webdev`), enabling "English URL slug + Chinese display" without per-category theme edits. Falls back to a `webdev → 建站` mapping, then to the raw slug. Mobile stacks categories on row 1 and tags on row 2 via `@media (max-width: 760px)`.
- **Friends page styling out of the box** — Drop a `content/friends/` page bundle with the expected data shape and the theme renders a fully styled page (info card with eyebrow pill + gradient accent bar + `dl` info table + 5/4/3/2 col responsive friend-card grid + violet→cyan gradient hover + cyan avatar glow ring + dashed empty state). Zero config; style lives in `assets/css/components/friends.css`.
- Aurora background, glassmorphism surfaces, and full-bleed cover support
- Automatic light and dark mode with a persistent manual switch
- Client-side search powered by Hugo JSON output
- Categories, tags, pagination, RSS, sitemap, and robots.txt
- Article table of contents, reading time, word count, last modified indicator, and a real-time cross-user page view count via the busuanzi partial (third-party CN service)
- Dynamic copyright range (from `since` to the current year) and CC BY-NC-SA 4.0 license badge in the footer
- Syntax highlighting and one-click code or article-link copy
- **Opt-in client-side syntax highlighting via `[params] highlight = 'hljs'`** — When set, the theme loads highlight.js with monokai and a transparent `.hljs { background: transparent !important }` rule so the container blends with the article surface. The `_default/_markup/render-codeblock.html` hook emits raw `<pre><code>` (no chroma spans) so hljs highlights cleanly without double-markup. Sites not setting the param see zero change — no chroma bytes shipped unless you opt in.
- PhotoSwipe-powered image gallery shortcode with CSS grid + justified masonry layouts, sortable by name / date / weight prefix
- Optional Artalk comments module — config-driven partial that mirrors the article card style (glass, button--ghost, mono uppercase header) and auto-aligns to `.article-main` via the existing CSS grid, with a per-comment stagger fade-in on list load
- Optional article like button — centered heart CTA at the bottom of the article body, one-way semantics (no cancel after click) with bump animation, pink accent (#ff6b8a) when liked, count synced across devices via a self-hosted `/api/like/*` endpoint (like-server.py, JSON file backend) with `localStorage` fallback for per-user like state; cursor switches to `not-allowed` to signal the action is locked
- Optional `cover` front matter per post — page-bundle image (resolved via `Resources.GetMatch`) or `static/` asset, used as the archive-page thumbnail **and as the `og:image` / `twitter:image` meta tag for social sharing** (falls back to `/og.svg` when unset — covers with leading `/` or page-bundle resources resolve to their real permalink)
- Optional `cover_caption` front matter — When set, renders below the cover image inside a dark-glass pill wrapper (`rgba(15,23,42,.72)` + `border: 1px solid rgba(255,255,255,.08)` + `border-radius: 999px` + `backdrop-filter: blur(8px)` + off-white text) readable on any cover background, including white. Empty (default) → no `<figcaption>` rendered.
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

  # Opt-in client-side syntax highlighting (highlight.js + monokai).
  # Omit this line (or leave it as the default empty) to use Hugo's built-in Chroma instead.
  highlight = 'hljs'   # set to 'hljs' to enable; remove or set to '' to use the default chroma

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
cover_caption: ""   # optional; renders inside a dark-glass pill below the cover, readable on any background
toc: true
---
```

`lastmod` is optional. When present and later than `date`, a "Last updated …" line is rendered in the article header (the template uses a localized label, so the rendered text matches the site's language).

`cover` is optional. When set, it shows up as the post-card thumbnail on the archives page and as the `og:image` / `twitter:image` meta tag for social sharing (used by Twitter, Facebook, Discord, Slack previews). The value is first looked up as a page-bundle resource via `Resources.GetMatch`, then falls back to a path under `static/` (e.g. `cover: images/foo.png` resolves to `/images/foo.png`); paths without a leading `/` are auto-prefixed. Falls back to `/og.svg` when `cover` is unset.

`cover_caption` is optional. When set, it renders inside a dark-glass pill below the cover image (the existing `.article-cover figcaption { text-align: center }` rule centers the pill). Leave empty to skip the `<figcaption>` entirely.

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

### Run locally

```bash
hugo server -D
```

Open `http://localhost:1313/` in your browser.
### CSS component architecture

`layouts/_partials/head.html` bundles the per-component CSS files into a single minified, fingerprinted `main.css` at build time using an **explicit slice + `resources.Concat`**, in cascade order:

```go
{{ $components := slice
    (resources.Get "css/components/tokens.css")
    (resources.Get "css/components/reset.css")
    (resources.Get "css/components/utilities.css")
    (resources.Get "css/components/aurora.css")
    (resources.Get "css/components/header.css")
    (resources.Get "css/components/home.css")
    (resources.Get "css/components/page-hero.css")
    (resources.Get "css/components/pagination.css")
    (resources.Get "css/components/gallery-prose.css")
    (resources.Get "css/components/photoswipe.css")
    (resources.Get "css/components/term.css")
    (resources.Get "css/components/article.css")
    (resources.Get "css/components/like.css")
    (resources.Get "css/components/archive.css")
    (resources.Get "css/components/toc.css")
    (resources.Get "css/components/404.css")
    (resources.Get "css/components/search.css")
    (resources.Get "css/components/footer.css")
    (resources.Get "css/components/back-to-top.css")
    (resources.Get "css/components/responsive.css")
    (resources.Get "css/components/motion.css")
    (resources.Get "css/components/theme-light.css")
    (resources.Get "css/components/gallery.css")
}}
{{ $main := $components | resources.Concat "css/main.css" | minify | fingerprint }}
```

The same cascade order is documented as a numbered comment block at the top of `head.html`, so the two stay in sync.

`assets/css/main.css` (685 lines, the pre-split monolithic source) is kept as a **canonical reference** of the previous bundle. It is not what the site serves — the build pipeline ignores it and produces `main.css` from the slice above.

**Why not `resources.Match`?** An earlier attempt used `resources.Match "css/components/_*.css" | resources.Concat`, relying on ASCII sort (with an underscore prefix) to keep cascade order. That was wrong: `resources.Match` returns files in **alphabetical** order, which doesn't match the CSS cascade. The result was a real bug — `_tokens.css` ended up *after* component files, so CSS variables were redefined downstream instead of being available upstream, and the desktop layout visibly broke (≈980px-wide pages centered instead of filling the viewport). The fix is to list the files in cascade order in an explicit slice and let `resources.Concat` emit them in that order. Adding a component is therefore a deliberate two-step edit (file + slice + comment), not a free `Match` pickup.

The 24 components, in cascade order:

| # | File | BEM prefix | What |
| --- | --- | --- | --- |
| 1 | `tokens.css` | (root vars) | `:root` custom properties |
| 2 | `reset.css` | (global) | `*, html, body, a, button, img, ::selection, :focus-visible, ::-webkit-scrollbar` |
| 3 | `utilities.css` | (global) | `.sr-only, .skip-link, .glass, .glass::before, .site-shell` |
| 4 | `aurora.css` | `.aurora, .aurora__*` | background canvas, blobs, drift animations |
| 5 | `header.css` | `.site-header, .brand, .main-nav, .icon-button, .menu-toggle, .header-actions` | top nav |
| 6 | `home.css` | `.hero, .hero__*, .chip, .button, .fade-up, .explore-panel, .about-panel` | home/hero |
| 7 | `page-hero.css` | `.page-hero, .page-hero__stats, .breadcrumbs, .empty-state, .eyebrow` | section chrome |
| 8 | `pagination.css` | `.pagination, .pagination-item, .pagination-pages` | pagination |
| 9 | `gallery-prose.css` | `.pswp-figure, .pswp-inline, figcaption` | inline-image reset inside `.prose` |
| 10 | `photoswipe.css` | `.pswp__bg, .pswp__container, .pswp__item, .pswp__img` | PhotoSwipe overrides |
| 11 | `term.css` | `.term-grid, .term-card` | taxonomy list |
| 12 | `article.css` | `.article, .article-header, .article-cover, .prose, .copy-code` | article body |
| 13 | `like.css` | `.article-like, .like-btn, .like-icon, .like-count` | article like CTA |
| 14 | `archive.css` | `.archive-board, .archive-block, .archive-count, .archive-empty` | archive page |
| 15 | `toc.css` | `.toc, .toc__inner` | TOC sidebar |
| 16 | `404.css` | `.not-found, .not-found__*, .suggest-card` | 404 page |
| 17 | `search.css` | `.search-dialog, .search-field, .search-result, .search-empty, kbd` | search modal |
| 18 | `footer.css` | `.site-footer, .footer-inner, .footer-bottom, .footer-links` | footer |
| 19 | `back-to-top.css` | `.back-to-top` | back-to-top button |
| 20 | `responsive.css` | (media queries) | breakpoint overrides |
| 21 | `motion.css` | (media queries) | `prefers-reduced-motion` overrides |
| 22 | `theme-light.css` | `html[data-theme="light"] *` | light-theme overrides |
| 23 | `gallery.css` | `.gallery, .gallery__*, .pswp-gallery, .pswp-item` | gallery shortcode |
| 24 | `douban-card.css` | `.douban-card, .douban-card__*` | douban-card shortcode |

**To add a new component**:

1. Create `assets/css/components/<name>.css` with BEM-namespaced styles. Pick the correct cascade position (variables → reset → utilities → chrome → page-specific → overrides).
2. Append it to the slice in `head.html` and update the numbered comment block. The build will fail loudly if a `resources.Get` path doesn't resolve.
3. Re-build: `hugo server -D`.

### Customization

- Edit site identity, social links, and license year under `[params]`.
- Replace `static/favicon.svg` and `static/og.svg` with your own brand assets.
- Override any theme file by creating the same path in your site's `layouts`, `assets`, or `static` directory.
- The theme follows the system color preference by default. A visitor's manual selection is stored locally in the browser.

For the Chinese translation, see [README.zh.md](README.zh.md).

## License

Lumenveil is released under the [GNU General Public License v3.0](LICENSE). The default site footer links to the [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh-hans) license for the site's written content; you can replace it with the license that suits your work.
