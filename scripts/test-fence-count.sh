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
set -uo pipefail
REPO=$(cd "$(dirname "$0")/.." && pwd)
d=$(mktemp -d)
rm -rf "$d"; mkdir -p "$d"

# The repo path is passed as argv, not derived from __file__: this python runs
# from a heredoc on stdin, where __file__ does not exist and `here` would
# silently collapse to the cwd — which is how the first in-repo run looked for
# .github/workflows/ci.yml one directory ABOVE the repo and found nothing.
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
echo "### against the shipped example content"
tot=0
while IFS= read -r md; do
  n=$(count "$md")
  tot=$((tot+n))
  printf '  %-32s %s\n' "$(basename "$md")" "$n"
done < <(find "$REPO/exampleSite/content/posts" -name '*.md' ! -name '_index.md' | sort)
echo "  total=$tot  (CI's correct-build expectation is 3)"
if [ "$tot" = "3" ]; then
  pass=$((pass+1)); echo "  PASS  example content total == 3"
else
  fail=$((fail+1)); echo "  FAIL  example content total expected 3 got $tot"
fi

echo
echo "fence tests: $pass passed, $fail failed"
rm -rf "$d"
exit $fail
