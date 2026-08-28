from playwright.sync_api import sync_playwright

import os
BASE_URL = os.environ.get("BASE_URL", "https://blog.hansendong.top")
# Default targets the Hansen1018 demo site; override with BASE_URL env var
# to test a fork or staging instance. e.g. `BASE_URL=https://staging.example.com python verify.py`

with sync_playwright() as p:
    browser = p.chromium.launch(args=['--no-sandbox'])
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    # Force dark theme via localStorage (lumenveil reads this key)
    page.goto(BASE_URL + "/", wait_until="networkidle", timeout=30000)
    page.evaluate("localStorage.setItem('lumenveil-theme', 'dark')")
    page.goto(BASE_URL + "/archives/2020/12/2020-retro/", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2500)
    page.evaluate("document.querySelector('.article-share').scrollIntoView({block:'center'})")
    page.wait_for_timeout(600)
    diag = page.evaluate("""() => {
        const s = document.querySelector('.article-share');
        const cs = getComputedStyle(s);
        const r = s.getBoundingClientRect();
        return {
            color: cs.color, bg: cs.backgroundColor, border: cs.border,
            zIndex: cs.zIndex, position: cs.position,
            rect: {top: r.top, w: r.width, h: r.height},
            dataTheme: document.documentElement.getAttribute('data-theme')
        };
    }""")
    print("DARK DIAG:", diag)
    page.screenshot(path="/root/.openclaw/agents/coder/workspace/share-dark.png", full_page=False)
    print("saved share-dark.png")
    browser.close()
