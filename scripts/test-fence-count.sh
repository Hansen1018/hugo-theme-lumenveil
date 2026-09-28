#!/usr/bin/env bash
# Regression test for the fence counter in .github/workflows/ci.yml.
# Run directly: scripts/test-fence-count.sh
#
# Test the round-23 fence counter against every fence form the comment claims.
#
# Harness bug fixed here: the first version extracted the awk program with a
# NON-GREEDY regex that stopped BEFORE `END { print c+0 }`, so the extracted
# program had no END block and printed nothing — all 10 cases reported
# `got=` empty. That was a broken test, not a broken counter. The extractor now
# takes everything between `n=$(awk '` and `' "$md")`, END included.
set -euo pipefail
REPO=$(cd "$(dirname "$0")/.." && pwd)
d=$(mktemp -d)
# EXIT trap, not just a trailing rm: an early abort (the FATAL exit 2, or
# set -e tripping on an assertion) would otherwise leave the temp dir and
# the extracted awk program behind on every failed run.
trap 'rm -rf "$d"' EXIT

# The repo path is passed as argv, not derived from __file__: this python runs
# from a heredoc on stdin, where __file__ does not exist and `here` would
# silently collapse to the cwd — which is how the first in-repo run looked for
# .github/workflows/ci.yml one directory ABOVE the repo and found nothing.
# The container regex, mined from the same file for the same reason the awk
# program is: two copies of one definition drift, and this test exists to check
# the shipped behaviour rather than a lookalike of it.
BOX_RE=$(python3 - "$REPO" <<'PY2'
import io, re, sys
s = io.open(sys.argv[1] + "/.github/workflows/ci.yml", encoding="utf8").read()
# Anchor on the line, then take everything between -oE ' and ' "$p".
# NOT a [^']* scan: in ci.yml the pattern is written in YAML shell-escaped form
# (class=["'"'"']?highlight...) so a quote-avoiding class hits the embedded
# quote and fails to match.
m = re.search(r"n_box=\$\(grep -oE '(.*)' \"\$p\"", s)
assert m, "could not find the container regex in ci.yml"
pat = m.group(1)
assert "highlight" in pat, "mined pattern is not the container regex: %r" % pat
print(pat)
PY2
)
[ -n "$BOX_RE" ] || { echo "FATAL: could not mine the container regex from ci.yml"; exit 2; }
echo "container regex mined: $BOX_RE"

python3 - "$REPO" <<'PY' > "$d/prog.awk"
import io, sys
ci = sys.argv[1] + "/.github/workflows/ci.yml"
s = io.open(ci, encoding="utf8").read()
start = s.index("n=$(awk '") + len("n=$(awk '")
end = s.index("' \"$md\")", start)
prog = s[start:end]
assert "END { print c+0 }" in prog, "END block missing from extraction"
print(prog)
PY

if ! grep -q 'END { print c+0 }' "$d/prog.awk"; then
  echo "FATAL: extraction produced no END block"; exit 2
fi
echo "extracted $(wc -l < "$d/prog.awk") lines, END present"

count() { awk -f "$d/prog.awk" "$1"; }
pass=0; fail=0
expect() { # name, expected, file
  got=$(count "$3")
  if [ "$got" = "$2" ]; then
    pass=$((pass+1)); echo "PASS  $1 (=$got)"
  else
    fail=$((fail+1)); echo "FAIL  $1 expected=$2 got=${got:-<empty>}"
  fi
}

printf 'plain triple fence\n```\ncode\n```\n' > "$d/a.md"
expect "plain triple" 1 "$d/a.md"

printf '```js\nx\n```\n```py\ny\n```\n' > "$d/b.md"
expect "two blocks" 2 "$d/b.md"

printf '~~~sh\nx\n~~~\n' > "$d/c.md"
expect "tilde fence" 1 "$d/c.md"

printf '````md\n```js\ninner\n```\n````\n' > "$d/d.md"
expect "outer 4 wrapping inner 3" 1 "$d/d.md"

printf -- '- ```bash\n  x\n  ```\n' > "$d/e.md"
expect "list-item fence" 1 "$d/e.md"

printf '1. ~~~\n   y\n   ~~~\n' > "$d/f.md"
expect "ordered-list tilde fence" 1 "$d/f.md"

printf '    ```\n    indented\n    ```\n' > "$d/g.md"
expect "indented fence" 1 "$d/g.md"

printf '```\n```py\n' > "$d/h.md"
expect "unclosed fence counts once" 1 "$d/h.md"

