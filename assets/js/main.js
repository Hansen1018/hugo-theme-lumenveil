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

  menuToggle?.addEventListener('click', () => {
    const open = menu?.classList.toggle('is-open') ?? false
    menuToggle.setAttribute('aria-expanded', String(open))
  })

  menu?.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => {
    menu.classList.remove('is-open')
    menuToggle?.setAttribute('aria-expanded', 'false')
  }))

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
    if (typeof searchDialog.showModal === 'function') searchDialog.showModal()
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
    const wrapper = pre.closest('.highlight') || pre.parentElement
    if (!wrapper || wrapper.querySelector('.copy-code')) return
    if (getComputedStyle(wrapper).position === 'static') wrapper.style.position = 'relative'
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
    try {
      await navigator.clipboard.writeText(window.location.href)
      event.currentTarget.textContent = '链接已复制'
    } catch {
      event.currentTarget.textContent = '复制失败'
    }
    window.setTimeout(() => { event.currentTarget.textContent = '复制文章链接' }, 1600)
  })

  const archive = document.querySelector('[data-archive]')
  if (archive) {
    const grid = document.querySelector('[data-post-grid]')
    const titleNode = document.querySelector('[data-archive-title]')
    const labelNode = document.querySelector('[data-archive-label]')
    const emptyNode = document.querySelector('[data-archive-empty]')
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
    const yearPills = Array.from(pills)
    const update = (year) => {
      cards.forEach((card) => {
        const cardYear = card.dataset.year || ''
        const match = !year || cardYear === year
        card.classList.toggle('is-hidden', !match)
      })
      const visible = year ? (yearCounts.get(year) || 0) : allCount
yearPills.forEach((pill) => pill.classList.toggle('is-active', pill.dataset.year === year))
      const allPill = archive.querySelector('[data-archive-all]')
      if (allPill) allPill.classList.toggle('is-active', !year)
      if (titleNode) titleNode.textContent = year ? `${year} 年文章` : '全部文章'
      if (labelNode) labelNode.textContent = year ? `Year ${year}` : 'All Articles'
      if (emptyNode) emptyNode.hidden = visible !== 0 || !year
      if (pagination) {
        if (year) {
          buildClientPagination(visible)
        } else {
          restoreServerPagination()
        }
      }
    }
    archive.querySelector('[data-archive-all]')?.addEventListener('click', (event) => {
      event.preventDefault()
      const url = new URL(window.location.href)
      url.searchParams.delete('year')
      window.history.replaceState(null, '', url)
      update('')
    })
    pills.forEach((pill) => pill.addEventListener('click', (event) => {
      event.preventDefault()
      const year = pill.dataset.year
      const url = new URL(window.location.href)
      url.searchParams.set('year', year)
      window.history.replaceState(null, '', url)
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
    update(new URLSearchParams(window.location.search).get('year') || '')
  }
})()

  // Page view counter — front matter baseline + per-visitor localStorage count
  // Display = .Params.views (authoritative baseline) + this visitor's localStorage count
  // Only the inner [data-page-views-num] gets updated; the " 次阅读" suffix stays put.
  const pageViews = document.querySelector('[data-page-views]')
  if (pageViews) {
    const counter = pageViews.querySelector('[data-page-views-num]')
    if (counter) {
      const baseline = parseInt(pageViews.dataset.pageViews, 10) || 0
      const key = 'lumenveil-views-' + location.pathname
      let visited = parseInt(localStorage.getItem(key), 10) || 0
      visited += 1
      try { localStorage.setItem(key, visited) } catch {}
      counter.textContent = baseline + visited
    }
  }
