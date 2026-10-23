#!/usr/bin/env python3
"""Turn an HTML figure prototype (figs/src/<name>.html) into the paper's figs/<name>.pdf and a figs/<name>.png preview.

Each prototype holds one inline <svg> drawn at its final physical size (width/height in pt; \\columnwidth = 3.5 in =
252 pt), so LaTeX includes it unscaled. Steps:
  1. inject `@page { size: <w> <h>; margin: 0 }` from the svg's width/height into a temporary copy of the page;
  2. google-chrome --headless --disable-gpu --no-pdf-header-footer --print-to-pdf=...;
  3. assert one page, then pdfcrop;
  4. assert with pdffonts that every font is embedded and none is Type 3 (Chrome turns the CFF Nimbus Roman into
     Type 3; the prototypes therefore list Liberation Serif, Times-metric TrueType, first);
  5. pdftoppm a PNG preview (git-ignored).
Usage (from anywhere):  python3 scripts/html2pdf.py fig_dram_pim [fig_tile ...]   (no argument = every prototype)
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SRC = os.path.join(REPO, "figs", "src")
OUT = os.path.join(REPO, "figs")
CHROME = shutil.which("google-chrome") or shutil.which("chromium")


def svg_size(html):
    m = re.search(r"<svg\b[^>]*?\bwidth=\"([\d.]+)pt\"[^>]*?\bheight=\"([\d.]+)pt\"", html, re.S)
    assert m, "the prototype's <svg> needs width=\"..pt\" height=\"..pt\""
    return float(m.group(1)), float(m.group(2))


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, f"{cmd[0]} failed:\n{r.stdout}\n{r.stderr}"
    return r.stdout


def convert(name):
    src = os.path.join(SRC, name + ".html")
    html = open(src, encoding="utf-8").read()
    w, h = svg_size(html)
    page = f"<style>@page {{ size: {w}pt {h}pt; margin: 0 }} html, body {{ margin: 0; padding: 0 }}</style>"
    html = html.replace("</head>", page + "\n</head>", 1)
    pdf = os.path.join(OUT, name + ".pdf")
    with tempfile.TemporaryDirectory() as tmp:
        page_path = os.path.join(tmp, name + ".html")
        open(page_path, "w", encoding="utf-8").write(html)
        raw = os.path.join(tmp, "raw.pdf")
        run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--user-data-dir={tmp}/profile",
             f"--print-to-pdf={raw}", "file://" + page_path])
        pages = int(re.search(r"Pages:\s+(\d+)", run(["pdfinfo", raw])).group(1))
        assert pages == 1, f"{name}: Chrome printed {pages} pages (svg larger than its @page?)"
        run(["pdfcrop", raw, pdf])
    fonts = run(["pdffonts", pdf]).splitlines()[2:]
    assert fonts, f"{name}: no fonts in the PDF"
    for line in fonts:
        cols = line.split()
        emb = cols[-5]  # name type [encoding] emb sub uni object ID
        assert emb == "yes", f"{name}: font not embedded: {line}"
        assert "Type 3" not in line, f"{name}: Type 3 font (list a TrueType face such as Liberation Serif first): {line}"
    run(["pdftoppm", "-r", "200", "-png", "-singlefile", pdf, os.path.join(OUT, name)])
    print(f"wrote {pdf} ({w:g} x {h:g} pt; {len(fonts)} fonts, all embedded) and {name}.png")


def main():
    names = sys.argv[1:] or sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(SRC, "*.html")))
    for n in names:
        convert(n)


if __name__ == "__main__":
    main()
