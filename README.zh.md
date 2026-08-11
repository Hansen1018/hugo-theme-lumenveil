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
| ![深色文章页：PhotoSwipe 图集](docs/screenshots/post-dark.png) | ![深色关于页：玻璃表面](docs/screenshots/about-dark.png) |

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
- 可选的 Artalk 评论模块 —— 配置驱动的 partial，样式与文章卡片对齐（玻璃卡片、按钮--ghost 等），自动通过现有 CSS Grid 与 .article-main 列对齐
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

## 许可

Lumenveil 主题以 [GNU General Public License v3.0](LICENSE) 发布。站点默认页脚的 CC BY-NC-SA 4.0 链接用于站点文字内容，请按需要替换为适合你的许可协议。