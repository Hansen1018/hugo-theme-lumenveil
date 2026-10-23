#!/usr/bin/env python3
"""Fault injection for scripts/test-cdn-versions.py.

A check that never fails is a comment. This copies the tree the checker reads,
breaks it in each way the checker is supposed to catch, and asserts the
checker actually catches it -- and that it stays quiet on an intact tree.

Every case asserts on the EXIT CODE, not on the wording of the output: a
message that changes phrasing must not turn a caught fault into a pass.

The versions are READ OUT of the tree rather than hardcoded. A test that
asserts on "11.12.0" stops working the moment the pin moves, and would then
fail for the wrong reason -- a test that has to be edited in step with the
thing it tests is a second place to forget.

The offline cases are hermetic. The one case that needs the npm registry is
skipped, not failed, when the registry cannot be reached: an unreachable
registry says nothing about the checker, and a test that turns a network
outage into a red build is the same mistake the checker itself avoids by
keeping --latest out of pull-request CI.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
WORK = os.path.join("/tmp", "cdn-faults")

# The checker reads layouts/ and the READMEs, and resolves the repository
# root from its own location -- so the copy has to reproduce that shape.
# A directory named themes is skipped: exampleSite/themes/ is a symlink back
# to the repo root, and copying it would recurse into itself.
COPY = ["layouts", "README.md", "README.zh.md"]
SKIP = shutil.ignore_patterns("themes", "public", "resources", "__pycache__")

HEAD = os.path.join(WORK, "layouts", "_partials", "head.html")

# The two pin shapes this test mutates. The stylesheet comes from jsDelivr
# and the script from cdnjs, so the stylesheet alone is the half-bump case:
# a tree where the two disagree is exactly the bug the checker is for.
STYLE_PIN = re.compile(r"(highlight\.js@)(\d+\.\d+\.\d+)(/styles)")
KATEX_PIN = re.compile(r"(katex@)(\d+\.\d+\.\d+)(/dist)")
KATEX_PROSE = re.compile(r"(KaTeX )(\d+\.\d+\.\d+)")


def reset():
    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(os.path.join(WORK, "scripts"))
    shutil.copy2(os.path.join(HERE, "test-cdn-versions.py"),
                 os.path.join(WORK, "scripts", "test-cdn-versions.py"))
    for name in COPY:
        src = os.path.join(REPO, name)
        dst = os.path.join(WORK, name)
        if os.path.isdir(src):
            shutil.copytree(src, dst, symlinks=True, ignore=SKIP)
        else:
            shutil.copy2(src, dst)


def run(args=()):
    proc = subprocess.run(
        [sys.executable, os.path.join(WORK, "scripts", "test-cdn-versions.py")]
        + list(args),
        capture_output=True, text=True, timeout=180, cwd=WORK)
    return proc.returncode, proc.stdout + proc.stderr


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def sub(path, pattern, repl, count=0):
    text = read(path)
    new, n = pattern.subn(repl, text, count=count)
    if n == 0:
        raise SystemExit("FATAL: %r not found in %s" % (pattern.pattern, path))
    write(path, new)
    return n


def current_katex():
    m = KATEX_PIN.search(read(HEAD))
    if not m:
        raise SystemExit("FATAL: no katex pin found in the template")
    return m.group(2)


def registry_reachable():
    try:
        req = urllib.request.Request(
            "https://registry.npmjs.org/katex/latest",
            headers={"User-Agent": "lumenveil-cdn-faults"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8")).get("version") is not None
    except Exception:
        return False


def report(name, code, expect):
    ok = (code == expect)
    print("  [%s] %-46s exit=%d (expected %d)"
          % ("PASS" if ok else "FAIL", name, code, expect))
    return ok


def main():
    results = []
    print("fault injection for scripts/test-cdn-versions.py")
    print()

    # Baseline: an intact tree must pass, or the rest proves nothing.
    reset()
    code, out = run()
    results.append(report("intact tree passes", code, 0))
    if code != 0:
        print(out[-1500:])

    # Fault 1: a half-finished bump -- the jsDelivr stylesheet moved, the
    # cdnjs script did not. This is the failure the checker exists for.
    reset()
    sub(HEAD, STYLE_PIN, lambda m: m.group(1) + bump(m.group(2)) + m.group(3), count=1)
    code, out = run()
    results.append(report("half-finished bump (jsdelivr only)", code, 1))
    if code != 1:
        print(out[-1500:])

    # Fault 2: the English README left on the old version.
    reset()
    old = current_katex()
    sub(os.path.join(WORK, "README.md"), KATEX_PROSE,
        lambda m: m.group(1) + bump(m.group(2)), count=1)
    code, out = run()
    results.append(report("README quotes a different version", code, 1))
    if code != 1:
        print(out[-1500:])

    # Fault 3: the Chinese README left on the old version.
    reset()
    sub(os.path.join(WORK, "README.zh.md"), KATEX_PROSE,
        lambda m: m.group(1) + bump(m.group(2)), count=1)
    code, out = run()
    results.append(report("README.zh.md quotes a different version", code, 1))
    if code != 1:
        print(out[-1500:])

    # Fault 4: a pin genuinely behind upstream, which only --latest can see.
    # The whole tree moves together, so this is CONSISTENT but STALE: the
    # offline check must not notice it, and --latest must.
    reset()
    old = current_katex()
    stale = "%d.%d.0" % (int(old.split(".")[0]), int(old.split(".")[1]) - 1)
    sub(HEAD, KATEX_PIN, lambda m: m.group(1) + stale + m.group(3))
    sub(os.path.join(WORK, "README.md"), KATEX_PROSE,
        lambda m: m.group(1) + stale)
    sub(os.path.join(WORK, "README.zh.md"), KATEX_PROSE,
        lambda m: m.group(1) + stale)
    if registry_reachable():
        code, out = run(["--latest"])
        results.append(report("stale pin fails --latest", code, 1))
        if code != 1:
            print(out[-1500:])
    else:
        print("  [SKIP] %-46s npm registry unreachable" % "stale pin fails --latest")

    # Fault 5: the same stale tree must NOT fail the OFFLINE check. The
    # offline check does not look at upstream -- if it did, every pull
    # request would go red the day a release lands, which is why the two
    # modes are separate in the first place.
    code, out = run()
    results.append(report("stale but consistent tree passes offline mode",
                          code, 0))
    if code != 0:
        print(out[-1500:])

    # Fault 6: no pins at all must be a FAILURE. A check that finds nothing
    # to check has checked nothing, and would pass forever on a tree where
    # the templates had been refactored past the URLs.
    reset()
    shutil.rmtree(os.path.join(WORK, "layouts"))
    os.makedirs(os.path.join(WORK, "layouts"))
    code, out = run()
    results.append(report("no pins at all -> treated as a failure", code, 1))
    if code != 1:
        print(out[-1500:])

    shutil.rmtree(WORK, ignore_errors=True)

    print()
    print("  %d/%d cases behaved as specified" % (sum(results), len(results)))
    return 0 if all(results) else 1


def bump(version):
    """A different version, derived from the one in the tree."""
    major, minor, patch = (int(p) for p in version.split("."))
    return "%d.%d.%d" % (major, minor, patch + 1)


if __name__ == "__main__":
    sys.exit(main())
