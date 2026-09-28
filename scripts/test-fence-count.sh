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
# Segments whose rendered page could not be joined back to a source file.
# Declared here rather than at first use: under `set -u` a reference to an
# unset variable aborts the script, and the first use is inside the loop that
# records the miss. It lives under $d, so the trap below already cleans it up.
UNMAPPED="$d/unmapped"
: > "$UNMAPPED"
# EXIT trap, not just a trailing rm: an early abort (the FATAL exit 2, or
# set -e tripping on an assertion) would otherwise leave the temp dir and
# the extracted awk program behind on every failed run.
trap 'rm -rf "$d"' EXIT

# The repo path is derived from the script's own location, so the suite reads
# scripts/ relative to the checkout it lives in and works from any cwd.
# Both definitions are read from scripts/, the same files the workflow reads.
# They used to be mined out of the ci.yml run: block by string anchors, so
# reformatting that block left this test checking a stale pattern or failing
# with "could not mine". One definition, two readers, nothing to mine.
FENCE_AWK="$REPO/scripts/fence-counter.awk"
BOX_RE_FILE="$REPO/scripts/container-regex.txt"
# Existence BEFORE the read, and the read cannot inherit a non-zero status.
# This script runs under `set -e`, so `BOX_RE=$(cat ...)` on a missing file
# aborted the suite right there with a bare `cat:` error and the FATAL below
# never printed — the guard fired for the empty-file case only, while its
# message said "missing". Same guard-before-assignment ordering ci.yml now
# uses for these two files.
[ -f "$FENCE_AWK" ] || { echo "FATAL: missing $FENCE_AWK"; exit 2; }
[ -f "$BOX_RE_FILE" ] || { echo "FATAL: missing $BOX_RE_FILE"; exit 2; }
BOX_RE=$(cat "$BOX_RE_FILE")
[ -n "$BOX_RE" ] || { echo "FATAL: empty $BOX_RE_FILE"; exit 2; }
echo "container regex from scripts/container-regex.txt: $BOX_RE"

cp "$FENCE_AWK" "$d/prog.awk"

if ! grep -q 'END { print c+0 }' "$d/prog.awk"; then
  echo "FATAL: extraction produced no END block"; exit 2
fi
echo "extracted $(wc -l < "$d/prog.awk") lines, END present"

