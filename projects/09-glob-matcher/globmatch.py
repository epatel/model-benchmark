"""Shell-style glob matching.

Pattern language:
  *        matches any sequence of characters (including empty)
  ?        matches exactly one character
  [set]    matches one character in set          (e.g. [abc])
  [!set]   matches one character NOT in set      (e.g. [!abc])
           a ']' first in the set (after optional '!') is a literal member;
           an unterminated '[' matches a literal '['
  <other>  matches itself

No ranges ('-' is an ordinary set member), no escapes.
"""


def match(text, pattern):
    """Return True iff the whole of `text` matches `pattern`."""
    return _match(text, 0, pattern, 0)


def _match(t, ti, p, pi):
    if pi == len(p):
        return ti == len(t)
    c = p[pi]
    if c == "*":
        return _match(t, ti, p, pi + 1) or (
            ti < len(t) and _match(t, ti + 1, p, pi)
        )
    if ti == len(t):
        return False
    if c == "[":
        ok, nxt = _match_class(t[ti], p, pi)
        return ok and _match(t, ti + 1, p, nxt)
    if c == "?" or c == t[ti]:
        return _match(t, ti + 1, p, pi + 1)
    return False


def _match_class(ch, p, pi):
    """p[pi] == '['. Return (does ch match the class, index after the class)."""
    i = pi + 1
    negate = i < len(p) and p[i] == "!"
    if negate:
        i += 1
    chars = []
    if i < len(p) and p[i] == "]":
        chars.append("]")
        i += 1
    while i < len(p) and p[i] != "]":
        chars.append(p[i])
        i += 1
    if i == len(p):
        return ch == "[", pi + 1
    return (ch in chars) != negate, i + 1
