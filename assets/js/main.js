(() => {
  const header = document.querySelector('[data-header]')
  const menu = document.querySelector('#main-nav')
  const menuToggle = document.querySelector('[data-menu-toggle]')
  const searchDialog = document.querySelector('#search-dialog')
  const searchInput = document.querySelector('#search-input')
  const searchResults = document.querySelector('#search-results')
  const themeToggle = document.querySelector('[data-theme-toggle]')
  let searchIndex = null

  const updateThemeLabel = () => {
    if (!themeToggle) return
    const light = document.documentElement.dataset.theme === 'light'
    const label = light ? '切换深色模式' : '切换浅色模式'
    themeToggle.setAttribute('aria-label', label)
    themeToggle.setAttribute('title', label)
  }

  updateThemeLabel()
  themeToggle?.addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light'
    document.documentElement.dataset.theme = next
    try { localStorage.setItem('lumenveil-theme', next) } catch {}
    updateThemeLabel()
  })

  const colorScheme = window.matchMedia('(prefers-color-scheme: light)')
  colorScheme.addEventListener?.('change', (event) => {
    try {
      if (localStorage.getItem('lumenveil-theme')) return
    } catch {}
    document.documentElement.dataset.theme = event.matches ? 'light' : 'dark'
    updateThemeLabel()
  })

  const updateHeader = () => header?.classList.toggle('is-scrolled', window.scrollY > 20)
  updateHeader()
  window.addEventListener('scroll', updateHeader, { passive: true })

  document.addEventListener('keydown', (e) => { if (e.key === "Escape" && menu?.classList.contains("is-open")) { menu.classList.remove("is-open"); menuToggle.setAttribute("aria-expanded", "false"); menuToggle.focus(); } });

