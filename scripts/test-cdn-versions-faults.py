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
import atexit
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
# A unique directory per run. A fixed path under /tmp collides between
# concurrent runs on the same machine -- and reset() deletes this path
# wholesale, so two runs would delete each other's tree.
WORK = tempfile.mkdtemp(prefix="cdn-faults-")
# Removed on exit however the harness ends, so a case that dies early
# does not leave a tree behind.
atexit.register(shutil.rmtree, WORK, True)

# The harness could not build the case it was asked to build. Its own code,
# so that CI can tell it apart from a case that behaved wrongly.
FATAL_HARNESS = 3


class BudgetSpent(Exception):
    """The harness ran out of its network budget mid-question.

    Its own exception, because "I ran out of time to ask" and "I asked
    and the answer was no" are different facts: the first is a skip,
    the second is a verdict. Reporting one as the other tells the
    reader that a question was answered when it was never asked.
    """

# Every check this harness runs, by name.
#
# This is the harness's own account of what it owes the reader. At the
# end of the run each name has to be accounted for exactly once: either
# as a verdict or as a skip. A name that is neither was a check that
# silently stopped running, and a name that is both means one branch
# of a case counted the same check twice. Either way the reader would
# see a number that does not add up, with nothing to say which check
# went missing -- so the accounting is checked rather than assumed.
CHECKS = (
    "intact tree passes",
    "half-finished bump (jsdelivr only)",
    "README quotes a different version",
    "README.zh.md quotes a different version",
    "stale pin fails --latest",
    "the failure names the stale pin",
    "stale but consistent tree passes offline mode",
    "a pin nobody published passes the offline check",
    "a pin nobody published fails --latest",
    "the failure names the unpublished pin",
    "the failure says the version was never published",
    "an unreachable registry leaves the tree alone",
    "an unreachable registry exits 2",
    "a missing CDN file passes the offline check",
    "a missing CDN file fails --latest",
    "the failure names the missing file",
    "a wedged checker is reported as a timeout",
    "no pins at all -> treated as a failure",
    "a pin that is not a version is reported",
    "the failure names the malformed pin",
)

# The names of the checks that produced a verdict. The skips live in
# main(), next to the case that skipped them.
ACCOUNTED = []

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
# The version part of every pattern below accepts what the CHECKER
# accepts -- a prerelease or build suffix included -- so that a pin
# shape the checker reads fine cannot abort the whole harness with a
# fatal error that takes every later case down with it.
VERSION = r"[0-9][0-9A-Za-z.+-]*"
# The same rule as the checker's VERSION constant, in
# scripts/test-cdn-versions.py -- spelled out in both places because
# this harness runs against a COPY of the tree and cannot import the
# file it is testing. A pattern that stopped one character earlier
# would compare a different string than the one the template pins, and
# the difference shows up as a mismatch that is not there.
STYLE_PIN = re.compile(r"(highlight\.js@)(" + VERSION + r")(/styles)")
KATEX_PIN = re.compile(r"(katex@)(" + VERSION + r")(/dist)")
KATEX_PROSE = re.compile(r"(KaTeX )(" + VERSION + r")")
# The KaTeX stylesheet URL. Used by the case that plants a path that
# does not exist inside a real, published release.
KATEX_CSS = re.compile(r"(katex@" + VERSION + r"/dist/)katex\.min\.css")

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


# The exit code a run reports when the checker did not finish. 124 is
# the conventional shell code for a timeout, and it is deliberately a
# code nothing else here uses: this harness's own codes are 0, 1 and 3
# (every case behaved, a case did not behave, the harness could not do
# its own job) and the checker's are 0, 1 and 2. A wedged checker must
# not be reported as any of those.
TIMEOUT = 124


