#!/usr/bin/env python3
"""Check that feed summaries never end inside an open container element.

What Hugo 0.167.0 changed
-------------------------
Release 0.167.0 carries d692a243 (#14044): "Automatic summaries are expanded
past summaryLength when needed so they don't end inside an open container
element." Before that fix, Hugo truncated an auto-summary at a word boundary
and could stop in the middle of a `<blockquote>` or list, so the summary
embedded in the feed carried unbalanced markup.

Why this is the theme's problem and not just Hugo's
---------------------------------------------------
The theme ships no RSS template — Hugo's embedded one is used — but it does
decide what gets into a feed:

  layouts/home.json   .Summary, straight into the JSON search/feed payload
  layouts/_partials/post-card.html
  layouts/404.html

So a truncated summary is not a Hugo-internal detail; it is published bytes
that subscribers and the search payload read.

Measured on a real site before/after the upgrade
------------------------------------------------
Building /var/www/blog with 0.166.0 vs 0.167.0 changed 5 of 417 output files.
Every one was an index.xml, and every change was the same thing: 0.166 ended a
description at

    ...强制开启 HTTPS。&lt;/p&gt;</description>

while 0.167 ends it at

    ...强制开启 HTTPS。&lt;/p&gt;&#10;&#10;&lt;/blockquote&gt;</description>

i.e. 0.166 emitted an unclosed blockquote into the feed. That is a real
regression-shaped bug this test now pins.

Version handling — deliberately not asserted below 0.167.0
--------------------------------------------------------
The fix does not exist before 0.167.0, and the CI matrix includes 0.146.0. A
test that demanded balanced markup everywhere would fail that leg for a reason
that is Hugo's, not the theme's, and the usual result of that is someone
deleting the test. So below FIXED_FROM the test reports the known-bad shape and
passes, with the finding printed, which is more useful than a red X nobody can
act on.

Usage: scripts/test-rss-summary.py        (uses `hugo` from PATH)
       THEME_DIR=/path/to/repo scripts/test-rss-summary.py
"""
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser

REPO = os.environ.get("THEME_DIR") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "exampleSite")

# d692a243 shipped in 0.167.0.
FIXED_FROM = (0, 167, 0)

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}

fails = []


def check(ok, label, detail=""):
    print("  %-56s %s" % (label, "ok" if ok else "FAIL"))
    if not ok:
        if detail:
            print("      %s" % detail)
        fails.append(label)
    return ok


class Balance(HTMLParser):
    """Track open tags. The point is not to render anything, only to notice a
    container left open at the end of the description."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.unbalanced = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag in self.stack:
            while self.stack:
                top = self.stack.pop()
                if top == tag:
                    return
            return
        self.unbalanced.append(("stray-close", tag))

    def finish(self):
        return self.unbalanced, list(self.stack)


# A post whose blockquote straddles the summary boundary. Structure:
#   - a short lead-in, comfortably inside the summary
#   - a blockquote that OPENS before summaryLength is reached and CLOSES well
#     after it, so a naive word-boundary truncation lands inside it
# The lead-in length is tuned so the opening > is around word 30 and the
# closing is around word 130, comfortably past any default summaryLength.
POST = """---
title: "Summary container probe {n}"
date: 2026-01-0{n}T10:00:00+08:00
draft: false
description: ""
---

This opening paragraph is deliberately short so that the blockquote below
starts before any plausible summary boundary is reached.

> {words}
>
> trailing line of the quote