menuToggle?.addEventListener('click', () => {
    const open = menu?.classList.toggle('is-open') ?? false
    menuToggle.setAttribute('aria-expanded', String(open))
  })

  menu?.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => {
    menu.classList.remove('is-open')
    menuToggle?.setAttribute('aria-expanded', 'false')
  }))

  // Escape closes the mobile menu (keyboard a11y).
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && menu?.classList.contains('is-open')) {
      menu.classList.remove('is-open')
      menuToggle?.setAttribute('aria-expanded', 'false')
    }
  })

  const revealNodes = document.querySelectorAll('[data-reveal]')
  if ('IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => entry.target.classList.toggle('is-visible', entry.isIntersecting))
    }, { threshold: 0.08, rootMargin: '0px 0px -8% 0px' })
    revealNodes.forEach((node) => revealObserver.observe(node))
  } else {
    revealNodes.forEach((node) => node.classList.add('is-visible'))
  }

  const escapeHTML = (value) => String(value).replace(/[&<>'"]/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  })[char])

  const loadSearch = async () => {
    if (searchIndex) return searchIndex
    const response = await fetch(searchDialog.dataset.index)
    if (!response.ok) throw new Error('Search index unavailable')
    searchIndex = await response.json()
    return searchIndex
  }

  const renderSearch = (query) => {
    const term = query.trim().toLocaleLowerCase()
    if (!term) {
      searchResults.innerHTML = '<p class="search-empty">输入关键词开始搜索。</p>'
      return
    }
    if (!searchIndex) return
    const matches = searchIndex.filter((item) => {
      const haystack = [item.title, item.description, item.content, ...(item.tags || [])].join(' ').toLocaleLowerCase()
      return haystack.includes(term)
    }).slice(0, 12)
    searchResults.innerHTML = matches.length
      ? matches.map((item) => `<a class="search-result" href="${escapeHTML(item.url)}"><strong>${escapeHTML(item.title)}</strong><p>${escapeHTML(item.description || '暂无摘要')}</p><small>${escapeHTML(item.date)}${item.tags?.length ? ` · ${escapeHTML(item.tags.join(' / '))}` : ''}</small></a>`).join('')
      : '<p class="search-empty">没有匹配的文章，请尝试其他关键词。</p>'
  }

  const openSearch = async () => {
    if (!searchDialog) return
    if (typeof searchDialog.showModal === 'function' && !searchDialog.open) searchDialog.showModal()
    searchInput?.focus()
    if (!searchIndex) searchResults.innerHTML = '<p class="search-empty">正在加载搜索索引…</p>'
    try {
      await loadSearch()
      renderSearch(searchInput.value)
    } catch {
      searchResults.innerHTML = '<p class="search-empty">搜索索引加载失败，请稍后重试。</p>'
    }
  }

  document.querySelectorAll('[data-search-open]').forEach((button) => button.addEventListener('click', openSearch))
  document.querySelector('[data-search-close]')?.addEventListener('click', () => searchDialog?.close())
  searchDialog?.addEventListener('click', (event) => {
    if (event.target === searchDialog) searchDialog.close()
  })
  searchInput?.addEventListener('input', (event) => renderSearch(event.target.value))

  const initialQuery = new URLSearchParams(window.location.search).get('q')
  if (initialQuery && searchInput) {
    searchInput.value = initialQuery
    openSearch()
  }

  document.querySelectorAll('.prose pre').forEach((pre) => {
    let wrapper = pre.closest('.highlight')
    if (!wrapper) {
      // render-codeblock.html (hljs mode) emits raw <pre><code> without a
      // .highlight wrapper. Create one so the absolute-positioned copy
      // button anchors to the code block instead of the whole .prose body.
      wrapper = document.createElement('div')
      wrapper.className = 'highlight'
      pre.parentNode.insertBefore(wrapper, pre)
      wrapper.appendChild(pre)
    }
    if (wrapper.querySelector('.copy-code')) return
    wrapper.style.position = 'relative'
    const button = document.createElement('button')
    button.className = 'copy-code'
    button.type = 'button'
    button.textContent = '复制'
    button.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(pre.textContent)
        button.textContent = '已复制'
      } catch {
        button.textContent = '复制失败'
      }
      window.setTimeout(() => { button.textContent = '复制' }, 1600)
    })
    wrapper.appendChild(button)
  })

  document.querySelector('[data-copy-link]')?.addEventListener('click', async (event) => {
    const btn = event.currentTarget
    const author = btn.dataset.author || ''
    const title = btn.dataset.title || ''
    const date = btn.dataset.date || ''
    const url = btn.dataset.url || window.location.href
    const copyright = btn.dataset.copyright || ''
    const copyrightUrl = btn.dataset.copyrightUrl || ''
    const text = [
      `作者:${author}`,
      `文章标题:[${title}](${url})`,
      `发表时间:${date}`,
      `文章链接:${url}`,
      `版权说明:[${copyright}](${copyrightUrl})`
    ].join('\n')
    try {
      await navigator.clipboard.writeText(text)
      btn.textContent = '✓ 引用已复制'
    } catch {
      btn.textContent = '复制失败'
    }
    window.setTimeout(() => { btn.textContent = '复制文章链接' }, 1600)
  })

  const backToTop = document.querySelector('[data-back-to-top]')
  if (backToTop) {
    const toggleVisible = () => {
      if (window.scrollY > 300) {
        backToTop.classList.add('is-visible')
      } else {
        backToTop.classList.remove('is-visible')
      }
    }
    toggleVisible()
    window.addEventListener('scroll', toggleVisible, { passive: true })
    backToTop.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    })
  }

  const archive = document.querySelector('[data-archive]')
  if (archive) {
    const grid = document.querySelector('[data-post-grid]')
    const titleNode = document.querySelector('[data-archive-title]')
    const labelNode = document.querySelector('[data-archive-label]')
    const emptyNode = document.querySelector('.empty-state')
    const allPill = archive.querySelector('[data-archive-all]')
    const pills = archive.querySelectorAll('[data-year]')
    const cards = grid ? Array.from(grid.children) : []
    const pagination = document.querySelector('.pagination')
    const perPage = parseInt(grid?.dataset.perPage || '8', 10) || 8
    const yearCounts = new Map()
    archive.querySelectorAll('[data-year]').forEach((pill) => {
      const countEl = pill.querySelector('.archive-count')
      if (countEl) yearCounts.set(pill.dataset.year, parseInt(countEl.textContent, 10) || 0)
    })
    const allCount = (() => {
      const el = archive.querySelector('[data-archive-all] .archive-count')
      return el ? (parseInt(el.textContent, 10) || 0) : cards.length
    })()
    const buildClientPagination = (visible) => {
      if (!pagination) return
      const url = new URL(window.location.href)
      const params = url.searchParams
      const currentPage = Math.max(1, parseInt(params.get('page') || '1', 10))
      const totalPages = Math.max(1, Math.ceil(visible / perPage))
      const pageHref = (page) => {
        const u = new URL(window.location.href)
        u.searchParams.set('page', String(page))
        return `${u.pathname}${u.search}`
      }
      pagination.innerHTML = ''
      const prev = document.createElement(currentPage > 1 ? 'a' : 'span')
      prev.className = `pagination-item${currentPage > 1 ? '' : ' is-disabled'}`
      if (currentPage > 1) {
        prev.rel = 'prev'
        prev.href = pageHref(currentPage - 1)
        prev.textContent = '← 上一页'
      } else {
        prev.setAttribute('aria-disabled', 'true')
        prev.textContent = '← 上一页'
      }
      pagination.appendChild(prev)
      const pages = document.createElement('span')
      pages.className = 'pagination-pages'
      for (let i = 1; i <= totalPages; i++) {
        if (i === currentPage) {
          const item = document.createElement('span')
          item.className = 'pagination-item is-active'
          item.setAttribute('aria-current', 'page')
          item.textContent = String(i)
          pages.appendChild(item)
        } else {
          const item = document.createElement('a')
          item.className = 'pagination-item'
          item.href = pageHref(i)
          item.textContent = String(i)
          pages.appendChild(item)
        }
      }
      pagination.appendChild(pages)
      const next = document.createElement(currentPage < totalPages ? 'a' : 'span')
      next.className = `pagination-item${currentPage < totalPages ? '' : ' is-disabled'}`
      if (currentPage < totalPages) {
        next.rel = 'next'
        next.href = pageHref(currentPage + 1)
        next.textContent = '下一页 →'
      } else {
        next.setAttribute('aria-disabled', 'true')
        next.textContent = '下一页 →'
      }
      pagination.appendChild(next)
      pagination.dataset.client = '1'
    }
    const restoreServerPagination = () => {
      if (!pagination) return
      const tpl = pagination.querySelector('[data-pagination-template]')
      if (tpl) {
        pagination.innerHTML = tpl.innerHTML
        pagination.dataset.client = '0'
      }
    }
    const archiveAllTemplate = document.getElementById('archive-all-cards')
    const allArchiveCards = archiveAllTemplate
      ? Array.from(archiveAllTemplate.content.querySelectorAll('article.post-card'))
      : []
    const defaultCardsBackup = grid ? Array.from(grid.children).map((c) => c.cloneNode(true)) : []
    let clientPage = 1
    const yearPills = Array.from(pills)
    const renderClientPagination = (totalPages, page, year) => {
      if (!pagination) return
      if (totalPages <= 1) {
        pagination.innerHTML = ''
        pagination.hidden = true
        pagination.dataset.client = '0'
        return
      }
      pagination.hidden = false
      pagination.dataset.client = '1'
      const buildHref = (n) => {
        const u = new URLSearchParams()
        if (year) u.set('year', year)
        if (n > 1) u.set('page', String(n))
        const s = u.toString()
        return s ? `?${s}` : window.location.pathname
      }
      const prev = page > 1
        ? `<a href="${buildHref(page - 1)}" rel="prev" class="pagination-item">\u2190 \u4e0a\u4e00\u9875</a>`
        : `<span class="pagination-item is-disabled" aria-disabled="true">\u2190 \u4e0a\u4e00\u9875</span>`
      const links = Array.from({ length: totalPages }, (_, i) => i + 1).map((n) => {
        if (n === page) return `<span class="pagination-item is-active" aria-current="page">${n}</span>`
        return `<a href="${buildHref(n)}" class="pagination-item">${n}</a>`
      }).join('')
      const next = page < totalPages
        ? `<a href="${buildHref(page + 1)}" rel="next" class="pagination-item">\u4e0b\u4e00\u9875 \u2192</a>`
        : `<span class="pagination-item is-disabled" aria-disabled="true">\u4e0b\u4e00\u9875 \u2192</span>`
      pagination.innerHTML = `${prev}<span class="pagination-pages">${links}</span>${next}`
    }
    const update = (year) => {
      if (archiveAllTemplate) {
        // archive section: cross-page filter + client-side pagination by perPage
        const source = year ? allArchiveCards.filter((c) => c.dataset.year === year) : allArchiveCards
        const totalPages = Math.max(1, Math.ceil(source.length / perPage))
        const initialClientPage = clientPage
        if (clientPage > totalPages) clientPage = totalPages
        if (clientPage < 1) clientPage = 1
        if (clientPage !== initialClientPage) {
          const u = new URLSearchParams()
          if (year) u.set('year', year)
          if (clientPage > 1) u.set('page', String(clientPage))
          const s = u.toString()
          window.history.replaceState(null, '', s ? `?${s}` : window.location.pathname)
        }
        const start = (clientPage - 1) * perPage
        const pageCards = source.slice(start, start + perPage)
        grid.innerHTML = ''
        pageCards.forEach((card) => grid.appendChild(card.cloneNode(true)))
        renderClientPagination(totalPages, clientPage, year)
      } else {
        // other sections: original toggle logic (no grid re-render, just hide/show)
        if (pagination) {
          pagination.hidden = false
          pagination.dataset.client = '0'
          const tpl = pagination.querySelector('[data-pagination-template]')
          if (tpl) pagination.innerHTML = tpl.innerHTML
        }
        cards.forEach((card) => {
          const cardYear = card.dataset.year || ''
          const match = !year || cardYear === year
          card.classList.toggle('is-hidden', !match)
        })
      }
      const visible = year ? (yearCounts.get(year) || 0) : allCount
      yearPills.forEach((pill) => pill.classList.toggle('is-active', pill.dataset.year === year))
      const allPill = archive.querySelector('[data-archive-all]')
      if (allPill) allPill.classList.toggle('is-active', !year)
      if (titleNode) titleNode.textContent = year ? `${year} 年文章` : '全部文章'
      if (labelNode) labelNode.textContent = year ? `Year ${year}` : 'All Articles'
      if (emptyNode) emptyNode.hidden = visible !== 0 || !year
    }
    pagination?.addEventListener('click', (event) => {
      if (!pagination || pagination.dataset.client !== '1') return
      const link = event.target.closest('a.pagination-item')
      if (!link) return
      event.preventDefault()
      const url = new URL(link.href, window.location.href)
      const p = parseInt(url.searchParams.get('page') || '1', 10)
      if (!Number.isFinite(p) || p < 1) return
      clientPage = p
      const yearParam = url.searchParams.get('year') || ''
      window.history.replaceState(null, '', link.getAttribute('href'))
      update(yearParam)
    })
    archive.querySelector('[data-archive-all]')?.addEventListener('click', (event) => {
      event.preventDefault()
      const url = new URL(window.location.href)
      url.searchParams.delete('year')
      url.searchParams.delete('page')
      window.history.replaceState(null, '', url.pathname)
      clientPage = 1
      update("")
    })
    pills.forEach((pill) => pill.addEventListener('click', (event) => {
      event.preventDefault()
      const year = pill.dataset.year
      const url = new URL(window.location.href)
      url.searchParams.set('year', year)
      url.searchParams.delete('page')
      window.history.replaceState(null, '', url.pathname + url.search)
      clientPage = 1
      update(year)
    }))
    cards.forEach((card) => {
      const date = card.querySelector('time[datetime]')
      if (date) card.dataset.year = (date.getAttribute('datetime') || '').slice(0, 4)
    })
    if (pagination && !pagination.querySelector('[data-pagination-template]')) {
      const tpl = document.createElement('template')
      tpl.setAttribute('data-pagination-template', '')
      tpl.innerHTML = pagination.innerHTML
      pagination.appendChild(tpl)
    }
    if (archiveAllTemplate) {
      const params = new URLSearchParams(window.location.search)
      const rawPageParam = params.get('page')
      const parsedPage = parseInt(rawPageParam || '1', 10)
      if (rawPageParam !== null && (!Number.isFinite(parsedPage) || parsedPage < 1)) {
        params.delete('page')
        const s = params.toString()
        window.history.replaceState(null, '', s ? `?${s}` : window.location.pathname)
      }
      clientPage = Number.isFinite(parsedPage) && parsedPage > 0 ? parsedPage : 1
    }
    update(new URLSearchParams(window.location.search).get('year') || '')
  }
})()

  // Page view counter — busuanzi (third-party CN service).
  // The <span id="busuanzi_value_page_pv"> element is auto-populated by
  // the busuanzi.pure.mini.js script (loaded via layouts/partials/busuanzi.html).
  // No manual JS handling needed here — busuanzi fills the inner span on load,
  // and the outer "X reads" wrapper stays intact.
  // (Earlier we tried Artalk.loadCountWidget + nested <span> structure + manual
  // fetch to Artalk PV API — Artalk 2.x doesn't expose PV via REST and the
  // widget UI doesn't auto-fill an inline <span>. busuanzi is the simplest
  // path that preserves "X reads" format and gives real cross-user counts.)

