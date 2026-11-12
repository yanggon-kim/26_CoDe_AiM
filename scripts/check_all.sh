#!/usr/bin/env bash
# Full verification pass for a multi-section edit (the top tier; see paper_isca2/ONBOARDING.md "Verification tiers").
#   1. every scripts/make_*.py (each asserts the numbers its float and the prose print);
#      figs/fig_area.pdf (not in the paper; matplotlib rewrites it with a new timestamp) is restored if it was clean;
#      a figs/src/*.html the scripts changed means its PDF is stale (run scripts/html2pdf.py <name>) -> failure;
#      a changed tables/*.tex is reported (the build below already uses it).
#   2. latexmk once; 3. check_outline.py; 4. check_prose.py --system CoDe --cite --captions on all sections
#      (concatenated, so captions meet their citing paragraphs; a report, never a failure).
# Prints a summary of at most 10 lines; exits 1 on any failure.
# Usage: bash scripts/check_all.sh      (from anywhere)
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO" || exit 2
PROSE="${CHECK_PROSE:-/home/yanggon/skills/architecture-paper-writing/scripts/check_prose.py}"
PROSE_BASELINE=3   # prose flags at the commit that added this script (3 caption runs shared with the prose); update when accepted
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fail=0

# 1. generators
area_clean=0
git diff --quiet -- figs/fig_area.pdf && area_clean=1
md5sum figs/src/*.html tables/*.tex > "$TMP/before.md5"
bad=""
for s in scripts/make_*.py; do
  if ! python3 "$s" > "$TMP/out.txt" 2>&1; then
    bad="$bad $(basename "$s" .py): $(grep -v '^\s*$' "$TMP/out.txt" | tail -1)"
  fi
done
[ "$area_clean" = 1 ] && git checkout -q -- figs/fig_area.pdf
stale_html="" ; new_tab=""
while read -r f; do
  case "$f" in figs/src/*) stale_html="$stale_html $(basename "$f" .html)";; *) new_tab="$new_tab $(basename "$f")";; esac
done < <(md5sum --quiet -c "$TMP/before.md5" 2>/dev/null | sed -n 's/: FAILED$//p')
if [ -n "$bad" ]; then echo "asserts : FAIL$bad"; fail=1; else echo "asserts : all make_*.py pass"; fi
if [ -n "$stale_html" ]; then echo "stale   : figs/src changed, run html2pdf.py$stale_html"; fail=1; fi
[ -n "$new_tab" ] && echo "tables  : regenerated with changes:$new_tab"

# 2. build
if latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex > "$TMP/latexmk.txt" 2>&1; then build=ok; else build=FAIL; fail=1; fi
pages="$(pdfinfo main.pdf 2>/dev/null | awk '/^Pages:/{print $2}')"
undef="$(grep -cE "LaTeX Warning: (Reference|Citation).*undefined" main.log)"
multi="$(grep -c "multiply defined" main.log)"
ohb="$(grep -c "^Overfull \\\\hbox" main.log)"
ovb="$(grep -c "^Overfull \\\\vbox" main.log)"
etal="$(grep -c "et al" main.bbl)"
refs="$(pdftotext -bbox main.pdf - 2>/dev/null | awk '/<page /{p++} />References</{split($0,a,"\""); print p (a[2] > 306 ? " R" : " L"); exit}')"
[ "$undef" -gt 0 ] || [ "$multi" -gt 0 ] || [ "$ohb" -gt 0 ] || [ "$etal" -gt 0 ] && fail=1
echo "build   : latexmk $build; $pages pages; References heading p. ${refs:-?} (body ends there)"
echo "latex   : undefined $undef, multiply defined $multi, overfull hbox $ohb / vbox $ovb (vbox not fatal), 'et al' in bbl $etal"

# 3. outline
if python3 scripts/check_outline.py > "$TMP/outline.txt" 2>&1; then
  echo "outline : pass ($(grep -o '[0-9]* paragraphs' "$TMP/outline.txt"))"
else
  echo "outline : FAIL: $(head -1 "$TMP/outline.txt")"; fail=1
fi

# 4. prose (report only)
cat sections/*.tex | python3 "$PROSE" - --system CoDe --cite --captions --quiet > "$TMP/prose.txt" 2>&1
flags="$(awk -F: '
  /\(1\) questions/ {split($2,a," "); n+=a[1]}
  /\(2\) banned/    {split($2,a," "); n+=a[1]}
  /\(7\) citation/  {if (match($2,/[0-9]+ suspects/)) n+=substr($2,RSTART,RLENGTH)+0}
  /\(8\) captions/  {if (match($2,/[0-9]+ over 30/)) n+=substr($2,RSTART,RLENGTH)+0;
                     if (match($2,/[0-9]+ runs shared/)) n+=substr($2,RSTART,RLENGTH)+0}
  END {print n+0}' "$TMP/prose.txt")"
echo "prose   : $flags flags (questions + banned + cite suspects + long captions + caption runs), $((flags - PROSE_BASELINE)) vs baseline $PROSE_BASELINE"

if [ "$fail" = 0 ]; then echo "RESULT  : PASS"; else echo "RESULT  : FAIL"; fi
exit "$fail"
