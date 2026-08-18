# Lumenveil（光幕）

A luminous, responsive Hugo theme with glass surfaces, aurora ambience, automatic light and dark modes, search, galleries, and a reading-first experience for long-form content.

[English](README.md) · [中文说明](#lumenveil光幕) · [Screenshots](#截图)

Lumenveil（光幕）是一款面向个人博客的 Hugo 主题，以通透玻璃表面、柔和极光背景和舒适长文阅读为核心，并提供完整的浅色与深色模式。

在线预览：<https://blog.hansendong.top>

## 截图

### 浅色模式

| 首页 | 文章列表 |
| --- | --- |
| ![首页：极光背景与状态徽章](docs/screenshots/home.png) | ![文章归档页：本地化标题与分页](docs/screenshots/posts.png) |

| 文章页 | 关于页 |
| --- | --- |
| ![文章页：PhotoSwipe 图集与代码复制](docs/screenshots/post.png) | ![关于页：玻璃表面与联系方式表格](docs/screenshots/about.png) |

### 深色模式

| 首页 | 文章列表 |
| --- | --- |
| ![深色首页：极光辉光](docs/screenshots/home-dark.png) | ![深色文章归档页](docs/screenshots/posts-dark.png) |

| 文章页 | 关于页 |
| --- | --- |
| ![深色文章页：PhotoSwipe 图集](docs/screenshots/post-dark.png) | ![深色关于页：玻璃表面](docs/screenshots/about-dark.png)
### 移动端

| 首页 | 文章列表 |
| --- | --- |
| ![移动端首页（浅色）](docs/screenshots/home-mobile.png) | ![移动端文章列表（浅色）](docs/screenshots/posts-mobile.png) |

| 文章页 | 关于页 |
| --- | --- |
| ![移动端文章页（浅色）](docs/screenshots/post-mobile.png) | ![移动端关于页（浅色）](docs/screenshots/about-mobile.png) |

| 首页（深色） | 文章列表（深色） |
| --- | --- |
| ![移动端首页（深色）](docs/screenshots/home-mobile-dark.png) | ![移动端文章列表（深色）](docs/screenshots/posts-mobile-dark.png) |

| 文章页（深色） | 关于页（深色） |
| --- | --- |
| ![移动端文章页（深色）](docs/screenshots/post-mobile-dark.png) | ![移动端关于页（深色）](docs/screenshots/about-mobile-dark.png) |
 |

## 主要功能

- 首页、文章归档、分类、标签、正文、相册与 404 页面
- 极光背景、玻璃卡片、封面图全幅展示
- 自动跟随系统的浅色/深色模式，并记忆手动选择
- 基于 Hugo JSON 输出的前端全文搜索
- 分类、标签、分页、RSS、站点地图与 robots.txt
- 文章目录、阅读时间、字数统计、最后更新时间与通过 busuanzi partial 显示的实时跨访客阅读次数（第三方 CN 服务）
- 页脚动态版权（`since` 至今）和 CC BY-NC-SA 4.0 许可链接
- 代码高亮、代码复制与文章链接复制
- 由 PhotoSwipe 驱动的相册 shortcode，使用 CSS 网格布局
- 可选的 Artalk 评论模块 —— 配置驱动的 partial，样式与文章卡片对齐（玻璃卡片、按钮--ghost 等），自动通过现有 CSS Grid 与 .article-main 列对齐，并在评论列表加载时加入逐条 stagger fade-in
- 可选的 `cover` 封面图 — 支持 page-bundle 图片或 `static/` 静态资源，在文章列表中作为缩略图展示
- Open Graph、Twitter Card、Canonical 和 JSON-LD
- 响应式导航、键盘焦点和减少动态效果支持
- Hugo Pipes 自动压缩与资源指纹

## 安装

在 Hugo 站点根目录执行：

```bash
git submodule add https://github.com/Hansen1018/hugo-theme-lumenveil.git themes/lumenveil
```

然后在 `hugo.toml` 中启用：

```toml
theme = 'lumenveil'
```

搜索功能依赖首页 JSON 输出，请按需复制 [README.md](README.md#required-configuration) 中 *Required configuration* 章节的完整 `hugo.toml` 示例，并修改其中的 `[params]` 与菜单内容。

## 新建文章

```bash
hugo new content posts/my-first-post.md
hugo server -D
```

主题自带文章原型。发布前将文章 Front Matter 中的 `draft` 改为 `false`。

示例 Front Matter：

```yaml
---
title: "你好世界"
date: 2026-08-10T10:00:00+08:00
lastmod: 2026-08-15T18:30:00+08:00
draft: false
description: "摘要，会在文章卡片和 meta 区域显示。"
categories: ["笔记"]
tags: ["Hugo", "写作"]
cover: "images/hello-world.jpg"   # 可选；首先查 page-bundle 资源，找不到时 fallback 到 static/ 路径
toc: true
---
```

`cover` 可选。设置后会在归档列表页作为文章卡片缩略图。值先按 page-bundle 资源查找，找不到时 fallback 到 `static/` 下的路径（例如 `cover: images/foo.png` 解析为 `/images/foo.png`）。

## 相册 shortcode

将图片放入 `static/gallery/<name>/` 目录，然后在文章中：

```md
{{< gallery "gallery/2026-tokyo" >}}
```

短代码会渲染响应式 CSS 网格，并使用 PhotoSwipe 提供大图浏览。

### CSS 组件架构

`main.css` 故意删除了。主题用 Hugo 的 `resources.Match` + `resources.Concat` 在 build 时把按组件拆分的文件 bundle 起来：

```go
{{ $main := resources.Match "css/components/_*.css" | resources.Concat "main.css" | minify | fingerprint }}
```

组件文件在 `assets/css/components/_<name>.css`，一个文件对应一个 BEM 命名空间：

| 文件 | BEM 前缀 | 内容 |
| --- | --- | --- |
| `_tokens.css` | (root vars) | `:root` 自定义属性，浅色主题覆盖 |
| `_reset.css` | (global) | `*, html, body, a, button, img, ::selection, :focus-visible, ::-webkit-scrollbar` |
| `_utilities.css` | (global) | `.sr-only, .skip-link, .glass, .glass::before, .site-shell` |
| `_aurora.css` | `.aurora, .aurora__*` | 背景画布，光斑，drift 动画 |
| `_layout.css` | `.section, .page-hero, .breadcrumbs, .empty-state, .eyebrow` | 页面框架 |
| `_article.css` | `.article, .article-header, .article-cover, .prose, .copy-code` | 文章正文 |
| `_comments.css` | `.article-comments` | Artalk 评论容器 |
| `_like.css` | `.article-like, .like-btn, .like-icon, .like-count` | 文章点赞 CTA |
| `_gallery.css` | `.gallery-image, .pswp__*, .pswp-gallery, .pswp-item` | PhotoSwipe 覆盖 |
| `_search.css` | `.search-dialog, .search-field, .search-result, .search-empty, kbd` | 搜索弹窗 |
| `_term.css` | `.term-grid, .term-card` | 分类列表 |
| `_post.css` | `.post-card, .post-grid, .post-meta, .post-nav, .read-link, .tag-list` | 文章列表 + 翻页 |
| `_archive.css` | `.archive-board, .archive-block, .archive-count, .archive-empty` | archive 页 |
| `_toc.css` | `.toc, .toc__inner` | TOC 侧边栏 |
| `_404.css` | `.not-found, .not-found__*, .suggest-card` | 404 页 |
| `_back-to-top.css` | `.back-to-top` | 返回顶部按钮 |
| `_douban-card.css` | `.douban-card, .douban-card__*` | douban shortcode |
| `_header.css` | `.site-header, .brand, .main-nav, .icon-button, .menu-toggle, .header-actions` | 顶部导航 |
| `_footer.css` | `.site-footer, .footer-inner, .footer-bottom, .footer-links` | footer |
| `_home.css` | `.hero, .hero__*, .chip, .button, .fade-up, .explore-panel, .about-panel` | 首页/hero |

**下划线前缀**是关键：ASCII 排序时 `_` (0x5F) 在小写字母 (0x61+) 之前，所以 `resources.Match "css/components/_*.css"` 返回的文件顺序恰好匹配 CSS cascade 顺序：

- `_tokens` 和 `_reset` 最先（CSS 变量必须先定义）
- `_aurora` / `_utilities` 接着（页面框架）
- 之后是 BEM 组件按 cascade 顺序

Build 时 `resources.Concat` 把所有文件 bundle 成单个 `main.min.<hash>.css`（没有 `@import` 瀑布、单个 HTTP 请求、单个 cache key）。

**添加新组件**：

1. 创建 `assets/css/components/_<name>.css`，BEM 命名空间
2. 文件名必须以 `_` 开头，确保 cascade 顺序正确
3. 组件自动被 `resources.Match "css/components/_*.css"` 拾起——不用改 `head.html`

## 许可

Lumenveil 主题以 [GNU General Public License v3.0](LICENSE) 发布。站点默认页脚的 CC BY-NC-SA 4.0 链接用于站点文字内容，请按需要替换为适合你的许可协议。