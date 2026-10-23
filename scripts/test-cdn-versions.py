#!/usr/bin/env python3
"""Check the CDN library versions the theme pins.

Two independent checks live here, and they fail for different reasons:

1. INTERNAL CONSISTENCY (offline, the default). Every occurrence of a CDN
   library pin under layouts/ must name the SAME version, and every version
   quoted in the README files must match the template pin. Only a full
   x.y.z version quoted in the README is compared: a partial quote such as
   "0.16" is not a pin, and is left alone. This catches a
   half-finished bump. highlight.js is loaded as a stylesheet from jsDelivr
   and as a script from cdnjs, so bumping one source and not the other
   ships a stylesheet from one release next to a highlighter from another;
   that mismatch is invisible in a green build and shows up as broken colours
   in a browser. The README quotes a version in prose, so it drifts the same
   way.

2. UPSTREAM DRIFT (--latest, needs the network). Two questions about each
   pin, in this order: is the pinned version published on the npm registry
   at all, and is the latest release newer than it? The first question
   catches a pin that names a version nobody ever published -- a typo, or
   a version that was withdrawn. Comparing it against the latest release
   cannot catch that, because a pin ABOVE the latest release looks "not
   behind", and a version that does not exist has no file behind it on
   the CDN either. The second question is the ordinary drift.

3. CDN REACHABILITY (--latest, needs the network). Every pinned URL is
   fetched, the way a browser would fetch it. The version pins can agree
   with each other, with the registry and with the README, and still name
   a path the CDN does not have: the page then loads a 404 for the maths
   or the highlighter and renders without it, silently.

The network half has a wall-clock budget of its own (NETWORK_BUDGET). A
registry or a CDN that accepts the connection and then stalls costs the
full per-request timeout for every request in turn, and there are enough
of them -- three packages, each looked up twice, plus every pinned URL
-- to turn a total outage into minutes of waiting. Once the budget is
spent the check stops asking and reports what it could not reach, which
is the same "could not be carried out" outcome a timeout produces.

The network half is deliberately NOT part of pull-request CI: a new
upstream release is not a defect in the PR being reviewed, and failing
every build until somebody bumps the pin teaches people to ignore red CI.
It runs from .github/workflows/cdn-versions.yml on a schedule instead,
where a red run is a signal rather than a roadblock.

Only libraries that are actually pinned are checked. The version number is
read out of the templates rather than duplicated here, so this file cannot
become a second place that has to be edited by hand.

Exit codes:
    0  every check passed
    1  a check FAILED -- pins disagree with each other, with the README, or
       with upstream. A real disagreement is reported even when the
       registry was also unreachable: the disagreement does not depend on
       the network.
    2  the check could not be carried out (network down, unreadable tree,
       unexpected error) and nothing failed. Deliberately distinct from 1:
       a scheduled run that cannot reach the registry must not be reported
       as "your pins are behind", and the workflow opens an issue only on a
       genuine failure.

Usage:
    scripts/test-cdn-versions.py            # internal consistency only
    scripts/test-cdn-versions.py --latest   # also check npm and the CDNs
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYOUTS = os.path.join(REPO, "layouts")
READMES = ("README.md", "README.zh.md")

# Both URL shapes the theme uses. The jsDelivr form carries the version as
# @<version>, the cdnjs form as a path segment /<version>/. A third shape,
# the busuanzi counter URL, is not an npm package and is deliberately not
# matched here: it has no registry to compare against, and its version is
# pinned by the service operator rather than by us.
# The package group allows an optional scope. jsDelivr serves
# @scope/pkg@1.2.3 as well as pkg@1.2.3, and a scoped name the pattern
# does not match would be invisible to every check below.
# The shape of a version as the pins spell it: a digit, then whatever
# a version may carry after it -- another digit, a letter, a dot, a plus
# or a dash. It is ONE constant because the pin patterns and the README
# pattern have to read a version the same way: a pattern that stopped
# one character earlier would compare a different string than the one
# the template pins, and the difference shows up as a mismatch that is
# not there.
VERSION = r"[0-9][0-9A-Za-z.+-]*"
# The fault harness spells the same rule out again, in
# scripts/test-cdn-versions-faults.py. It cannot import this file: it
# tests a COPY of the tree, and importing the thing under test is how
# a test stops testing it.

JSDELIVR = re.compile(
    r"cdn\.jsdelivr\.net/npm/((?:@[A-Za-z0-9._-]+/)?[A-Za-z0-9._-]+)"
    r"@(" + VERSION + r")")
CDNJS = re.compile(
    r"cdnjs\.cloudflare\.com/ajax/libs/([A-Za-z0-9._-]+)/(" + VERSION + r")")

# The whole URL, for the reachability check. The version is part of it, so
# the URL names one exact file on one exact CDN: the thing a browser would
# fetch, and the thing that 404s if the version or the path inside it is
# wrong. Both npm hosts are covered; the busuanzi counter is not an npm
# package and is not checked here for the same reason as above.
CDN_URL = re.compile(
    r"https?://(?:cdn\.jsdelivr\.net/npm/|cdnjs\.cloudflare\.com/ajax/libs/)"
    r"[^\s\"'()<>,;]+")

fails = []
unreachable = []

# The wall-clock budget for the whole network half of the check.
#
# A registry or a CDN that accepts the connection and then stalls costs
# the full per-request timeout for every request in turn, and there are
# enough of them -- three packages, each looked up twice, plus every
# pinned URL -- to turn a total outage into minutes of waiting. Once the
# budget is spent the check stops asking and reports what it could not
# reach, which is the same "could not be carried out" outcome (exit 2)
# that a single timeout already produces.
NETWORK_BUDGET = 90.0
_deadline = None


def start_network_budget():
    global _deadline
    _deadline = time.monotonic() + NETWORK_BUDGET


def budget_spent():
    """Has the network budget run out?"""
    if _deadline is None:
        return False
    return time.monotonic() > _deadline


def fail(msg):
    fails.append(msg)
    print("  FAIL  %s" % msg)


def ok(msg):
    print("  ok    %s" % msg)


def version_tuple(v):
    """(major, minor, patch) for a version string, or None if it is not one.

    Pre-release and build metadata are dropped: npm's `latest` dist-tag is
    never a pre-release, and comparing `1.2.3-rc1` against `1.2.3` by
    numeric parts is the only comparison that decides the question this
    script asks, which is whether a newer release exists.

    None means the string does not name a version at all -- `1.2.x`. The
    caller has to report that rather than guess, and the guess this
    function used to make was always in the direction that hides a
    defect: an unreadable component became 0, so a malformed pin looked
    like the oldest possible version rather than like a broken one.

    The rule is the one the fault harness parses versions by, so the two
    cannot answer the same question two different ways: a part that is
    not a number is not a version to either of them, and a version with
    more than three parts is compared by its first three.
    """
    core = v.split("+")[0].split("-")[0]
    parts = []
    for part in core.split("."):
        if not re.fullmatch(r"[0-9]+", part):
            return None
        parts.append(int(part))
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def collect_pins():
    """{package: {version: ["file:line", ...]}} over layouts/."""
    pins = {}
    for root, dirs, files in os.walk(LAYOUTS):
        dirs[:] = [d for d in dirs if d != "exampleSite"]
        for name in sorted(files):
            path = os.path.join(root, name)
            try:
                with open(path, encoding="utf-8") as fh:
                    lines = fh.read().splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            rel = os.path.relpath(path, REPO)
            for lineno, line in enumerate(lines, 1):
                for pattern in (JSDELIVR, CDNJS):
                    for m in pattern.finditer(line):
                        pkg, ver = m.group(1), m.group(2)
                        pins.setdefault(pkg, {}).setdefault(ver, []).append(
                            "%s:%d" % (rel, lineno))
    return pins


def collect_urls():
    """{url: ["file:line", ...]} for every npm CDN URL under layouts/."""
    urls = {}
    for root, dirs, files in os.walk(LAYOUTS):
        dirs[:] = [d for d in dirs if d != "exampleSite"]
        for name in sorted(files):
            path = os.path.join(root, name)
            try:
                with open(path, encoding="utf-8") as fh:
                    lines = fh.read().splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            rel = os.path.relpath(path, REPO)
            for lineno, line in enumerate(lines, 1):
                for m in CDN_URL.finditer(line):
                    urls.setdefault(m.group(0), []).append("%s:%d" % (rel, lineno))
    return urls


def http_status(url, timeout=20):
    """(status, kind, detail) for a HEAD request against a URL.

    kind is None when the server answered, "gone" when it answered 404 (the
    file is not there) and "unreachable" when it could not be asked at all --
    a 5xx, a timeout, a DNS failure. The middle one is a fact about the
    tree; the last one is the absence of one.
    """
    if budget_spent():
        return None, "unreachable", "the network budget was spent"
    req = urllib.request.Request(
        url, method="HEAD", headers={"User-Agent": "lumenveil-cdn-versions"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, None, None
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return 404, "gone", "HTTP 404"
        if exc.code in (403, 405, 501):
            # Some CDNs refuse HEAD. Ask for the file itself instead of
            # declaring the pin broken on the strength of a method the
            # host happens not to implement.
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "lumenveil-cdn-versions"})
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return resp.status, None, None
            except urllib.error.HTTPError as exc2:
                if exc2.code == 404:
                    return 404, "gone", "HTTP 404"
                return exc2.code, "unreachable", "HTTP %s" % exc2.code
            except Exception as exc2:  # network, DNS, timeout
                return None, "unreachable", str(exc2)
        return exc.code, "unreachable", "HTTP %s" % exc.code
    except Exception as exc:  # network, DNS, timeout
        return None, "unreachable", str(exc)


def check_urls(urls):
    """Every pinned CDN URL has to resolve.

    The version pins above agree with each other and with the registry.
    That is not the same as the file being there: a version can be
    published and still not carry the path the template asks for, and the
    page then loads a 404 for the maths or the highlighter and renders
    without it, silently. This asks the CDN the question the browser
    will ask.
    """
    print()
    print("[4] the pinned CDN URLs resolve")
    ordered = sorted(urls)
    for i, url in enumerate(ordered):
        where = ", ".join(urls[url])
        if budget_spent():
            # The budget is gone, so the URLs after this one cannot be
            # asked. ONE entry for all of them rather than one per URL:
            # the reason is the same for every one, and a flood of
            # identical errors buries the line that says what actually
            # happened. The count says how many went unchecked, so
            # nothing is quietly dropped.
            left = len(ordered) - i
            unreachable.append(
                "%d pinned CDN URL(s) could not be checked: the network "
                "budget was spent" % left)
            print("  ERROR the network budget was spent: %d pinned URL(s) "
                  "were not checked" % left)
            break
        status, kind, detail = http_status(url)
        if kind is None:
            ok("%s resolves (HTTP %d, %s)" % (url, status, where))
        elif kind == "gone":
            fail("%s is pinned but the CDN does not have that file (HTTP 404, "
                 "%s)" % (url, where))
        else:
            unreachable.append("%s: the CDN could not be reached (%s)"
                               % (url, detail))
            print("  ERROR %s: the CDN could not be reached (%s)" % (url, detail))


def check_consistency(pins):
    print("[1] internal consistency (offline)")
    if not pins:
        fail("no CDN pins found under layouts/ -- the pin format changed?")
        return
    for pkg in sorted(pins):
        versions = pins[pkg]
        if len(versions) == 1:
            ver = list(versions)[0]
            if version_tuple(ver) is None:
                # A pin that names no version names no file: there is no
                # such release on npm and no such path on the CDN. The
                # offline half is where this is caught, because the
                # offline half is what runs on every pull request.
                fail("%s is pinned at %s, which is not a version number"
                     % (pkg, ver))
                continue
            ok("%s pinned at %s (%d occurrence%s)"
               % (pkg, ver, len(versions[ver]),
                  "" if len(versions[ver]) == 1 else "s"))
        else:
            detail = "; ".join(
                "%s at %s (%d occurrence%s)"
                % (v, ", ".join(versions[v]), len(versions[v]),
                   "" if len(versions[v]) == 1 else "s")
                for v in sorted(versions))
            fail("%s is pinned at more than one version: %s" % (pkg, detail))


def check_readme(pins):
    """A version quoted in the README prose must match the template pin."""
    print()
    print("[2] README prose matches the templates")
    for pkg in sorted(pins):
        if len(pins[pkg]) != 1:
            # Already reported by check_consistency; a mismatch here would be
            # a consequence of that, not a separate fact.
            continue
        pinned = list(pins[pkg])[0]
        # A lookbehind rather than \b: a scoped package name starts with
        # "@", which is not a word character, so \b would never match in
        # front of it.
        # The quoted version is a full x.y.z, and nothing may follow it
        # that would make it longer. A pattern that stopped after three
        # numbers read "1.2.3" out of a README that says "1.2.3.4" or
        # "1.2.3-rc1" and compared that against the pin -- a mismatch
        # that is not there, or a match that is not one. The lookaheads
        # refuse the truncated reading instead of accepting it: what
        # follows the version may not be a digit, a pre-release marker,
        # or a dot and a digit. The full stop that ends a sentence is
        # not a version character, so "loads KaTeX 0.16.11." still
        # quotes 0.16.11.
        pattern = re.compile(
            r"(?i)(?<!\w)%s\s+v?(\d+\.\d+\.\d+)(?!\d)(?![-+])(?!\.\d)"
            % re.escape(pkg))
        for name in READMES:
            path = os.path.join(REPO, name)
            if not os.path.exists(path):
                continue
            try:
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
            except (OSError, UnicodeDecodeError) as exc:
                # A README that cannot be read is a fact about the run,
                # not a reason to throw away the facts the template scan
                # already produced: an exception here used to end the
                # whole check as "could not be carried out" and the
                # findings collected before it were never printed.
                unreachable.append("%s: the README could not be read (%s)"
                                   % (name, exc))
                print("  ERROR %s: the README could not be read (%s)"
                      % (name, exc))
                continue
            for m in pattern.finditer(text):
                quoted = m.group(1)
                if quoted != pinned:
                    fail("%s quotes %s %s but the template pins %s"
                         % (name, pkg, quoted, pinned))
                else:
                    ok("%s quotes %s %s, matching the template" % (name, pkg, quoted))


def npm_published(pkg, version, timeout=20):
    """(published, detail) for one exact version on the npm registry.

    published is True when the registry has that version, False when it
    does not, and None when the registry could not be asked at all. The
    three-way answer is deliberate: "not there" and "could not look" are
    different facts, and only the first is a defect in the tree.
    """
    if budget_spent():
        return None, "the network budget was spent"
    url = "https://registry.npmjs.org/%s/%s" % (
        urllib.parse.quote(pkg, safe=""),
        urllib.parse.quote(version, safe=""))
    req = urllib.request.Request(
        url, headers={"User-Agent": "lumenveil-cdn-versions"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False, "HTTP 404"
        return None, "HTTP %s" % exc.code
    except Exception as exc:  # network, DNS, malformed JSON
        return None, str(exc)
    return data.get("version") == version, None


def npm_latest(pkg, timeout=20):
    """(version, kind, detail) for the latest release of a package.

    kind is None when the registry answered, "not-published" when it
    answered 404 (the package has no npm release to compare against) and
    "unreachable" when it could not be asked at all -- DNS, a timeout, a
    5xx, a malformed body. The last one is not a fact about the package: it
    is the absence of one, and the two must not be reported alike.
    """
    if budget_spent():
        return None, "unreachable", "the network budget was spent"
    url = "https://registry.npmjs.org/%s/latest" % (
        urllib.parse.quote(pkg, safe=""))
    req = urllib.request.Request(
        url, headers={"User-Agent": "lumenveil-cdn-versions"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None, "not-published", "HTTP 404"
        return None, "unreachable", "HTTP %s" % exc.code
    except Exception as exc:  # network, DNS, malformed JSON
        return None, "unreachable", str(exc)
    version = data.get("version")
    if not version:
        return None, "unreachable", "the registry returned no version"
    return version, None, None


def check_upstream(pins):
    print()
    print("[3] upstream drift (npm registry)")
    for pkg in sorted(pins):
        if len(pins[pkg]) != 1:
            continue
        pinned = list(pins[pkg])[0]
        latest, kind, detail = npm_latest(pkg)
        if kind == "unreachable":
            # The registry could not be asked. That says nothing about the
            # pins, so it must not be reported as agreement either: the
            # check could not be carried out, and the run has to say so.
            unreachable.append(
                "%s: the npm registry could not be reached (%s)"
                % (pkg, detail))
            print("  ERROR %s: the npm registry could not be reached (%s)"
                  % (pkg, detail))
            continue
        if kind == "not-published":
            # A package that is not on npm cannot be compared. That is not a
            # failure of this script, and it must not fail the schedule run
            # for a library we simply cannot track.
            ok("%s: no npm release to compare against (%s)" % (pkg, detail))
            continue

        # The pin has to name a version that EXISTS. Comparing it against
        # the latest release cannot tell "one release behind" apart from
        # "a version that was never published", and a version that was
        # never published has no file behind it on the CDN.
        published, detail = npm_published(pkg, pinned)
        if published is None:
            unreachable.append(
                "%s: the npm registry could not be reached (%s)"
                % (pkg, detail))
            print("  ERROR %s: the npm registry could not be reached (%s)"
                  % (pkg, detail))
            continue
        if not published:
            fail("%s is pinned at %s but that version was never published "
                 "to npm, so the CDN has no file behind it"
                 % (pkg, pinned))
            continue
        pinned_key = version_tuple(pinned)
        if pinned_key is None:
            # The offline check already reported a pin that names no
            # version. There is nothing to compare here, and the
            # version npm published exists, so this is not a drift.
            continue
        latest_key = version_tuple(latest)
        if latest_key is None:
            unreachable.append(
                "%s: npm published a version this check cannot read (%s)"
                % (pkg, latest))
            print("  ERROR %s: npm published a version this check cannot "
                  "read (%s)" % (pkg, latest))
            continue
        if latest_key > pinned_key:
            fail("%s is pinned at %s but npm publishes %s" % (pkg, pinned, latest))
        else:
            ok("%s is pinned at %s, npm latest is %s" % (pkg, pinned, latest))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--latest", action="store_true",
                    help="also compare the pins against the npm registry")
    args = ap.parse_args()

    print("=" * 78)
    print("CDN VERSION CHECK   repo: %s" % REPO)
    print("=" * 78)

    try:
        pins = collect_pins()
        check_consistency(pins)
        check_readme(pins)
        if args.latest:
            start_network_budget()
            check_upstream(pins)
            check_urls(collect_urls())
    except Exception as exc:  # noqa: BLE001 -- the point is to report, not crash
        # Whatever was found before the crash stays found. A crash
        # after a finding must not swallow it: the finding is a fact
        # about the tree, and it does not depend on the rest of the
        # check having run. The crash is a DIFFERENT thing -- the
        # check could not be carried out -- so it is recorded as that,
        # and printed with the "!" marker, never as a finding.
        print("  ERROR the check could not be carried out: %s" % exc)
        unreachable.append("the check could not be carried out: %s" % exc)

    print()
    print("=" * 78)
    if fails:
        print("FAILED  %d problem(s)." % len(fails))
        for f in fails:
            print("  - %s" % f)
        for u in unreachable:
            # A different marker from the failures above, on purpose. An
            # unreachable entry is the ABSENCE of a finding, and anything
            # that reads this output to decide what went wrong has to be
            # able to tell the two apart. The fault harness looks for the
            # "  - " marker, and must not read "could not reach the
            # registry" as if the checker had reported the version the
            # case planted.
            print("  ! %s" % u)
        return 1
    if unreachable:
        # Nothing failed, but part of the check could not be carried out.
        # Exit 2, not 0: a run that never reached the registry has not
        # verified anything, and reporting it as a pass would let a
        # tracking issue be closed on the strength of an outage.
        print("INCOMPLETE  %d check(s) could not be carried out."
              % len(unreachable))
        for u in unreachable:
            # The same marker as in the FAILED branch above: these are
            # not findings either.
            print("  ! %s" % u)
        return 2
    if args.latest:
        print("PASSED  every CDN pin agrees with itself, with the README "
              "and with upstream.")
    else:
        # Say only what was actually checked. The offline half never
        # asked npm or the CDNs anything, so a summary that claims the
        # pins agree "with upstream" asserts a comparison that did not
        # happen.
        print("PASSED  every CDN pin agrees with itself and with the "
              "README (the upstream half needs --latest).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