printf 'no fences at all\njust prose\n' > "$d/i.md"
expect "no fences" 0 "$d/i.md"

printf '```ts\na\n```\n```go\nb\n```\n~~~js\nc\n~~~\n- ```rust\n  d\n  ```\n' > "$d/j.md"
expect "mixed forms" 4 "$d/j.md"

# The real example content, which is what CI actually counts.
echo
echo "### cross-check against what Hugo actually rendered"
# No magic constant. An earlier version asserted total == 3, which meant any
# edit to the example content broke this test for reasons that had nothing to
# do with the counter — and, worse, a coincidental miscount could have matched
# 3 and hidden a real regression. The useful invariant is that the counter
# agrees with the containers in a real build; that stays true as content is
# added or removed, and fails precisely when the two disagree.
TREE=${TREE:-}
REQUIRE_TREE=${REQUIRE_TREE:-}
if [ -z "$TREE" ] || [ ! -d "$TREE" ]; then
  if [ -n "$REQUIRE_TREE" ]; then
    # Asked for a tree and did not get one. Skipping here is exactly how the
    # cross-check went green without running when the build output path moved.
    echo "::error::REQUIRE_TREE is set but TREE='${TREE}' is not a directory"
    exit 1
  fi
  echo "  SKIP  no rendered tree given (set TREE=/path/to/pub to run this)"
else
  # Same set rule as ci.yml: count only files that actually rendered. A
  # find over all of content/posts included drafts and future-dated posts,
  # which are in source and never in the build — so the cross-check would fail
  # on a draft post while the CI assertion passed, and the two would disagree
  # about what they are checking.
  # Same set rule as ci.yml, by the same mechanism: map each rendered page back
  # to its source file through `hugo list all`, not by guessing from the
  # filename. An earlier version of this block did guess, and was wrong twice
  # over — the example posts carry no `slug:` front matter, so the output name
  # falls back to the TITLE slug: aurora.md renders as the-aurora-background and
  # douban-card-demo.md as douban-card-shortcode. It also counted every
  # content/posts/*.md, which includes drafts and future-dated posts that are in
  # source and never in the build, so a draft post made this fail while the CI
  # assertion passed — the two would have been checking different sets.
  LIST=$(mktemp)
  ( cd "$REPO/exampleSite" && hugo list all ) > "$LIST" 2>/dev/null
  tot=0
  for p in "$TREE"/posts/*/index.html; do
    [ -e "$p" ] || continue
    case "$p" in */page/*) continue ;; esac
    seg=$(basename "$(dirname "$p")")
    md=$(awk -F, -v want="$seg" '
      /^content\/posts\// && !/_index\.md$/ {
        if (match($0, /https?:\/\/[^ ,]+/)) {
          u = substr($0, RSTART, RLENGTH)
          sub(/\/+$/, "", u)
          n = split(u, a, "/")
          if (a[n] == want) { print $1; exit }
        }
      }' "$LIST")
    if [ -z "$md" ]; then
      fail=$((fail+1)); echo "  FAIL  could not map rendered page $seg back to a source file"
      continue
    fi
    n=$(count "$REPO/exampleSite/$md")
    tot=$((tot+n))
    printf '  %-32s %s\n' "$(basename "$md")" "$n"
  done
  rm -f "$LIST"

  rendered=0
  for p in "$TREE"/posts/*/index.html; do
    [ -e "$p" ] || continue
    case "$p" in */page/*) continue ;; esac
    # BOX_RE is mined from ci.yml, not repeated here. This test asks whether
    # the fence counter agrees with the build; if it counted containers by its
    # own regex, a change to the CI regex would leave the two comparing
    # different notions of "container" and still pass. `|| true` because under
    # `set -euo pipefail` a grep matching nothing exits 1 and would kill the
    # script on a page with no code blocks — a normal page, not a failure.
    k=$(grep -oE "$BOX_RE" "$p" | wc -l || true)
    rendered=$((rendered+k))
  done
  echo "  source blocks (counter) = $tot"
  echo "  containers (rendered)   = $rendered"
  if [ "$tot" = "$rendered" ]; then
    pass=$((pass+1)); echo "  PASS  counter agrees with the rendered build"
  else
    fail=$((fail+1)); echo "  FAIL  counter=$tot but the build rendered $rendered"
  fi
fi

echo
echo "fence tests: $pass passed, $fail failed"
rm -rf "$d"
exit $fail