// Gallery 2-per-row with widths proportional to aspect ratio (Stack-
// style masonry). For each pair, set flex-basis in px so the row
// distributes width by aspect ratio. Both items end up the same
// height naturally because w / aspect = (W - gap) / sum for both.
// Odd-count last item gets 100% row width.
(() => {
  function layout(gallery) {
    const items = Array.from(gallery.children).filter(el =>
      el.classList && el.classList.contains('pswp-item'));
    if (!items.length) return;
    const cs = getComputedStyle(gallery);
    const gap = parseFloat(cs.columnGap || cs.gap) || 14;
    const W = gallery.clientWidth;
    if (!W) return;
    for (let i = 0; i < items.length; i += 2) {
      const a = items[i], b = items[i + 1];
      if (b) {
        const rA = parseFloat(a.dataset.pswpRatio) || 1;
        const rB = parseFloat(b.dataset.pswpRatio) || 1;
        const sum = rA + rB;
        const avail = W - gap;
        a.style.flex = '0 0 ' + ((rA / sum) * avail) + 'px';
        b.style.flex = '0 0 ' + ((rB / sum) * avail) + 'px';
      } else {
        a.style.flex = '0 0 ' + W + 'px';
        a.style.maxWidth = '100%';
      }
    }
  }
  function run() {
    document.querySelectorAll('.pswp-gallery[data-pswp-layout="justified"]').forEach(layout);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
  window.addEventListener('load', run);
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    document.querySelectorAll('.pswp-gallery[data-pswp-layout="justified"] > .pswp-item').forEach(el => {
      el.style.flex = '';
      el.style.maxWidth = '';
    });
    resizeTimer = setTimeout(run, 150);
  });
})();
