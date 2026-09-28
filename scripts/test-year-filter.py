#!/usr/bin/env python3
"""Check the contract the year filter in assets/js/main.js depends on.

The bug this guards is the one at the centre of this branch: the year pills
rendered, but the <template> that ships the full card list was gated on
$isList, which came from mainSections. On a site that never sets mainSections
the template was not emitted at all, so the pills could only ever filter the
7 cards already on screen — the filter looked wired up and did nothing.

This asserts the DATA side of that contract against a real Hugo build. It is
deliberately not a browser test: main.js reads these four things and nothing
else, and they are all in the rendered HTML, so they can be checked without a
DOM. What it does NOT cover is the click itself (main.js mutating the live
grid) — that still needs a browser.

Why a fixture at all: the shipped exampleSite has 3 posts, all in 2026, with
pagerSize 7. On that input a filter that does nothing is indistinguishable
from a correct one, so the example site cannot test this. The fixture here
spreads 20 posts over three years, with one year (2024, 9 posts) exceeding
pagerSize so that the client-side slicing path is exercised too.

Usage: scripts/test-year-filter.py       (uses `hugo` from PATH)
       THEME_DIR=/path/to/repo scripts/test-year-filter.py
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from html.parser import HTMLParser

REPO = os.environ.get("THEME_DIR") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "exampleSite")

# 9 exceeds pagerSize 7, so 2024 needs two pages of client-side slicing.
PLAN = {2024: 9, 2025: 7, 2026: 4}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}

fails = []


def check(ok, label, detail=""):
    print("  %-52s %s" % (label, "ok" if ok else "FAIL"))
    if not ok:
        if detail:
            print("      %s" % detail)
        fails.append(label)
    return ok


# --------------------------------------------------------------- tiny DOM
# A regex over the page is not good enough here: a flat scan cannot tell a
# card inside the grid from the same card inside #archive-all-cards, and a
# non-greedy match runs straight past </div>. Track nesting explicitly.
class Node:
    __slots__ = ("tag", "attrs", "children", "parent", "text")

    def __init__(self, tag, attrs=None, parent=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children = []
        self.parent = parent
        self.text = ""

    def cls(self):
        return self.attrs.get("class", "").split()

    def all_text(self):
        out = [self.text]
        for c in self.children:
            out.append(c.all_text())
        return "".join(out)


class DOM(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root")
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, {k: (v if v is not None else "") for k, v in attrs},
                 self.cur)
        self.cur.children.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        n = Node(tag, {k: (v if v is not None else "") for k, v in attrs},
                 self.cur)
        self.cur.children.append(n)

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.text += data


def walk(node):
    for c in node.children:
        yield c
        yield from walk(c)


def find_all(node, pred):
    return [n for n in walk(node) if pred(n)]


def cards_in(node):
    """Direct post-card articles at any depth under node."""
    return [n for n in walk(node)
            if n.tag == "article" and "post-card" in n.cls()]


# --------------------------------------------------------------- fixture
print("theme  :", REPO)
hugo = shutil.which("hugo")
if not hugo:
    print("FATAL: `hugo` not on PATH", file=sys.stderr)
    sys.exit(2)
ver = subprocess.run([hugo, "version"], capture_output=True, text=True)
print("hugo   :", (ver.stdout or ver.stderr).strip().split("\n")[0])

if not os.path.isdir(SRC):
    print("FATAL: no exampleSite at", SRC, file=sys.stderr)
    sys.exit(2)

tmp = tempfile.mkdtemp(prefix="yearfix-")
try:
    fix = os.path.join(tmp, "site")
    os.makedirs(fix)
    # Copy everything except themes/. exampleSite/themes/lumenveil is a
    # symlink to the repo root, and copytree follows it — the repo ends up
    # nested inside itself until the symlink depth limit trips (E40). Link
    # the real theme in instead, which is what the CI step does too.
    for name in os.listdir(SRC):
        if name == "themes":
            continue
        s, d = os.path.join(SRC, name), os.path.join(fix, name)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
    os.makedirs(os.path.join(fix, "themes"))
    os.symlink(REPO, os.path.join(fix, "themes", "lumenveil"))

    posts = os.path.join(fix, "content", "posts")
    shutil.rmtree(posts, ignore_errors=True)
    os.makedirs(posts)
    with open(os.path.join(posts, "_index.md"), "w", encoding="utf8") as f:
        f.write("---\ntitle: Posts\n---\n")
    n = 0
    for year, count in sorted(PLAN.items()):
        for i in range(1, count + 1):
            n += 1
            with open(os.path.join(posts, "p%02d-%d.md" % (n, year)), "w",
                      encoding="utf8") as f:
                f.write("---\n"
                        "title: \"Post %02d Year %d\"\n"
                        "date: %d-%02d-01\n"
                        "draft: false\n"
                        "---\n\nBody %02d.\n"
                        % (n, year, year, (i % 12) + 1, n))
    total = sum(PLAN.values())
    print("fixture: %d posts %s pagerSize=7" % (total, PLAN))
    print()

    r = subprocess.run([hugo, "--config", "hugo.toml", "-d",
                        os.path.join(fix, "public"), "--quiet"],
                       cwd=fix, capture_output=True, text=True)
    if r.returncode != 0:
        print("FATAL: hugo failed rc=%d" % r.returncode, file=sys.stderr)
        print(r.stdout[-3000:], r.stderr[-3000:], file=sys.stderr)
        sys.exit(2)

    page = os.path.join(fix, "public", "posts", "index.html")
    if not os.path.isfile(page):
        print("FATAL: no /posts/ output at", page, file=sys.stderr)
        sys.exit(2)

    dom = DOM()
    with open(page, encoding="utf8") as f:
        dom.feed(f.read())

    # ---------------------------------------------------------- the pills
    print("year pills — main.js builds yearCounts from these")
    pills = {}
    all_pill = None
    for a in find_all(dom.root, lambda n: n.tag == "a"):
        # Read the .archive-count SPAN's text. An earlier version ran the
        # regex `archive-count">\s*(\d+)` against a.all_text(), which returns
        # text content, not markup -- so it could never match and every pill
        # came back None.
        span = [n for n in walk(a)
                if "archive-count" in n.cls()]
        val = int(re.sub(r"\D", "", span[0].all_text()) or 0) if span else None
        if a.attrs.get("data-archive-all") is not None and val is not None:
            all_pill = val
        y = a.attrs.get("data-year")
        if y and val is not None:
            pills[y] = val
    check(all_pill == total, "all-pill count == %d" % total,
          "got %r" % all_pill)
    for year in sorted(PLAN, reverse=True):
        check(pills.get(str(year)) == PLAN[year],
              "%d pill count == %d" % (year, PLAN[year]),
              "got %r" % pills.get(str(year)))

    # ---------------------------------------------------- the full listing
    print()
    print("#archive-all-cards — main.js clones these into the grid")
    tpl = [n for n in find_all(dom.root, lambda n: n.tag == "template")
           if n.attrs.get("id") == "archive-all-cards"]
    if not check(len(tpl) == 1, "the template is emitted", "found %d" % len(tpl)):
        print()
        print("This is the bug this test exists for: with no template, the "
              "filter can only ever see the cards already on screen.")
        print("FAILURES: %d" % len(fails))
        sys.exit(1)
    tpl_cards = cards_in(tpl[0])
    tpl_years = [c.attrs.get("data-year", "") for c in tpl_cards]
    check(len(tpl_cards) == total, "template ships all %d cards" % total,
          "got %d" % len(tpl_cards))
    got = Counter(tpl_years)
    check(all(got.get(str(y), 0) == c for y, c in PLAN.items()),
          "every card's data-year matches its post",
          "template years %r" % dict(sorted(got.items())))

    # ---------------------------------------------------------- page one
    print()
    print("page-1 grid — the unfiltered initial view")
    grid = [n for n in find_all(dom.root,
                                lambda n: "data-post-grid" in n.attrs)]
    if not check(len(grid) == 1, "the grid is emitted", "found %d" % len(grid)):
        sys.exit(1)
    grid_cards = cards_in(grid[0])
    per_page = int(grid[0].attrs.get("data-per-page") or 7)
    check(per_page == 7, "pagerSize is 7", "got %d" % per_page)
    check(len(grid_cards) == min(per_page, total),
          "page 1 holds min(7, %d) = %d cards" % (total, min(per_page, total)),
          "got %d" % len(grid_cards))
    # data-year is a string attribute; PLAN is keyed by int. Third time on
    # this comparison in this session -- convert on the attribute side.
    check(all(int(c.attrs.get("data-year", -1)) in PLAN for c in grid_cards),
          "grid card years are all real",
          "got %r" % [c.attrs.get("data-year") for c in grid_cards])

    # ------------------------------------------------------ the filtering
    # Replay main.js update(year) against the real data. matches/visible come
    # from two different places, so they can disagree; assert they don't, and
    # that the card count each year yields is the one the pill advertises.
    print()
    print("replay of main.js update(year) against this build")
    for year in [""] + [str(y) for y in sorted(PLAN, reverse=True)]:
        if year:
            matches = [y for y in tpl_years if y == year]
            visible = pills.get(year, 0)
            pages = max(1, -(-visible // per_page))
            grid_len = len(matches[:per_page])  # one page of the slice
        else:
            matches = tpl_years
            visible = all_pill or 0
            pages = max(1, -(-visible // per_page))
            grid_len = len(matches)  # 'all' is unsliced
        expect = PLAN[int(year)] if year else total
        check(visible == expect and len(matches) == expect,
              "%s: pill count matches the cards available"
              % (year or "all"),
              "visible=%d matches=%d expected=%d" % (visible, len(matches), expect))
        check(grid_len == len(matches if not year else matches[:per_page]),
              "%s: grid receives what the filter selected" % (year or "all"),
              "grid=%d" % grid_len)

    four = [y for y in tpl_years if y == "2024"]
    check(len(four[:7]) + len(four[7:14]) == PLAN[2024]
          and max(1, -(-len(four) // per_page)) == 2,
          "2024 (9 posts) paginates into 2 pages, 7 + 2")

    print()
    if fails:
        print("FAILURES: %d" % len(fails))
        for f in fails:
            print("  - %s" % f)
        sys.exit(1)
    print("year filter contract: all checks passed")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
