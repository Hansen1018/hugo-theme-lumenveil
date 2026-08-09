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
})()
