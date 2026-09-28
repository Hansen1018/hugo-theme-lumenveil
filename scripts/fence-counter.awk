# Fence counter for .github/workflows/ci.yml.
#
# One definition, read by BOTH the CI step and scripts/test-fence-count.sh.
# It used to live inline in the ci.yml run: block and be mined back out by
# string anchors, so reformatting that block left the test checking a stale
# pattern or failing with "could not mine".
#
# Counts opening fences by CommonMark's rules rather than toggling on any ``` or
# ~~~ line:
#   - a fence may be indented, follow a list marker (`- ```bash`, `1. ~~~`), or
#     sit inside a blockquote (`> ```js`);
#   - a fence opens with 3+ of one marker and closes only on the SAME marker, at
#     least as long, with nothing after it — without the length check a
#     4-backtick outer fence wrapping an inner 3-backtick block toggled twice per
#     outer pair and miscounted;
#   - a closing fence carries no info string.
{
  if (!open) {
    if (match($0, /^[[:space:]]*([-*+]|[0-9]+[.)])?[[:space:]]*(>[[:space:]]*)*(```+|~~~+)/)) {
      s = substr($0, RSTART, RLENGTH)
      ch = (index(s, "`") > 0) ? "`" : "~"
      if (length(substr(s, index(s, ch))) >= 3) {
        open = 1; c++
        clen = length(substr(s, index(s, ch)))
        cch = ch
      }
    }
  } else {
    if (match($0, /^[[:space:]]*(>[[:space:]]*)*(```+|~~~+)[[:space:]]*$/)) {
      s = substr($0, RSTART, RLENGTH)
      if (index(s, cch) > 0 && length(substr(s, index(s, cch))) >= clen) {
        open = 0
      }
    }
  }
}
END { print c+0 }
