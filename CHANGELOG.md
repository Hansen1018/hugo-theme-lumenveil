# Changelog

Detailed release notes per version live in `.release-notes/` (tracked from this
commit onward). This file gives a concise summary for quick scanning.

## v0.2.1 — 2026-08-27

**Highlights**
- Bilibili + YouTube embed shortcodes (privacy-enhanced, tracking-stripped,
  responsive 16:9)
- Inline image caption pill (centered, dark-glass backdrop-blur)
- `layouts/ja/single.html` for the JA section
- Post-meta layout restored (word count + page views + meta-pills)
- `lastmod` displays for freshly-published posts (ge instead of gt)

**Bug fixes**
- Archives meta-pills regression rolled back
- Caption pill selector rewritten to match actual Hugo output

## v0.2.0 — 2026-08-19

**Highlights**
- Categories alongside tags in article header (Chinese display via term
  lookup with `webdev → 建站` fallback)
- Per-page `cover` honored in `og:image` / `twitter:image`
- Cover-image caption gets a dark-glass pill wrapper
- Douban-card light-mode hover uses `--glass-bg-hover` token
- CSS re-split into 23 explicit component slices via `slice + resources.Concat`
- Friends page styling (5/4/3/2 col responsive grid, dashed empty state)
- Opt-in highlight.js with monokai for sites that want client-side highlighting

**Bug fixes**
- `Resources.GetMatch` for page-bundle covers in `og:image`
- `douban-card` selectors dropped during re-split restored
- Unused `chroma.css` removed from head bundle

## v0.1.x and earlier

See git tags (`git tag -l 'v0.1.*'`). Per-version notes were not formalised;
relevant work is visible in `git log --oneline` for those tags.