# The harness's own wall-clock budget for network work.
#
# The checker's NETWORK_BUDGET bounds the CHECKER's requests, not the
# probes below: those are this script's, and they are paid for once per
# case. A registry that accepts the connection and then stalls would
# otherwise be paid for again and again, and the step in CI would be
# killed by its own timeout -- turning a slow network into a red build,
# which is the one outcome the skip rules exist to prevent.
#
# It is read from the environment so that the number the CI step allows
# and the number the step's own timeout allows are set in the same
# place and cannot drift apart silently.
#
# The headroom the harness keeps inside the allowance it is given.
#
# The number in the environment is the time the CI step allows the
# harness to run -- the step's timeout-minutes reads it back out of the
# environment, so it is the same number by construction. The network
# work has to fit inside that, together with the cases that touch no
# network at all and the process start-up, so the harness spends less
# than the whole allowance. The headroom is a constant HERE, so the two
# numbers cannot drift apart: raising the allowance raises the network
# budget with it, and nothing else has to be edited.
BUDGET_HEADROOM_MINUTES = 5


def budget_seconds():
    """The harness's network budget, in seconds.

    The environment carries the allowance in MINUTES -- the same number
    the step's own timeout is derived from -- and the harness spends
    that minus the headroom above.

    A value that is not a number is a broken configuration, not a case
    that misbehaved, so it exits FATAL_HARNESS instead of dying with an
    uncaught ValueError whose exit code (1) is the one a failing case
    uses. An allowance that leaves nothing for the network would be the
    same mistake wearing a disguise: every network case would be
    skipped and the run would report green without having asked
    anything.
    """
    raw = os.environ.get("CDN_FAULTS_BUDGET_MINUTES", "12")
    try:
        value = float(raw)
    except ValueError:
        print("FATAL: CDN_FAULTS_BUDGET_MINUTES is not a number: %r" % raw,
              file=sys.stderr)
        sys.exit(FATAL_HARNESS)
    if value <= BUDGET_HEADROOM_MINUTES:
        print("FATAL: CDN_FAULTS_BUDGET_MINUTES must leave more than %d "
              "minutes for the network: %r"
              % (BUDGET_HEADROOM_MINUTES, raw), file=sys.stderr)
        sys.exit(FATAL_HARNESS)
    return (value - BUDGET_HEADROOM_MINUTES) * 60


BUDGET = budget_seconds()

_deadline = None
# Whether the npm registry has answered YES at least once. A probe that
# failed does not stick: a registry that blipped is asked again later,
# because a case that runs later deserves its own reading rather than
# an earlier probe's verdict. The one answer that does stick is the bad
# one -- a registry that answered and then failed, which is unusable
# for the rest of the run (see mark_registry_flaky).
_registry_ok = False
_registry_flaky = False


def start_budget():
    global _deadline
    _deadline = time.monotonic() + BUDGET


def budget_left():
    """Seconds of network work still allowed, or 0.0 when it is spent."""
    if _deadline is None:
        return BUDGET
    return max(0.0, _deadline - time.monotonic())


def budget_spent():
    return budget_left() <= 0.0


def probe_timeout(own):
    """The timeout for one probe: its own limit, or what is left of the budget.

    Zero means the budget is gone: a probe cannot be asked at all then,
    and a one-second probe would report a timeout instead of reporting
    that there was no time left to ask.
    """
    left = budget_left()
    if left <= 0:
        return 0
    return max(1, int(min(own, left)))


