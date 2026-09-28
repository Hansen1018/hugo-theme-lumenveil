#!/usr/bin/env python3
"""Pin the measured behaviour of the imaging quality config across Hugo versions.

Why this exists
---------------
`exampleSite/hugo.toml` sets per-format keys:

    [imaging.jpeg] / [imaging.webp] / [imaging.avif]   ->  quality

Those keys only exist from Hugo 0.163.0. On 0.146.0 — the floor declared in
theme.toml — they are unknown keys, and Hugo ignores unknown config keys
SILENTLY: the build exits 0 and prints no warning. A green 0.146.0 CI leg
therefore says nothing about whether image quality is being applied.

The scalar form (`[imaging] quality`) does work on 0.146.0, but Hugo 0.163.0
deprecated it and prints:

    WARN  deprecated: project config key imaging.quality was deprecated in
          Hugo v0.163.0 and will be removed in a future release. Set the quality
          per format instead with imaging.jpeg.quality, ...

So no single spelling is clean across the whole 0.146.0+ range, and that is a
property of Hugo, not something this theme can configure away. The shipped
config keeps the forward-compatible spelling deliberately.

What this test actually asserts
-------------------------------
Not "the config is right" — that is a judgement call already recorded in the
config comment. This asserts the two mechanical facts that a future Hugo could
silently invalidate, and that a reviewer should not have to re-derive by hand:

  1. On Hugo >= 0.163.0 the per-format form TAKES EFFECT: quality 20 and 85
     produce different output.
  2. On Hugo < 0.163.0 the per-format form is INERT: quality 20, 85 and no
     config at all produce byte-identical output — and the build still
     succeeds silently.

Assertion 2 is the important one. It is the exact failure mode this file exists
to make visible: if a future Hugo ever starts WARNING on unknown keys, or
starts applying them, this test fails and someone has to look, instead of the
inertness continuing to look like a passing build.

A third, unconditional assertion guards against the test itself going vacuous:
the scalar form must produce a different size at 20 vs 85 on every version
that is supposed to support it. Without that, a fixture that failed to build
could return equal sizes everywhere and assertions 1 and 2 would both pass for
the wrong reason.

Usage: scripts/test-imaging-config.py     (uses `hugo` from PATH)
       THEME_DIR=/path/to/repo scripts/test-imaging-config.py
"""
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

REPO = os.environ.get("THEME_DIR") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

PER_FORMAT_MIN = (0, 163, 0)

fails = []


def check(ok, label, detail=""):
    print("  %-56s %s" % (label, "ok" if ok else "FAIL"))
    if not ok:
        if detail:
            print("      %s" % detail)
        fails.append(label)
    return ok


def hugo_exe():
    """Resolve the Hugo binary, or exit with something readable.

    Without this, a missing binary surfaces as a bare FileNotFoundError
    traceback from subprocess. The friendly "cannot parse `hugo version`"
    message that used to be the only diagnostic only covered an *unparsable*
    version string, never an *absent* one — measured: with `hugo` off PATH the
    script died on a raw traceback and printed nothing of its own.
    """
    exe = shutil.which("hugo")
    if exe is None:
        print("  FATAL: `hugo` was not found on PATH.")
        print("  This test builds a real fixture, so it needs a Hugo binary.")
        print("  Install one, or put its directory at the front of PATH.")
        sys.exit(2)
    return exe


def hugo_version():
    try:
        out = subprocess.run([hugo_exe(), "version"],
                             capture_output=True, text=True)
    except OSError as e:
        print("  FATAL: could not run hugo: %s" % e)
        sys.exit(2)
    m = re.search(r"v(\d+)\.(\d+)\.(\d+)", out.stdout)
    if not m:
        print("  FATAL: could not parse `hugo version` output")
        print(out.stdout, out.stderr)
        sys.exit(2)
    return tuple(int(x) for x in m.groups())


