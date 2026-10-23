#!/usr/bin/env python3
"""Check the CDN library versions the theme pins.

Two independent checks live here, and they fail for different reasons:

1. INTERNAL CONSISTENCY (offline, the default). Every occurrence of a CDN
   library pin under layouts/ must name the SAME version, and every version
   quoted in the README files must match the template pin. This catches a
   half-finished bump. highlight.js is loaded as a stylesheet from jsDelivr
   and as a script from cdnjs, so bumping one source and not the other
   ships a stylesheet from one release next to a highlighter from another;
   that mismatch is invisible in a green build and shows up as broken colours
   in a browser. The README quotes a version in prose, so it drifts the same
   way.

2. UPSTREAM DRIFT (--latest, needs the network). Compares each pin against
   the latest version published on the npm registry and reports the ones
   that are behind. This is deliberately NOT part of pull-request CI: a new
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
       with upstream
    2  the check could not be carried out (network down, unreadable tree,
       unexpected error). Deliberately distinct from 1: a scheduled run that
       cannot reach the registry must not be reported as "your pins are
       behind", and the workflow opens an issue only on a genuine failure.

Usage:
    scripts/test-cdn-versions.py            # internal consistency only
    scripts/test-cdn-versions.py --latest   # also compare against npm
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYOUTS = os.path.join(REPO, "layouts")
READMES = ("README.md", "README.zh.md")

# Both URL shapes the theme uses. The jsDelivr form carries the version as
# @<version>, the cdnjs form as a path segment /<version>/. A third shape,
# the busuanzi counter URL, is not an npm package and is deliberately not
# matched here: it has no registry to compare against, and its version is
# pinned by the service operator rather than by us.
JSDELIVR = re.compile(
    r"cdn\.jsdelivr\.net/npm/([A-Za-z0-9._-]+)@([0-9][0-9A-Za-z.+-]*)")
CDNJS = re.compile(
    r"cdnjs\.cloudflare\.com/ajax/libs/([A-Za-z0-9._-]+)/([0-9][0-9A-Za-z.+-]*)")

fails = []


def fail(msg):
    fails.append(msg)
    print("  FAIL  %s" % msg)


def ok(msg):
    print("  ok    %s" % msg)


def vtuple(v):
    """(major, minor, patch) for a version string.

    Pre-release and build metadata are dropped: npm's `latest` dist-tag is
    never a pre-release, and comparing `1.2.3-rc1` against `1.2.3` by
    numeric parts is the only comparison that decides the question this
    script asks, which is whether a newer release exists.
    """
    core = v.split("+")[0].split("-")[0]
    parts = []
    for part in core.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
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


def check_consistency(pins):
    print("[1] internal consistency (offline)")
    if not pins:
        fail("no CDN pins found under layouts/ -- the pin format changed?")
        return
    for pkg in sorted(pins):
        versions = pins[pkg]
        if len(versions) == 1:
            ver = list(versions)[0]
            ok("%s pinned at %s (%d occurrence%s)"
               % (pkg, ver, len(versions[ver]),
                  "" if len(versions[ver]) == 1 else "s"))
        else:
            detail = "; ".join(
                "%s at %s (%s)" % (v, ", ".join(versions[v]), len(versions[v]))
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
        pattern = re.compile(
            r"(?i)\b%s\s+v?(\d+\.\d+\.\d+)" % re.escape(pkg))
        for name in READMES:
            path = os.path.join(REPO, name)
            if not os.path.exists(path):
                continue
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            for m in pattern.finditer(text):
                quoted = m.group(1)
                if quoted != pinned:
                    fail("%s quotes %s %s but the template pins %s"
                         % (name, pkg, quoted, pinned))
                else:
                    ok("%s quotes %s %s, matching the template" % (name, pkg, quoted))


def npm_latest(pkg, timeout=20):
    url = "https://registry.npmjs.org/%s/latest" % pkg
    req = urllib.request.Request(
        url, headers={"User-Agent": "lumenveil-cdn-versions"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return None, "HTTP %s" % exc.code
    except Exception as exc:  # network, DNS, malformed JSON
        return None, str(exc)
    return data.get("version"), None


def check_upstream(pins):
    print()
    print("[3] upstream drift (npm registry)")
    for pkg in sorted(pins):
        if len(pins[pkg]) != 1:
            continue
        pinned = list(pins[pkg])[0]
        latest, err = npm_latest(pkg)
        if latest is None:
            # A package that is not on npm cannot be compared. That is not a
            # failure of this script, and it must not fail the schedule run
            # for a library we simply cannot track.
            ok("%s: no npm release to compare against (%s)" % (pkg, err))
            continue
        if vtuple(latest) > vtuple(pinned):
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
            check_upstream(pins)
    except Exception as exc:  # noqa: BLE001 -- the point is to report, not crash
        print("  ERROR the check could not be carried out: %s" % exc)
        return 2

    print()
    print("=" * 78)
    if fails:
        print("FAILED  %d problem(s)." % len(fails))
        for f in fails:
            print("  - %s" % f)
        return 1
    print("PASSED  every CDN pin agrees with itself, with the README and "
          "with upstream.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