def run(args=(), timeout=180, network=False):
    """(exit code, output) for one run of the checker against the copy.

    A checker that hangs is reported as TIMEOUT rather than crashing the
    harness: subprocess.run raises TimeoutExpired, and an uncaught
    exception exits with 1 -- the same code this harness uses for "a case
    did not behave as specified", which would make a wedged checker
    indistinguishable from a case that caught a fault.

    A run that reaches the network and finds the budget spent is
    reported the same way, and the caller skips it: the network did not
    answer, which says nothing about the tree. The `network` flag says
    which runs those: the case that points the checker at a dead local
    port reaches no network at all -- it is refused instantly -- so it
    must not be refused by a budget it does not spend.
    """
    if network and budget_spent():
        return TIMEOUT, "the harness ran out of its network budget"
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(WORK, "scripts", "test-cdn-versions.py")]
            + list(args),
            capture_output=True, text=True, timeout=timeout, cwd=WORK)
    except subprocess.TimeoutExpired:
        return TIMEOUT, "the checker did not finish within %ds" % timeout
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
    timeout = probe_timeout(20)
    if timeout <= 0:
        return False
    url = ("https://cdn.jsdelivr.net/npm/katex@%s/dist/katex.min.css"
           % current_katex())
    try:
        req = urllib.request.Request(
            url, method="HEAD",
            headers={"User-Agent": "lumenveil-cdn-faults"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:  # network, DNS, timeout
        return False


def registry_reachable():
    """Can the npm registry be asked at all?

    A registry that answered is not asked again -- the probe is paid
    for once. A registry that did NOT answer is asked again later: it
    may come back, and a case that runs later deserves its own reading
    rather than an earlier case's verdict. The one answer that sticks
    is the bad one: a registry that answered and then failed is
    unusable for the rest of the run.
    """
    global _registry_ok
    if _registry_flaky:
        return False
    if _registry_ok:
        return True
    timeout = probe_timeout(20)
    if timeout <= 0:
        return False
    try:
        req = urllib.request.Request(
            REGISTRY + "/katex/latest",
            headers={"User-Agent": "lumenveil-cdn-faults"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            _registry_ok = (json.loads(resp.read().decode("utf-8"))
                             .get("version") is not None)
    except Exception:
        _registry_ok = False
    return bool(_registry_ok)


def mark_registry_flaky():
    """The registry answered and then failed: do not ask it again."""
    global _registry_ok, _registry_flaky
    _registry_flaky = True
    _registry_ok = False


def version_published(pkg, version):
    """(published, looked) for one exact version on the npm registry.

    published is True when npm has it, False when it does not, and None
    when the registry could not be asked. The three-way answer matters:
    "nobody published it" and "we could not look" are different facts,
    and only the first is a defect in the tree.
    """
    timeout = probe_timeout(30)
    if timeout <= 0:
        return None, False
    url = (REGISTRY + "/" + urllib.parse.quote(pkg, safe="")
           + "/" + urllib.parse.quote(version, safe=""))
    req = urllib.request.Request(
        url, headers={"User-Agent": "lumenveil-cdn-faults"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("version") == version, True
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False, True
        return None, True
    except Exception:  # network, DNS, timeout, malformed body
        return None, False


def published_below(pkg, current):
    """The greatest version npm has published that is below `current`.

    Read from the registry rather than computed from the version string:
    arithmetic on the string produces versions that were never published
    (katex has no 0.15.11), and a stale pin that does not exist upstream
    would be caught for the wrong reason -- as a typo, not as drift.
    """
    timeout = probe_timeout(30)
    if timeout <= 0:
        raise BudgetSpent()
    url = REGISTRY + "/" + urllib.parse.quote(pkg, safe="")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "lumenveil-cdn-faults",
                 "Accept": "application/vnd.npm.install-v1+json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    limit = version_core(current)
    best = None
    for ver in data.get("versions", {}):
        if "-" in ver:
            # A prerelease is not what "behind upstream" means.
            continue
        key = version_parts(ver)
        if key is None:
            # A published version this harness cannot parse cannot be
            # compared against, so it is not a candidate.
            continue
        if key < limit and (best is None or key > best[0]):
            best = (key, ver)
    return best[1] if best else None


def version_parts(version):
    """(major, minor, patch) for a version string, prerelease parts dropped.

    Returns None for a version that does not parse. ONE parser for
    the whole harness: two parsers that disagree about a malformed
    version are two places where the version a case planted and the
    comparison made against it can drift apart.

    The same rule is the one the checker parses versions by
    (version_tuple in scripts/test-cdn-versions.py): a part that is not
    a number is not a version, and a version with more than three parts
    is compared by its first three. A malformed version is therefore
    reported by the checker rather than guessed at by either of them.
    """
    core = version.split("+")[0].split("-")[0]
    parts = []
    for part in core.split("."):
        if not re.fullmatch(r"[0-9]+", part):
            return None
        parts.append(int(part))
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


def network_not_carried_out(names, code, skipped):
    """Did the checker fail to carry the case out at all?

    Two answers mean that, and neither is a verdict about the tree:

    - TIMEOUT: the checker did not finish. A timeout is an outage.
    - 2: the checker's own "could not be carried out" -- the registry
      or the CDN could not be reached, or the network budget ran out
      before the question could be asked. The checker says so itself,
      and a run that could not be carried out has found nothing wrong.

    The offline cases have no network in them at all, so neither of
    these can happen there: a timeout there means a wedged checker and
    stays a failure -- which is what the case that plants a wedged
    checker asserts, and why it expects TIMEOUT rather than 2.
    """
    if code not in (TIMEOUT, 2):
        return False
    for name in names:
        skipped.append(name)
    print("  [SKIP] %-46s the check could not be carried out (%d)"
          % (names[0], code))
    return True


def report(name, code, expect):
    ok = (code == expect)
    ACCOUNTED.append(name)
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
    ACCOUNTED.append(name)
    hits = [line for line in failures(out) if version in line]
    ok = bool(hits)
    print("  [%s] %-46s %s"
          % ("PASS" if ok else "FAIL", name,
             "named %s" % version if ok else "did not name %s" % version))
    return ok


def report_says(name, out, phrase):
    """Did the checker report this reason?

    Naming the version is not enough. A version the registry DOES
    publish can still make --latest fail, for a different reason
    entirely -- and then the case would pass for the wrong reason. So the
    reason has to be asserted as well as the version.
    """
    ACCOUNTED.append(name)
    hits = [line for line in failures(out) if phrase in line]
    ok = bool(hits)
    print("  [%s] %-46s %s"
          % ("PASS" if ok else "FAIL", name,
             "said %r" % phrase if ok else "did not say %r" % phrase))
    return ok


def main():
    results = []
    skipped = []
    # The network budget starts here, so it covers every probe and every
    # network run this harness makes.
    start_budget()
    # Whether the npm registry answered. Bound here so that a case
    # which reads it before Fault 4 sets it sees False instead of
    # raising UnboundLocalError -- whose exit code (1) is
    # indistinguishable from "a case misbehaved".
    reachable = False
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
    # The stale version has to be one that really exists upstream, and it
    # has to be the release the registry itself reports as the greatest
    # published one below the pin. An arithmetic guess names a version
    # nobody published (katex has no 0.15.11), and then --latest fails
    # with "never published" rather than with "behind the latest
    # release" -- the case would pass, for the wrong reason.
    reachable = registry_reachable()
    stale = None
    # Why the stale pin could not be planted. These are different facts,
    # and the skip below reports which one happened instead of a
    # generic "could not".
    stale_reason = "no published release below the pin to plant"
    if reachable:
        try:
            stale = published_below("katex", pinned)
        except BudgetSpent:
            # The budget ran out before the question could be asked.
            # Not the same as an answer of "no release below the pin",
            # so it is not reported as one.
            stale_reason = "the harness ran out of its network budget"
        except Exception as exc:  # noqa: BLE001 -- a registry that
            # answers and then times out is an outage, not a defect
            # in the tree. Treated as unreachable: the cases that
            # need the registry are skipped and reported, instead of
            # the harness dying with a traceback whose exit code (1)
            # is indistinguishable from "a case misbehaved".
            print("  the registry answered and then failed: %s" % exc)
            stale = None
            stale_reason = "the registry answered and then failed"
            # The registry is unreliable, not just slow about this one
            # package: the later cases ask it questions too, and a
            # half-answered registry would fail them for the wrong
            # reason. So it is marked unusable for the rest of the run.
            mark_registry_flaky()
    else:
        stale_reason = "the registry could not be reached"
    if not stale:
        # No real published release below the pin to plant. BOTH cases
        # that need it are skipped, the offline one included: its
        # subject is a tree that is consistent but STALE, and a version
        # nobody published is a typo, not a stale pin. The intact-tree
        # case above still covers the offline mode.
        # One entry per CHECK, so the total reported below never drifts:
        # three checks are skipped here, and listing two of them would
        # report fewer skips than there are checks.
        for name in ("stale pin fails --latest",
                     "the failure names the stale pin",
                     "stale but consistent tree passes offline mode"):
            skipped.append(name)
            print("  [SKIP] %-46s %s" % (name, stale_reason))
    else:
        sub(find_pin_file(KATEX_PIN), KATEX_PIN,
            lambda m: m.group(1) + stale + m.group(3))
        sub(os.path.join(WORK, "README.md"), KATEX_PROSE,
            lambda m: m.group(1) + stale)
        sub(os.path.join(WORK, "README.zh.md"), KATEX_PROSE,
            lambda m: m.group(1) + stale)
        code, out = run(["--latest"], network=True)
        if not network_not_carried_out(
                ["stale pin fails --latest",
                 "the failure names the stale pin"], code, skipped):
            results.append(report("stale pin fails --latest", code, 1))
            results.append(report_names("the failure names the stale pin",
                                         out, stale))
            if code != 1:
                print(out[-1500:])

        # Fault 5: the same stale tree must NOT fail the OFFLINE check.
        # The offline check does not look at upstream -- if it did, every
        # pull request would go red the day a release lands, which is why
        # the two modes are separate in the first place.
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
    # Its own reading of the registry, not the one Fault 4 took: the
    # registry may have come back in between.
    if registry_reachable():
        code, out = run(["--latest"], network=True)
        if not network_not_carried_out(
                ["a pin nobody published fails --latest",
                 "the failure names the unpublished pin",
                 "the failure says the version was never published"],
                code, skipped):
            results.append(report("a pin nobody published fails --latest", code, 1))
            results.append(report_names("the failure names the unpublished pin",
                                         out, ghost))
            # The version this case plants is ABOVE the pin, so the only
            # thing that can make --latest fail is the "never
            # published" branch. A registry that did publish it would
            # fail for some other reason instead -- and the case would
            # pass for the wrong reason. So the reason is asserted too.
            results.append(report_says(
                "the failure says the version was never published",
                out, "never published"))
            if code != 1:
                print(out[-1500:])
    else:
        # Three checks of this case are skipped: the exit code, the
        # version in the text, and the reason it would have had.
        for name in ("a pin nobody published fails --latest",
                     "the failure names the unpublished pin",
                     "the failure says the version was never published"):
            skipped.append(name)
        print("  [SKIP] %-46s npm registry unreachable"
              % "a pin nobody published fails --latest")

    # Fault 7: the npm registry cannot be reached. That is not the same as
    # "the pins are current": the check could not be carried out, and it
    # has to say so. A run that reports success here would let the
    # scheduled workflow close the tracking issue on the strength of an
    # outage.
    reset()
    text = read(CHECKER)
    # The rewrite is a string substitution against a literal in the
    # checker, so it is coupled to how that file spells the registry
    # host. If the checker is refactored to spell it differently, the
    # substitution matches nothing and this case quietly stops testing
    # what it exists to test. So the substitution is checked, not
    # assumed.
    rewritten = text.replace(REGISTRY, "http://127.0.0.1:9")
    if rewritten == text:
        print("FATAL: the checker no longer spells the registry host %r"
              % REGISTRY, file=sys.stderr)
        sys.exit(FATAL_HARNESS)
    write(CHECKER, rewritten)
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
    # The case is only meaningful when the pinned release really exists
    # upstream. If it does not, --latest already fails with "never
    # published", the exit code says 1 for a reason this case did not
    # plant, and the URL check is never exercised at all.
    published, looked = version_published("katex", current_katex())
    if (registry_reachable() and cdn_reachable()
            and looked and published):
        code, out = run(["--latest"], network=True)
        if not network_not_carried_out(
                ["a missing CDN file fails --latest",
                 "the failure names the missing file"], code, skipped):
            results.append(report("a missing CDN file fails --latest", code, 1))
            # The exit code alone cannot say WHY: a tree that is already
            # behind upstream fails for a reason this case did not plant.
            # The failure has to name the missing file.
            results.append(report_names("the failure names the missing file",
                                         out, "katex.nonexistent.css"))
            if code != 1:
                print(out[-1500:])
    else:
        for name in ("a missing CDN file fails --latest",
                     "the failure names the missing file"):
            skipped.append(name)
        print("  [SKIP] %-46s the pinned release could not be confirmed"
              % "a missing CDN file fails --latest")

    # Fault 9: a checker that hangs. The harness must say so rather than
    # die: an uncaught TimeoutExpired exits with 1, the same code a case
    # that did not behave uses, so a wedged checker would be
    # indistinguishable from a case that caught a fault.
    reset()
    write(CHECKER, "import time\ntime.sleep(30)\n")
    code, out = run(timeout=2)
    results.append(report("a wedged checker is reported as a timeout",
                          code, TIMEOUT))
    if code != TIMEOUT:
        print(out[-1500:])

    # Fault 10: no pins at all must be a FAILURE. A check that finds nothing
    # to check has checked nothing, and would pass forever on a tree where
    # the templates had been refactored past the URLs.
    reset()
    shutil.rmtree(os.path.join(WORK, "layouts"))
    os.makedirs(os.path.join(WORK, "layouts"))
    code, out = run()
    results.append(report("no pins at all -> treated as a failure", code, 1))
    if code != 1:
        print(out[-1500:])

    # Fault 11: a pin that is not a version at all. "0.16.x" names no
    # release, so there is no file behind it on the CDN. A checker that
    # read the unreadable part as 0 would call it the oldest possible
    # version and report the tree as current.
    reset()
    sub(find_pin_file(KATEX_PIN), KATEX_PIN,
        lambda m: m.group(1) + "0.16.x" + m.group(3))
    for readme in ("README.md", "README.zh.md"):
        sub(os.path.join(WORK, readme), KATEX_PROSE,
            lambda m: m.group(1) + "0.16.x")
    code, out = run()
    results.append(report("a pin that is not a version is reported",
                          code, 1))
    results.append(report_names("the failure names the malformed pin",
                                 out, "0.16.x"))
    if code != 1:
        print(out[-1500:])

    shutil.rmtree(WORK, ignore_errors=True)

    # Every check has to be accounted for exactly once: as a verdict or
    # as a skip. A check that is neither was a case that quietly
    # stopped running, and the summary would report a number that does
    # not add up with nothing to say which one went missing.
    accounted = ACCOUNTED + skipped
    missing = [n for n in CHECKS if n not in accounted]
    duplicated = sorted({n for n in accounted if accounted.count(n) > 1})
    unexpected = [n for n in accounted if n not in CHECKS]
    if missing or duplicated or unexpected:
        print("FATAL: the harness's own accounting does not add up",
              file=sys.stderr)
        for name in missing:
            print("  never accounted for: %s" % name, file=sys.stderr)
        for name in duplicated:
            print("  accounted for twice: %s" % name, file=sys.stderr)
        for name in unexpected:
            print("  not a check this harness knows: %s" % name,
                  file=sys.stderr)
        return FATAL_HARNESS

    print()
    if skipped:
        print("  %d of %d checks ran; %d skipped: %s"
              % (len(results), len(results) + len(skipped), len(skipped),
                 ", ".join(skipped)))
        # The skipped cases are the only ones that exercise the --latest
        # half of the checker, so a green run that never asked it is not a
        # green run. Say so out loud rather than letting it pass as a full
        # pass.
        print("::warning::the registry-dependent cases were skipped, so the "
              "--latest half of the checker was not exercised")
    else:
        print("  %d/%d checks behaved as specified"
              % (sum(results), len(results)))
    return 0 if all(results) else 1


def version_core(version):
    """(major, minor, patch) for a version taken from the tree.

    The version comes out of the tree, so one that does not parse means
    the tree carries a version this harness cannot read -- which is
    FATAL_HARNESS, not a silently coerced zero. The message says which
    of the two is broken: the tree, not this harness.
    """
    parts = version_parts(version)
    if parts is None:
        print("FATAL: the tree pins a version that is not a version: %r"
              % version, file=sys.stderr)
        sys.exit(FATAL_HARNESS)
    return parts


def bump(version):
    """A different version, derived from the one in the tree."""
    major, minor, patch = version_core(version)
    return "%d.%d.%d" % (major, minor, patch + 1)


def never_published(version):
    """A version of the same package that was never published.

    Built from the version in the tree, with the minor component far above
    any real release of the package, so the case cannot accidentally name
    something npm happens to publish.
    """
    major = version_core(version)[0]
    return "%d.%d.0" % (major, 999)


if __name__ == "__main__":
    sys.exit(main())