count() { awk -f "$d/prog.awk" "$1"; }
pass=0; fail=0
expect() { # name, expected, file
  # `|| got=ERR`: under `set -e` a non-zero awk (a syntax error in the extracted
  # program, say) would abort the whole suite, so a counter regression surfaced
  # as a crash with no indication of which case broke.
  got=$(count "$3") || got=ERR
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

# Blockquote fences, added with the regex that started accepting `>` prefixes.
printf '> ```js\n> x\n> ```\n' > "$d/eb.md"
expect "blockquote fence" 1 "$d/eb.md"

printf '> ```js\n>\n> some text\n>\n> ```\n' > "$d/ec.md"
expect "blockquote fence with text" 1 "$d/ec.md"

printf '  > ```js\n  > x\n  > ```\n' > "$d/ed.md"
expect "indented blockquote fence" 1 "$d/ed.md"

printf '> - ```go\n>   y\n>   ```\n' > "$d/ee.md"
expect "blockquote + list-item fence" 1 "$d/ee.md"

# A SECOND block in the same form. The single-block case above passed even
# while the counter was wrong, and that is the whole reason this one exists.
# The opening regex allowed a list marker only BEFORE the blockquote markers,
# so it could not match `> - ```go`. On a single block the count still came out
# 1 — but by accident: the closing line `>   ``` ` was then re-read as a NEW
# opening fence, which cancelled the 0 it should have found. One block hides
# the bug; two expose it, and the pre-fix counter reports 1 instead of 2.
printf '> - ```go\n> y\n>   ```\n> - ```py\n> z\n> ```\n' > "$d/ee2.md"
expect "blockquote + list-item, two blocks" 2 "$d/ee2.md"

# The markers may also appear in the other order, and nest.
printf -- '- > ```go\n  > y\n  > ```\n' > "$d/ef.md"
expect "list-item then blockquote fence" 1 "$d/ef.md"

printf '> - > ```go\n>   > y\n>   > ```\n' > "$d/eg.md"
expect "blockquote + list-item + blockquote" 1 "$d/eg.md"

printf '1. ~~~\n   y\n   ~~~\n' > "$d/f.md"
expect "ordered-list tilde fence" 1 "$d/f.md"

# Indent boundary. 3 spaces is the CommonMark maximum for a fenced block and
# is the case that actually reaches the render hook: measured on 0.166.0, a
# 3-space fence emits 1 Chroma .highlight container, a 4-space one emits 0
# because it is an indented code block. ci.yml compares this counter against
# that container count and fails the build on a mismatch, so counting a 4-space
# fence as a fence produced a false "render hook dropped N". These two cases
# pin both sides of the boundary; the earlier single case asserted 4 spaces
# counted as 1 and would have kept that failure alive.
printf '   ```\n   indented 3\n   ```\n' > "$d/g.md"
expect "fence indented 3 spaces (max)" 1 "$d/g.md"

printf '    ```\n    indented 4\n    ```\n' > "$d/g4.md"
expect "fence indented 4 spaces is an indented code block" 0 "$d/g4.md"

# The cap covers the line's own indent only. The gap after a list or blockquote
# marker is the container's content indent and is NOT capped, so a two-digit
# ordered marker — which needs four spaces of gap — is still a fence. Capping
# the wrong one of the two would reject this valid case.
printf '10. ```bash\n    body\n    ```\n' > "$d/g10.md"
expect "two-digit ordered marker with 4-space gap" 1 "$d/g10.md"

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
  # Same set rule as ci.yml, by the same mechanism: map each rendered page back
  # to its source file through `hugo list all`, not by guessing from the
  # filename. Two earlier versions of this block got it wrong. One counted every
  # content/posts/*.md, which includes drafts and future-dated posts that are in
  # source and never in the build — so a draft post made this fail while the CI
  # assertion passed, and the two were checking different sets. The other guessed
  # the mapping from filenames, which is wrong twice over: the example posts
  # carry no `slug:` front matter, so Hugo falls back to the TITLE slug and
  # aurora.md renders as the-aurora-background, douban-card-demo.md as
  # douban-card-shortcode.
  # Under $d, so the EXIT trap owns it. It used to be `LIST=$(mktemp)`, created
  # outside $d and removed only on the two success paths below — so a `set -e`
  # trip between its creation and those removals (awk failing inside either
  # loop) leaked the file. $d and UNMAPPED were both already covered; this was
  # the one temp file the script leaked. With the two explicit `rm -f "$LIST"`
  # calls kept, cleanup happens early on the success paths too.
  LIST="$d/list"
  # Status captured rather than inherited: under `set -e` a failing subshell
  # (hugo missing from PATH, a bad config) killed the run with stderr discarded,
  # so the user saw the "### cross-check" header and nothing else.
  if ! ( cd "$REPO/exampleSite" && hugo list all ) > "$LIST" 2>&1; then
    fail=$((fail+1))
    echo "  FAIL  could not run 'hugo list all' in $REPO/exampleSite (is hugo on PATH?)"
    head -5 "$LIST" | sed 's/^/        /'
    # Stop here. Falling through ran the mapping and container loops against a
    # file holding stderr text instead of CSV, so every page also reported
    # "could not map" and buried the one failure that matters.
    rm -f "$LIST"
  else
  tot=0
  # find -mindepth 2, the same rule ci.yml uses. A posts/*/ glob matches one
  # level only, so a nested page bundle (posts/a/b/index.html) was counted by
  # the CI assertion and silently skipped here — the two sets diverged while
  # the comment claimed they were identical.
  while IFS= read -r p; do
    [ -n "$p" ] || continue
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
      printf '%s\n' "$seg" >> "$UNMAPPED"
      continue
    fi
    n=$(count "$REPO/exampleSite/$md")
    tot=$((tot+n))
    printf '  %-32s %s\n' "$(basename "$md")" "$n"
  done < <(find "$TREE/posts" -mindepth 2 -name index.html ! -path '*/page/*' | sort)
  rm -f "$LIST"

  rendered=0
  pages_seen=0
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    # A page that failed the join above has no source file, so it added
    # nothing to `tot` while this loop still added its containers. The
    # equality at the end then compared sums over two different sets, and a
    # mismatch blamed the fence state machine for what was a join miss. Skip
    # the same pages here so both sums cover the same set. The run still fails
    # — the join miss is already recorded above — this only fixes the
    # DIAGNOSIS.
    if grep -qxF "$(basename "$(dirname "$p")")" "$UNMAPPED"; then
      continue
    fi
    # BOX_RE comes from scripts/container-regex.txt — the same file ci.yml
    # reads — not from a copy inlined here, and not mined out of the workflow.
    # This test asks whether
    # the fence counter agrees with the build; if it counted containers by its
    # own regex, a change to the CI regex would leave the two comparing
    # different notions of "container" and still pass. `|| true` because under
    # `set -euo pipefail` a grep matching nothing exits 1 and would kill the
    # script on a page with no code blocks — a normal page, not a failure.
    k=$(grep -oE "$BOX_RE" "$p" | wc -l || true)
    rendered=$((rendered+k))
    pages_seen=$((pages_seen+1))
  done < <(find "$TREE/posts" -mindepth 2 -name index.html ! -path '*/page/*' | sort)
  if [ -s "$UNMAPPED" ]; then
    echo "  note  $(wc -l < "$UNMAPPED") page(s) counted in neither total:"\
" no source file to compare against"
  fi
  rm -f "$UNMAPPED"
  # Empty-set guard. With TREE present but holding no post pages, both loops
  # iterated zero times, 0 == 0, and the cross-check reported PASS — a green
  # assertion that checked nothing. ci.yml guards the same way with saw_pre.
  if [ "$pages_seen" -eq 0 ]; then
    fail=$((fail+1))
    echo "  FAIL  no post pages under $TREE/posts — the cross-check would pass on an empty set"
  fi
  echo "  source blocks (counter) = $tot"
  echo "  containers (rendered)   = $rendered"
  if [ "$tot" = "$rendered" ]; then
    pass=$((pass+1)); echo "  PASS  counter agrees with the rendered build"
  else
    fail=$((fail+1)); echo "  FAIL  counter=$tot but the build rendered $rendered"
  fi
  fi   # end of: hugo list all succeeded (the else branch above was the failure)
fi

echo
echo "fence tests: $pass passed, $fail failed"
# No trailing `rm -rf "$d"`: the trap installed at the top of this script owns
# cleanup. Deleting it here as well meant every successful run removed the
# temp dir twice, which made the trap look unreliable for no gain — and it
# covered nothing the trap missed, since the trap already runs on the `exit 1`
# below and on the FATAL exits.
# Not `exit $fail`: a POSIX exit status is masked to 8 bits, so 256 failures
# wrap to 0 and the CI step would report success with every check failing.
if [ "$fail" -ne 0 ]; then exit 1; fi
exit 0
