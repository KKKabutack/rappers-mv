#!/usr/bin/env python3
"""check_fit.py — measure every lyric line against the caption's usable width.

Any fixed "chars per line" cap in the docs is a consequence, not a rule: a line
fits when its rendered advance is under the canvas width minus both margins.
Character counts do not predict that, because a Latin run advances roughly half
a glyph per character — a long English bar and a short CJK phrase can look
similar typed and measure very differently. The cap also moves with the theme's
`scale` and `margin_pct`.

This tool reports measurements only. Where to break a line is a judgement about
meaning, breath, and rhyme, so it stays with the operator.

Usage:
    python3 check_fit.py lyrics.txt [--theme-file theme.json] [--font path.ttc] \
        [--canvas 1080x1920] [--scale 1.0] [--margin-pct 0.057]

Exit code is 0 when every line fits, 1 when any line overflows — so an agent
can gate rendering on it.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_cue_sheet import parse_lyrics, read_lyrics  # noqa: E402
from render_captions import (  # noqa: E402
    has_cjk,
    pick_cjk,
    pick_latin,
    text_size,
)

SIZE_PCT = 0.123  # renderer's caption size as a fraction of canvas width


def measure(text, cjk, latin):
    font = cjk if has_cjk(text) else latin
    return text_size(font, text)[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lyrics")
    ap.add_argument("--theme-file")
    ap.add_argument("--font")
    ap.add_argument("--canvas", default="1080x1920")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--margin-pct", type=float, default=None)
    a = ap.parse_args()

    W = int(a.canvas.lower().split("x")[0])
    scale, margin = a.scale, a.margin_pct
    if a.theme_file:
        import json
        doc = json.loads(Path(a.theme_file).expanduser().read_text(encoding="utf-8"))
        th = doc.get("theme", doc)
        scale = float(th.get("scale", scale))
        margin = float(th.get("margin_pct", margin if margin is not None else 0.057))
    if margin is None:
        margin = 0.057

    size = int(SIZE_PCT * W * scale)
    cjk, latin = pick_cjk(a.font, size), pick_latin(a.font, size)
    usable = W - 2 * int(margin * W)

    cues = parse_lyrics(read_lyrics(a.lyrics))
    over = 0
    print(f"usable width {usable}px  (glyph {size}px, margin {margin:.1%} of {W}px)\n")
    print(f"{'line':40s} {'px':>5s} {'%':>6s} {'room':>7s}  status")
    for cue in cues:
        for line in cue["lines"]:
            w = measure(line, cjk, latin)
            pct = w / usable * 100
            bad = w > usable
            over += bad
            # room = pixels left in the budget; negative means how far it runs over
            room = usable - w
            tag = "OVERFLOW" if bad else ("tight" if pct > 92 else "")
            print(f"{line[:40]:40s} {w:5d} {pct:5.1f}% {room:+7d}  {tag}")

    print()
    if over:
        print(f"{over} line(s) run past the usable width. How to break them is a "
              f"judgement call — split into two stacked lines (`|`) or two cues, "
              f"or lower theme scale / margin.")
        return 1
    print("every line fits.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