A closing paragraph that exists so the post is not only a blockquote.
"""


def make_post(n, count):
    body = " ".join("blockquote-word-%02d" % i for i in range(count))
    return POST.format(n=n, words=body)


def hugo_version():
    out = subprocess.run(["hugo", "version"], capture_output=True, text=True)
    m = re.search(r"v(\d+)\.(\d+)\.(\d+)", out.stdout)
    if not m:
        print("  FATAL: cannot parse `hugo version`")
        print(out.stdout, out.stderr)
        sys.exit(2)
    return tuple(int(x) for x in m.groups())


def main():
    ver = hugo_version()
    print("hugo   : %d.%d.%d" % ver)
    print("theme  : %s" % REPO)
    fixed = ver >= FIXED_FROM
    print("balanced-summary fix (>= 0.167.0) is %s on this version"
          % ("PRESENT" if fixed else "ABSENT"))

    if not os.path.isdir(SRC):
        print("FATAL: no exampleSite at", SRC, file=sys.stderr)
        return 2

    tmp = tempfile.mkdtemp(prefix="rsssum-")
    try:
        site = os.path.join(tmp, "site")
        os.makedirs(site)
        for name in os.listdir(SRC):
            if name == "themes":
                continue
            s, d = os.path.join(SRC, name), os.path.join(site, name)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
        os.makedirs(os.path.join(site, "themes"))
        os.symlink(REPO, os.path.join(site, "themes", "lumenveil"))

        # summaryLength is pinned so the boundary does not move when Hugo
        # changes its default. Without this the test would silently start
        # testing a different truncation point on some future release.
        cfg = os.path.join(site, "hugo.toml")
        with open(cfg, "a") as fh:
            fh.write("\nsummaryLength = 40\n")

        posts = os.path.join(site, "content", "posts")
        os.makedirs(posts, exist_ok=True)
        for i, n in enumerate((100, 160, 240), start=1):
            with open(os.path.join(posts, "probe-%d.md" % i), "w") as fh:
                fh.write(make_post(i, n))

        out = os.path.join(tmp, "pub")
        proc = subprocess.run(
            ["hugo", "--quiet", "--destination", out],
            cwd=site, capture_output=True, text=True)
        if proc.returncode != 0:
            print("  FATAL: fixture build failed")
            print((proc.stdout + proc.stderr)[:2000])
            return 2

        feeds = []
        for dp, _, fns in os.walk(out):
            for fn in fns:
                if fn == "index.xml":
                    feeds.append(os.path.join(dp, fn))
        if not feeds:
            print("  FATAL: no index.xml produced — nothing to check")
            return 2
        print("  feeds: %d" % len(feeds))

        # Pull every <description> out of every feed. RSS puts it in CDATA or
        # escapes it; both end up as markup after html.unescape().
        descs = []
        for f in feeds:
            raw = open(f, encoding="utf-8", errors="replace").read()
            descs += re.findall(r"<description>(.*?)</description>", raw,
                                re.S)
        if not descs:
            print("  FATAL: no <description> elements found")
            return 2
        print("  descriptions: %d" % len(descs))

        offenders = []
        for d in descs:
            text = d
            # Strip the CDATA wrapper if present, then unescape.
            c = re.search(r"<!\[CDATA\[(.*?)\]\]>", text, re.S)
            if c:
                text = c.group(1)
            text = html.unescape(text).strip()
            p = Balance()
            p.feed(text)
            p.close()
            stray, left = p.finish()
            if stray or left:
                offenders.append((stray, left, text[-160:]))

        if offenders:
            print()
            for stray, left, tail in offenders[:3]:
                print("      unclosed-at-end: %s" % (left or "none"))
                if stray:
                    print("      stray closes   : %s" % (stray,))
                print("      tail: ...%s" % tail.replace("\n", "\\n"))
        print()

        if fixed:
            check(not offenders,
                  "no feed summary ends inside an open container",
                  "%d of %d descriptions ended with tags still open"
                  % (len(offenders), len(descs)))
        else:
            # Document the known-bad shape rather than failing a leg that
            # cannot pass: the fix does not exist in this Hugo.
            if offenders:
                print("      NOTE: %d of %d descriptions end with tags open."
                      % (len(offenders), len(descs)))
                print("      That is the pre-0.167.0 behaviour this test was"
                      " written for; not asserted on this version.")
            else:
                print("      NOTE: this Hugo happened to balance the summary"
                      " anyway; nothing to assert either way.")
            check(True, "balanced-summary assertion applies from 0.167.0 only")

        # Independent of the fix: the probe posts must actually reach the feed,
        # otherwise the check above is comparing zero interesting descriptions.
        #
        # The posts need DISTINCT titles and dates, and the first version of
        # this fixture had neither. With no `slug:` front matter Hugo falls back
        # to the title slug, so three same-titled posts all resolved to
        # /posts/summary-container-probe/ and exactly one survived into the
        # feed. The balance check then ran over a set of descriptions that
        # never contained two probes at once — it could not have failed, and it
        # also could not have passed for the right reason. Asserting ">= 3
        # distinct titles" would have caught that, but only after the fact;
        # making the fixtures unique is what makes the earlier assertion
        # meaningful in the first place.
        seen = set()
        for f in feeds:
            raw = open(f, encoding="utf-8", errors="replace").read()
            for t in re.findall(r"<title>([^<]*)</title>", raw):
                m = re.fullmatch(r"Summary container probe (\d+)", t.strip())
                if m:
                    seen.add(int(m.group(1)))
        want = {1, 2, 3}
        check(seen == want,
              "all three probe posts reached the feed",
              "saw probe ids %s, expected %s" % (sorted(seen), sorted(want)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    print("rss summary tests: %s" % ("all checks passed" if not fails
                                     else "%d FAILED" % len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
