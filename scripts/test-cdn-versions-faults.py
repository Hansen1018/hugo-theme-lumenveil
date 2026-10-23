#!/usr/bin/env python3
"""Fault injection for scripts/test-cdn-versions.py.

A check that never fails is a comment. This copies the tree the checker reads,
breaks it in each way the checker is supposed to catch, and asserts the
checker actually catches it -- and that it stays quiet on an intact tree.

Every case asserts on the EXIT CODE, not on the wording of the output: a
message that changes phrasing must not turn a caught fault into a pass. The
two cases that plant a specific version also assert that the failure NAMES
that version, because the exit code alone cannot: a tree that is already
behind upstream fails for a reason the case did not plant, and the case would
then pass for the wrong reason.

Exit codes of this harness:
    0  every case behaved as specified
    1  a case did not behave as specified
    3  the harness could not build the case at all -- a template shape it
       does not recognise. Distinct from 1 on purpose: a checker that
       behaved correctly and a harness that never got to ask it are
       different problems, and they must not read the same in CI.

The versions are READ OUT of the tree rather than hardcoded. A test that
asserts on "11.12.0" stops working the moment the pin moves, and would then
fail for the wrong reason -- a test that has to be edited in step with the
thing it tests is a second place to forget.

The offline cases are hermetic. The cases that need the npm registry are
skipped, not failed, when the registry cannot be reached: an unreachable
registry says nothing about the checker, and a test that turns a network
outage into a red build is the same mistake the checker itself avoids by
keeping --latest out of pull-request CI. A skip is still reported -- counted
in the summary and announced as a warning -- so that a green run never hides
the fact that the network half of the checker was not exercised.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
WORK = os.path.join("/tmp", "cdn-faults")

# The harness could not build the case it was asked to build. Its own code,
# so that CI can tell it apart from a case that behaved wrongly.
FATAL_HARNESS = 3

# The checker reads layouts/ and the READMEs, and resolves the repository
# root from its own location -- so the copy has to reproduce that shape.
# A directory named themes is skipped: exampleSite/themes/ is a symlink back
# to the repo root, and copying it would recurse into itself.
COPY = ["layouts", "README.md", "README.zh.md"]
SKIP = shutil.ignore_patterns("themes", "public", "resources", "__pycache__")

CHECKER = os.path.join(WORK, "scripts", "test-cdn-versions.py")

# The two pin shapes this test mutates. The stylesheet comes from jsDelivr
# and the script from cdnjs, so the stylesheet alone is the half-bump case:
# a tree where the two disagree is exactly the bug the checker is for.
STYLE_PIN = re.compile(r"(highlight\.js@)(\d+\.\d+\.\d+)(/styles)")
KATEX_PIN = re.compile(r"(katex@)(\d+\.\d+\.\d+)(/dist)")
KATEX_PROSE = re.compile(r"(KaTeX )(\d+\.\d+\.\d+)")
# The KaTeX stylesheet URL. Used by the case that plants a path that
# does not exist inside a real, published release.
KATEX_CSS = re.compile(r"(katex@[\d.]+/dist/)katex\.min\.css")

# The registry the checker talks to. Rewritten inside the COPY of the
# checker to simulate an outage, so the simulation needs no hook in the
# checker itself.
REGISTRY = "https://registry.npmjs.org"


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
        print("FATAL: %r not found in %s" % (pattern.pattern, path),
              file=sys.stderr)
        sys.exit(FATAL_HARNESS)
    write(path, new)
    return n


def layout_files():
    """(path, text) for every readable file under the copied layouts/."""
    for root, dirs, files in os.walk(os.path.join(WORK, "layouts")):
        dirs[:] = [d for d in dirs if d != "exampleSite"]
        for name in sorted(files):
            path = os.path.join(root, name)
            try:
                yield path, read(path)
            except (OSError, UnicodeDecodeError):
                continue


def find_pin_file(pattern):
    """The file under layouts/ that carries a given pin.

    Found by looking for it rather than hardcoded: the template that holds
    the pins can move, and a harness that assumes a path breaks the day it
    does. When the pin is nowhere to be found this exits FATAL_HARNESS,
    which is a different exit code from a failed case -- a harness that
    cannot build its case must not look like a case that misbehaved.
    """
    for path, text in layout_files():
        if pattern.search(text):
            return path
    print("FATAL: no file under layouts/ carries a %r pin" % pattern.pattern,
          file=sys.stderr)
    sys.exit(FATAL_HARNESS)


def current_katex():
    """The katex version the templates pin, wherever that pin lives."""
    for path, text in layout_files():
        m = KATEX_PIN.search(text)
        if m:
            return m.group(2)
    print("FATAL: no katex pin found in the templates", file=sys.stderr)
    sys.exit(FATAL_HARNESS)


def cdn_reachable():
    """Can the CDN be asked for a file at all?

    The npm registry and the CDNs are separate hosts: one can be
    reachable while the other is not, and the URL check needs a probe
    of its own rather than borrowing the registry answer.
    """
    url = ("https://cdn.jsdelivr.net/npm/katex@%s/dist/katex.min.css"
           % current_katex())
    try:
        req = urllib.request.Request(
            url, method="HEAD",
            headers={"User-Agent": "lumenveil-cdn-faults"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status == 200
    except Exception:  # network, DNS, timeout
        return False


def registry_reachable():
    try:
        req = urllib.request.Request(
            REGISTRY + "/katex/latest",
            headers={"User-Agent": "lumenveil-cdn-faults"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8")).get("version") is not None
    except Exception:
        return False


def published_below(pkg, current):
    """The greatest version npm has published that is below `current`.

    Read from the registry rather than computed from the version string:
    arithmetic on the string produces versions that were never published
    (katex has no 0.15.11), and a stale pin that does not exist upstream
    would be caught for the wrong reason -- as a typo, not as drift.
    """
    url = REGISTRY + "/" + urllib.parse.quote(pkg, safe="")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "lumenveil-cdn-faults",
                 "Accept": "application/vnd.npm.install-v1+json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    limit = version_key(current)
    best = None
    for ver in data.get("versions", {}):
        if "-" in ver:
            # A prerelease is not what "behind upstream" means.
            continue
        key = version_key(ver)
        if key < limit and (best is None or key > best[0]):
            best = (key, ver)
    return best[1] if best else None


def version_key(version):
    """(major, minor, patch) for a version string, prerelease parts dropped."""
    core = version.split("+")[0].split("-")[0]
    parts = []
    for part in core.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def failures(out):
    """The failure bullets the checker printed, and nothing else.

    Only the bullets: the version numbers of an intact tree also appear in
    its "ok" lines, so scanning the whole output would match a version the
    case planted without the checker having caught anything.
    """
    lines = out.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("FAILED"):
            return [l for l in lines[i + 1:] if l.startswith("  - ")]
    return []


def report(name, code, expect):
    ok = (code == expect)
    print("  [%s] %-46s exit=%d (expected %d)"
          % ("PASS" if ok else "FAIL", name, code, expect))
    return ok


def report_names(name, out, version):
    """Did the checker report this version as a failure?

    The exit code alone cannot say that: a tree that is already behind
    upstream fails for a reason the case did not plant, and the case would
    pass for the wrong reason. The version is what the case planted, so
    the failure has to name it.
    """
    hits = [line for line in failures(out) if version in line]
    ok = bool(hits)
    print("  [%s] %-46s %s"
          % ("PASS" if ok else "FAIL", name,
             "named %s" % version if ok else "did not name %s" % version))
    return ok


def main():
    results = []
    skipped = []
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
    sub(find_pin_file(STYLE_PIN), STYLE_PIN,
        lambda m: m.group(1) + bump(m.group(2)) + m.group(3), count=1)
    code, out = run()
    results.append(report("half-finished bump (jsdelivr only)", code, 1))
    if code != 1:
        print(out[-1500:])

    # Fault 2: the English README left on the old version.
    reset()
    # current_katex() is a precondition here, not a value: it fails loudly
    # if the template has stopped carrying a katex pin, which would
    # otherwise make this case pass for the wrong reason.
    current_katex()
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
    pinned = current_katex()
    # The stale version has to be one that really exists upstream: a pin
    # that was never published is caught as a typo, not as drift.
    stale = older_than(pinned)
    reachable = registry_reachable()
    if reachable:
        published = published_below("katex", pinned)
        if published:
            stale = published
    sub(find_pin_file(KATEX_PIN), KATEX_PIN,
        lambda m: m.group(1) + stale + m.group(3))
    sub(os.path.join(WORK, "README.md"), KATEX_PROSE,
        lambda m: m.group(1) + stale)
    sub(os.path.join(WORK, "README.zh.md"), KATEX_PROSE,
        lambda m: m.group(1) + stale)
    if reachable:
        code, out = run(["--latest"])
        results.append(report("stale pin fails --latest", code, 1))
        results.append(report_names("the failure names the stale pin",
                                     out, stale))
        if code != 1:
            print(out[-1500:])
    else:
        skipped.append("stale pin fails --latest")
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

    # Fault 6: a pin that names a version nobody ever published. The
    # comparison against the latest release cannot see it -- a pin ABOVE
    # the latest release looks "not behind" -- but the CDN has no file
    # behind it either, so the page loads a 404 and the maths silently
    # never renders. The offline check must stay quiet: the tree is
    # internally consistent, it is the pin that points at nothing.
    reset()
    ghost = never_published(current_katex())
    sub(find_pin_file(KATEX_PIN), KATEX_PIN,
        lambda m: m.group(1) + ghost + m.group(3))
    sub(os.path.join(WORK, "README.md"), KATEX_PROSE,
        lambda m: m.group(1) + ghost)
    sub(os.path.join(WORK, "README.zh.md"), KATEX_PROSE,
        lambda m: m.group(1) + ghost)
    code, out = run()
    results.append(report("a pin nobody published passes the offline check",
                          code, 0))
    if code != 0:
        print(out[-1500:])
    if reachable:
        code, out = run(["--latest"])
        results.append(report("a pin nobody published fails --latest", code, 1))
        results.append(report_names("the failure names the unpublished pin",
                                     out, ghost))
        if code != 1:
            print(out[-1500:])
    else:
        skipped.append("a pin nobody published fails --latest")
        print("  [SKIP] %-46s npm registry unreachable"
              % "a pin nobody published fails --latest")

    # Fault 7: the npm registry cannot be reached. That is not the same as
    # "the pins are current": the check could not be carried out, and it
    # has to say so. A run that reports success here would let the
    # scheduled workflow close the tracking issue on the strength of an
    # outage.
    reset()
    text = read(CHECKER)
    write(CHECKER, text.replace(REGISTRY, "http://127.0.0.1:9"))
    code, out = run()
    results.append(report("an unreachable registry leaves the tree alone",
                          code, 0))
    if code != 0:
        print(out[-1500:])
    code, out = run(["--latest"])
    results.append(report("an unreachable registry exits 2", code, 2))
    if code != 2:
        print(out[-1500:])

    # Fault 8: a pinned URL the CDN does not serve. The version can be
    # perfectly published and perfectly current, and the FILE can still
    # be missing: a path that does not exist inside a real release. Every
    # version check passes, and the page loads a 404 for the maths and
    # renders without it, silently. Only asking the CDN for the file can
    # see this, which is why the URL check exists.
    reset()
    sub(find_pin_file(KATEX_CSS), KATEX_CSS,
        lambda m: m.group(1) + "katex.nonexistent.css")
    code, out = run()
    results.append(report("a missing CDN file passes the offline check",
                          code, 0))
    if code != 0:
        print(out[-1500:])
    if reachable and cdn_reachable():
        code, out = run(["--latest"])
        results.append(report("a missing CDN file fails --latest", code, 1))
        # The exit code alone cannot say WHY: a tree that is already
        # behind upstream fails for a reason this case did not plant.
        # The failure has to name the missing file.
        results.append(report_names("the failure names the missing file",
                                     out, "katex.nonexistent.css"))
        if code != 1:
            print(out[-1500:])
    else:
        skipped.append("a missing CDN file fails --latest")
        print("  [SKIP] %-46s the CDN could not be reached"
              % "a missing CDN file fails --latest")

    # Fault 9: no pins at all must be a FAILURE. A check that finds nothing
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
    if skipped:
        print("  %d of %d cases ran; %d skipped: %s"
              % (len(results), len(results) + len(skipped), len(skipped),
                 ", ".join(skipped)))
        # The skipped cases are the only ones that exercise the --latest
        # half of the checker, so a green run that never asked it is not a
        # green run. Say so out loud rather than letting it pass as a full
        # pass.
        print("::warning::the registry-dependent cases were skipped, so the "
              "--latest half of the checker was not exercised")
    else:
        print("  %d/%d cases behaved as specified"
              % (sum(results), len(results)))
    return 0 if all(results) else 1


def bump(version):
    """A different version, derived from the one in the tree."""
    major, minor, patch = (int(p) for p in version.split("."))
    return "%d.%d.%d" % (major, minor, patch + 1)


def older_than(version):
    """A version below the one in the tree, without going negative.

    Arithmetic only: it is the fallback for the case where the registry
    cannot be reached and the published list cannot be asked for a real
    older version. It is used only for the offline case, where the version
    does not have to exist upstream.
    """
    major, minor, patch = (int(p) for p in version.split("."))
    if minor > 0:
        return "%d.%d.%d" % (major, minor - 1, patch)
    if major > 0:
        return "%d.%d.%d" % (major - 1, 0, patch)
    return "0.0.%d" % max(patch - 1, 0)


def never_published(version):
    """A version of the same package that was never published.

    Built from the version in the tree, with the minor component far above
    any real release of the package, so the case cannot accidentally name
    something npm happens to publish.
    """
    major = int(version.split(".")[0])
    return "%d.%d.0" % (major, 999)


if __name__ == "__main__":
    sys.exit(main())
