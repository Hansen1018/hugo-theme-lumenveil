# Lumenveil

A luminous, responsive Hugo theme with glass surfaces, aurora ambience, automatic light and dark modes, and a reading-first experience.

[中文说明](#中文说明) · [English](#english)

## English

### Features

- Responsive home, archive, taxonomy, term, article, and 404 layouts
- Automatic light/dark mode with a persistent manual switch
- Client-side search powered by Hugo JSON output
- Categories, tags, pagination, RSS, sitemap, and robots.txt support
- Article table of contents, reading time, word count, previous/next navigation
- Syntax highlighting and one-click code or article-link copy
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

Set the theme in `hugo.toml`:

```toml
theme = 'lumenveil'
```

To update the theme later:

```bash
git submodule update --remote --merge
```

### Required configuration

Search requires a JSON output for the home page. Add the following configuration to your site:

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
draft: false
description: "A short summary displayed in article cards and metadata."
categories: ["Notes"]
tags: ["Hugo", "Writing"]
toc: true
---
```

### Run locally

```bash
hugo server -D
```

Open `http://localhost:1313/` in your browser.

### Customization

- Edit site identity and social links under `[params]`.
- Replace `static/favicon.svg` and `static/og.svg` with your own brand assets.
- Override any theme file by creating the same path in your Hugo site's `layouts`, `assets`, or `static` directory.
- The theme follows the system color preference by default. A visitor's manual selection is stored locally in the browser.

## 中文说明

Lumenveil（光幕）是一款面向个人博客的 Hugo 主题，以通透玻璃表面、柔和极光背景和舒适长文阅读为核心，同时提供完整的浅色与深色模式。

### 主要功能

- 首页、文章归档、分类、标签、正文与 404 页面
- 自动跟随系统的浅色/深色模式，并记忆手动选择
- 基于 Hugo JSON 输出的前端全文搜索
- 分类、标签、分页、RSS、站点地图与 robots.txt
- 文章目录、阅读时间、字数统计、上一篇/下一篇
- 代码高亮、代码复制与文章链接复制
- Open Graph、Twitter Card、Canonical 和 JSON-LD
- 响应式导航、键盘焦点和减少动态效果支持
- Hugo Pipes 自动压缩与资源指纹

### 安装

在 Hugo 站点根目录执行：

```bash
git submodule add https://github.com/Hansen1018/hugo-theme-lumenveil.git themes/lumenveil
```

然后在 `hugo.toml` 中启用：

```toml
theme = 'lumenveil'
```

搜索功能依赖首页 JSON 输出，请复制上方 [Required configuration](#required-configuration) 中的配置，并按需修改 `[params]` 和菜单内容。

### 新建文章

```bash
hugo new content posts/my-first-post.md
hugo server -D
```

主题自带文章原型。发布前将文章 Front Matter 中的 `draft` 改为 `false`。

## License

Lumenveil is released under the [GNU General Public License v3.0](LICENSE).