def noise_png(path, size=400, seed=20260929):
    """A noise PNG. Noise is the right fixture here: JPEG/WebP/AVIF all
    compress noise poorly and near-linearly in quality, so a quality knob that
    works moves the byte count a lot and one that is ignored moves it not at
    all. A smooth gradient would hide a 20-vs-85 difference."""
    import random
    random.seed(seed)
    # bytearray + list + join, not `+=` on immutable bytes. The first version
    # accumulated 400 rows with `rows += row` and each row with 400
    # `row += bytes(...)`: every one of those copies the whole accumulator, so
    # the fixture is quadratic in its own size. Measured, 400x400: 0.22s
    # building rows this way, 0.19s this way — a modest gain, because the
    # per-pixel randrange calls dominate, but the quadratic term is gone and
    # the code is no longer a trap for whoever doubles `size` later.
    rows = []
    for _ in range(size):
        row = bytearray(b"\x00")
        for _ in range(size):
            row += bytes((random.randrange(256), random.randrange(256),
                          random.randrange(256)))
        rows.append(bytes(row))
    rows = b"".join(rows)

    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(
            ">I", zlib.crc32(c) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(rows, 6))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


TEMPLATE = """{{ $img := resources.Get "images/probe.png" }}
{{ $j := $img.Process "jpg" }}
{{ $w := $img.Process "webp" }}
{{ $a := $img.Process "avif" }}
JPEG: {{ $j.Content | len }}
WEBP: {{ $w.Content | len }}
AVIF: {{ $a.Content | len }}
"""

PER_FORMAT = """[imaging.jpeg]
quality = {q}
[imaging.webp]
quality = {q}
[imaging.avif]
quality = {q}"""

SCALAR = "[imaging]\nquality = {q}"

FMTS = ("JPEG", "WEBP", "AVIF")


def build(work, name, cfg):
    """Render the fixture and return a (sizes, err) pair.

    sizes maps FMT -> output byte count, and is {} when the build failed.
    err is None on success, or the first few lines of Hugo's own output on
    failure — kept so a caller can say WHICH case broke instead of only that
    something did.
    """
    out = os.path.join(work, "out-" + name)
    shutil.rmtree(out, ignore_errors=True)
    with open(os.path.join(work, "hugo.toml"), "w") as fh:
        fh.write("baseURL = 'https://example.org/'\n"
                 "title = 'imaging probe'\n"
                 "disableKinds = ['taxonomy', 'term', 'rss', 'sitemap']\n")
        fh.write(cfg)
    proc = subprocess.run(
        [hugo_exe(), "--quiet", "--destination", out],
        cwd=work, capture_output=True, text=True)
    page = os.path.join(out, "index.html")
    if proc.returncode != 0 or not os.path.exists(page):
        return {}, (proc.stdout + proc.stderr).strip().splitlines()[:3]
    sizes = {}
    for line in open(page, encoding="utf-8", errors="replace"):
        m = re.match(r"(JPEG|WEBP|AVIF):\s*(\d+)", line.strip())
        if m:
            sizes[m.group(1)] = int(m.group(2))
    return sizes, None


