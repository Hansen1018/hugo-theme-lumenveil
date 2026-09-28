# Fence counter for .github/workflows/ci.yml.
#
# One definition, read by BOTH the CI step and scripts/test-fence-count.sh.
# It used to live inline in the ci.yml run: block and be mined back out by
# string anchors, so reformatting that block left the test checking a stale
# pattern or failing with "could not mine".
#
# Counts opening fences rather than toggling on any ``` or ~~~ line:
#   - a fence may follow a list marker (`- ```bash`, `1. ~~~`) or sit inside a
#     blockquote (`> ```js`);
#   - a fence opens with 3+ of one marker and closes only on the SAME marker, at
#     least as long, with nothing after it — without the length check a
#     4-backtick outer fence wrapping an inner 3-backtick block toggled twice per
#     outer pair and miscounted;
#   - a closing fence carries no info string.
#
# The 3-space indent cap is load-bearing, and it is here because of a measured
# asymmetry, not a stylistic choice. ci.yml compares the fence count against the
# number of Chroma .highlight containers the build produced and fails on a
# mismatch as "the render hook dropped N". A fence indented 4+ spaces is an
# INDENTED CODE BLOCK, which Hugo renders as a bare <pre><code> with no
# container, so counting it produced a permanent, content-dependent false
# failure. Measured on 0.166.0, building each case and counting the emitted
# containers:
#
#     indent 0..3  ->  counter 1, 1 .highlight container   agree
#     indent 4..5  ->  counter 1, 0 .highlight containers   disagree
#
# The cap applies to the line's leading indentation only. The gap after a list
# or blockquote marker is NOT capped, because that gap is the container's
# content indent and a two-digit ordered marker legitimately needs four spaces
# (`10. ```bash` is a fence, not an indented code block). Capping the wrong one
# of the two would reject a valid fence instead of the invalid one.
#
# The old header claimed these rules were "CommonMark's rules". They are
# CommonMark's rules for the cases this counter sees; the wording was broader
# than the regex, which accepted any indent at all.
function leading_spaces(s,   n) {
  n = 0
  while (substr(s, n + 1, 1) == " ") n++
  return n
}

# True when the text before the fence run is a legal block prefix: at most three
# leading spaces, plus optionally list/blockquote markers. For a bare fence the
# prefix is whitespace only, and it is the indent, so it is capped. Once a
# marker is present the prefix is a container construct and only the leading
# indent is capped.
function indent_ok(prefix,   lead) {
  lead = leading_spaces(prefix)
  if (lead > 3) return 0
  if (prefix ~ /^[ ]*$/) return 1
  return (prefix ~ /[-*+0-9>]/)
}

{
  if (!open) {
    if (match($0, /^[[:space:]]*([[:space:]]*([-*+]|[0-9]+[.)]|>))*[[:space:]]*(```+|~~~+)/)) {
      s = substr($0, RSTART, RLENGTH)
      ch = (index(s, "`") > 0) ? "`" : "~"
      if (indent_ok(substr(s, 1, index(s, ch) - 1))) {
        if (length(substr(s, index(s, ch))) >= 3) {
          open = 1; c++
          clen = length(substr(s, index(s, ch)))
          cch = ch
        }
      }
    }
  } else {
    # The trailing `[[:space:]]*$` anchor stays. It is what makes a CLOSING
    # fence carry no info string: without it, a line like "```py" inside an open
    # block would close it, which the file's own header promises it cannot. An
    # intermediate revision of this rewrite dropped the anchor in favour of the
    # opening-pattern regex; that was not a measured requirement, it was an
    # unmeasured regression, and the anchor is put back.
    if (match($0, /^[[:space:]]*([[:space:]]*([-*+]|[0-9]+[.)]|>))*[[:space:]]*(```+|~~~+)[[:space:]]*$/)) {
      s = substr($0, RSTART, RLENGTH)
      if (index(s, cch) > 0 && length(substr(s, index(s, cch))) >= clen) {
        open = 0
      }
    }
  }
}
END { print c+0 }
