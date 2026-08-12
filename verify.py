from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    b = p.chromium.launch(args=['--no-sandbox'])

    # === Mobile viewport test (Since 2013 should be visible) ===
    ctx_m = b.new_context(viewport={'width': 375, 'height': 667})
    pg = ctx_m.new_page()
    pg.goto("https://blog.hansendong.top/", wait_until='networkidle', timeout=30000)
    pg.wait_for_timeout(2000)
    diag_mobile = pg.evaluate("""() => {
        const chips = [...document.querySelectorAll('.hero__chips .chip')];
        const last = chips[chips.length - 1];
        const lastCS = last ? getComputedStyle(last) : null;
        const lastRect = last ? last.getBoundingClientRect() : null;
        return {
            chipCount: chips.length,
            chipTexts: chips.map(c => c.textContent.trim()),
            lastChip: last ? { text: last.textContent.trim(), display: lastCS.display, visibility: lastCS.visibility, rect: { w: lastRect.width, h: lastRect.height } } : null
        };
    }""")
    print("MOBILE 375:", json.dumps(diag_mobile, ensure_ascii=False))
    pg.evaluate("window.scrollTo(0,0)")
    pg.wait_for_timeout(300)
    pg.screenshot(path='/root/.openclaw/agents/coder/workspace/mobile-home.png', full_page=False)
    ctx_m.close()

    # === PC viewport test (article-share should NOT have card wrapping) ===
    ctx_p = b.new_context(viewport={'width': 1440, 'height': 900})
    pg = ctx_p.new_page()
    pg.goto("https://blog.hansendong.top/archives/2020/12/2020-retro/", wait_until='networkidle', timeout=30000)
    pg.wait_for_timeout(2500)
    pg.evaluate("document.querySelector('.article-share').scrollIntoView({block:'center'})")
    pg.wait_for_timeout(700)
    diag_pc = pg.evaluate("""() => {
        const s = document.querySelector('.article-share');
        const cs = getComputedStyle(s);
        return {
            padding: cs.padding,
            border: cs.border,
            borderRadius: cs.borderRadius,
            background: cs.backgroundColor,
            color: cs.color,
            position: cs.position,
            zIndex: cs.zIndex
        };
    }""")
    print("PC share:", json.dumps(diag_pc, ensure_ascii=False))
    pg.screenshot(path='/root/.openclaw/agents/coder/workspace/pc-share.png', full_page=False)
    ctx_p.close()
    b.close()