def main():
    ver = hugo_version()
    print("hugo   : %d.%d.%d" % ver)
    print("theme  : %s" % REPO)
    per_format_supported = ver >= PER_FORMAT_MIN
    print("per-format keys (>= 0.163.0) are %s on this version"
          % ("SUPPORTED" if per_format_supported else "INERT"))

    work = tempfile.mkdtemp(prefix="imaging-config-")
    try:
        os.makedirs(os.path.join(work, "assets", "images"))
        os.makedirs(os.path.join(work, "layouts"))
        os.makedirs(os.path.join(work, "content"))
        noise_png(os.path.join(work, "assets", "images", "probe.png"))
        with open(os.path.join(work, "layouts", "index.html"), "w") as fh:
            fh.write(TEMPLATE)
        with open(os.path.join(work, "content", "_index.md"), "w") as fh:
            fh.write("---\ntitle: probe\n---\n")

        print("\nper-format spelling (what exampleSite ships)")
        pf20, err = build(work, "pf20", PER_FORMAT.format(q=20))
        pf85, err85 = build(work, "pf85", PER_FORMAT.format(q=85))
        pfnone, errn = build(work, "pfnone", "")
        if not pf20 or not pf85 or not pfnone:
            for label, e in (("q=20", err), ("q=85", err85), ("none", errn)):
                if e:
                    print("      build %s failed: %s" % (label, " / ".join(e)))
            # Record the failure, then keep going to the summary below. This
            # used to `return check(False, ...)`, which had two problems: the
            # trailing "N FAILED" line never printed, and — worse — check()
            # returns `ok`, so that return statement handed `False` to
            # `sys.exit(main())`, and False is falsy: the process exited 0 on a
            # failed fixture build. A CI job reading the exit code went green
            # on the one failure this test most needs to report.
            check(False, "fixture builds on all three per-format cases")
            return 1
        for f in FMTS:
            print("      %-6s q20=%-9d q85=%-9d none=%-9d"
                  % (f, pf20[f], pf85[f], pfnone[f]))

        print("\nscalar spelling (works on 0.146.0, deprecated on 0.163.0+)")
        sc20, sc_err20 = build(work, "sc20", SCALAR.format(q=20))
        sc85, sc_err85 = build(work, "sc85", SCALAR.format(q=85))
        if not sc20 or not sc85:
            # The per-format path above prints Hugo's captured output on
            # failure. This one used to discard it (`sc20, _ = build(...)`) and
            # report only that a build failed, which is the one case where the
            # reason is most worth having: a scalar-form failure here is usually
            # a config key that no longer exists at all.
            for label, e in (("q=20", sc_err20), ("q=85", sc_err85)):
                if e:
                    print("      build %s failed: %s" % (label, " / ".join(e)))
            # Same reason as the per-format path above: no early return with
            # check()'s return value, or the script exits 0 on a failure.
            check(False, "scalar fixture builds on both quality settings")
            return 1
        for f in FMTS:
            print("      %-6s q20=%-9d q85=%-9d" % (f, sc20[f], sc85[f]))

        # Guard against a vacuous pass: if the scalar knob moved nothing either,
        # every equality below would hold for the wrong reason.
        check(any(sc20[f] != sc85[f] for f in FMTS),
              "scalar quality changes the output (test is not vacuous)",
              "scalar q20 == q85 for every format — the fixture cannot "
              "distinguish quality settings, so assertions below are unsafe")

        if per_format_supported:
            for f in FMTS:
                check(pf20[f] != pf85[f],
                      "per-format quality is honoured: %s" % f,
                      "0.163.0+ should honour [imaging.%s].quality; "
                      "q20=%d q85=%d" % (f.lower(), pf20[f], pf85[f]))
        else:
            # The silent-ignore behaviour this file exists to pin.
            for f in FMTS:
                check(pf20[f] == pf85[f] == pfnone[f],
                      "per-format quality is inert below 0.163.0: %s" % f,
                      "expected q20=q85=none, got q20=%d q85=%d none=%d"
                      % (pf20[f], pf85[f], pfnone[f]))
            # Informational, NOT an assertion. The first version called
            # check(True, ...) here, which can never fail and so padded the
            # "all checks passed" count with a line that read like coverage of
            # the silent-ignore property while testing nothing at all. A
            # permanent green entry is worse than no entry: it invites the next
            # reader to trust it.
            print("      NOTE: the build exited 0 with these unknown keys "
                  "present. That silence IS the failure mode this test "
                  "documents — the assertions above, not this line, are what "
                  "pin it.")
    finally:
        shutil.rmtree(work, ignore_errors=True)

    print()
    print("imaging config tests: %s" % ("all checks passed" if not fails
                                        else "%d FAILED" % len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
