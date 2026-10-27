#!/usr/bin/env python3
"""Check that outline.md and the LaTeX source list the same paragraphs in the same order (outline-first rule).

Outline entries are lines `- **[<id>]** ...`; source anchors are lines `% P:<id>`. The .tex files are walked from
main.tex, following \\input / \\include in order. Fails (exit 1) on:
  - an id in the outline but not in the .tex, or the other way round;
  - a duplicated id (in either list);
  - a different order;
  - a source paragraph with no anchor right before it, or an anchor not followed by a paragraph
    (paragraph = text between blank lines or a \\paragraph{} block, floats, headings and \\label lines excluded).
Prints one summary line on success. Stdlib only.

Usage: python3 scripts/check_outline.py [outline.md] [main.tex]   (defaults: the repo's own files)
"""
import re
import sys
from pathlib import Path

ENTRY = re.compile(r"^\s*-\s+\*\*\[([a-z0-9][a-z0-9-]*)\]\*\*")
ANCHOR = re.compile(r"^\s*%\s*P:([a-z0-9][a-z0-9-]*)\s*$")
INPUT = re.compile(r"^[^%]*\\(?:input|include)\{([^}]+)\}")
FLOAT_BEGIN = re.compile(r"^\\begin\{(figure|table)\*?\}")
FLOAT_END = re.compile(r"^\\end\{(figure|table)\*?\}")
NOT_TEXT = re.compile(r"^\\(section|subsection|subsubsection|label|begin\{abstract\}|end\{abstract\}|"
                      r"input|include|bibliography|bibliographystyle|end\{document\})")


def outline_ids(path):
    return [m.group(1) for line in path.read_text().splitlines() if (m := ENTRY.match(line))]


def scan(path, root, ids, errors, seen):
    """Collect anchors in \\input order and flag unanchored paragraphs and dangling anchors."""
    path = path if path.suffix == ".tex" else path.with_suffix(".tex")
    if path in seen or not path.exists():
        return
    seen.add(path)
    sections = path.parent.name == "sections"      # paragraph rule applies to the section files only
    in_body, in_float, pending, prev_text = False, False, None, False
    for n, line in enumerate(path.read_text().splitlines(), 1):
        s = line.strip()
        if m := ANCHOR.match(line):
            ids.append(m.group(1))
            if pending:
                errors.append(f"{path.name}:{n}: anchor {pending} is not followed by a paragraph")
            pending = m.group(1)
            continue
        if m := INPUT.match(line):
            scan(root / m.group(1), root, ids, errors, seen)
            continue
        if not sections:
            continue
        if FLOAT_BEGIN.match(s):
            in_float = True
        if in_float:
            in_float = not FLOAT_END.match(s)
            continue
        if not s or NOT_TEXT.match(s):
            prev_text = False
            if pending:                            # the anchor sits on the line right before its paragraph
                errors.append(f"{path.name}:{n}: anchor {pending} is followed by a blank line or a heading")
                pending = None
            continue
        if s.startswith("%"):
            continue
        starts = not prev_text or s.startswith("\\paragraph{")
        if starts and not pending:
            errors.append(f"{path.name}:{n}: paragraph without a % P: anchor: {s[:60]}")
        pending, prev_text = None, True
    if pending:
        errors.append(f"{path.name}: anchor {pending} at end of file")


def dups(ids):
    return sorted({i for i in ids if ids.count(i) > 1})


def main():
    repo = Path(__file__).resolve().parent.parent
    outline = Path(sys.argv[1]) if len(sys.argv) > 1 else repo / "outline.md"
    tex = Path(sys.argv[2]) if len(sys.argv) > 2 else repo / "main.tex"
    o, t, errors = outline_ids(outline), [], []
    scan(tex, tex.parent, t, errors, set())
    for name, ids in (("outline", o), ("tex", t)):
        if d := dups(ids):
            errors.append(f"duplicate ids in {name}: {', '.join(d)}")
    if only := [i for i in o if i not in t]:
        errors.append(f"in outline, no anchor in tex: {', '.join(only)}")
    if only := [i for i in t if i not in o]:
        errors.append(f"anchored in tex, no outline entry: {', '.join(only)}")
    common_o = [i for i in o if i in set(t)]
    common_t = [i for i in t if i in set(o)]
    if common_o != common_t:
        k = next((n for n, (a, b) in enumerate(zip(common_o, common_t)) if a != b), None)
        errors.append(f"order differs at entry {k + 1}: outline has {common_o[k]}, tex has {common_t[k]}" if k is not None
                      else "order differs: one list repeats an id the other lists once")
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    print(f"check_outline: {len(o)} paragraphs, outline.md and the .tex agree (ids, order, every paragraph anchored)")


if __name__ == "__main__":
    main()
