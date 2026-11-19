#!/usr/bin/env python3
"""make_cue_sheet.py — align lyric lines to word-level timestamps.

Optional path. CatchTheLyrics (helpers/from_ctl.py) is the default timing
source and needs no ASR; use this script when a word-level transcript already
exists and you want cue ends snapped to real word boundaries.

Usage:
    python3 make_cue_sheet.py transcript.json lyrics.txt -o cues.json \
        [--fps 60] [--canvas 1080x1920] [--audio-ref song.wav]

transcript.json: any object with a top-level "words" array of
{"text", "start", "end"} in seconds. Optional "type": "spacing" entries are
skipped. Most word-level ASR exports can be reshaped to this in a line or two.

lyrics.txt format: see references/cue-sheet.md in this skill (| splits stacked
lines, {word} lifts a rhyme span, trailing * / ** mark emphasis, @<char>
attaches emoji, "SHOUT TO: x" marks outro).

Unaligned cues are reported and flagged "aligned": false — fix them by hand
in cues.json before rendering. Prints a table of all cues when done.
"""
import argparse, json, re, unicodedata
from pathlib import Path

PAD_IN, PAD_OUT = 0.03, 0.08
MIN_DUR = 0.40
CHARS_PER_SEC_FALLBACK = 3.1  # typical Chinese rap delivery

PUNCT = re.compile(r"[\s。．.,，、!！?？;；:：'\"“”‘’（）()《》<>\[\]【】…—\-_.。〇]")

def read_json(raw):
    p = Path(raw).expanduser().resolve(strict=True)
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def read_lyrics(raw):
    p = Path(raw).expanduser().resolve(strict=True)
    with open(p, encoding="utf-8") as f:
        return f.read().splitlines()

def norm(s):
    """Normalize for matching: strip punct, fullwidth→ascii-ish, lower."""
    s = unicodedata.normalize("NFKC", s)
    s = PUNCT.sub("", s)
    return s.lower()

def build_char_stream(words):
    """Concat word texts into (chars, starts, ends); skip spacing tokens."""
    chars, starts, ends = [], [], []
    for w in words:
        if w.get("type") == "spacing":
            continue
        t = norm(w["text"])
        if not t:
            pass  # keep position mapping, zero-length contributes nothing
        n = len(t) or 1
        for i, ch in enumerate(t):
            chars.append(ch)
            starts.append(w["start"] + (w["end"] - w["start"]) * i / n)
            ends.append(w["start"] + (w["end"] - w["start"]) * (i + 1) / n)
    return chars, starts, ends

def lcs_ratio(a, b):
    """Similarity of short pattern a inside window b (order-sensitive)."""
    if not a:
        return 0.0
    m, n = len(a), len(b)
    prev = [0] * (n + 1)
    best = 0
    for i in range(1, m + 1):
        cur = [0] * (n + 1)
        ca = a[i - 1]
        for j in range(1, n + 1):
            if ca == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best = cur[j]
            else:
                cur[j] = max(cur[j - 1], prev[j])
        prev = cur
    return best / m

def find_sub(seq, sub, min_pos):
    """Index in seq where sub starts (allowing gaps), searching after min_pos."""
    for i in range(max(min_pos, 0), len(seq)):
        j, k = i, 0
        while j < len(seq) and k < len(sub):
            if seq[j] == sub[k]:
                k += 1
            j += 1
        if k == len(sub):
            return i
    return max(min_pos, 0)

SPAN_RE = re.compile(r"\{([^{}]*)\}")

def extract_spans(body):
    """Pull {rhyme} / {rhyme:effect} markers out of a line.

    Returns (clean_text, spans) where spans are [{"text":..., "effect":...}]
    in text order. `{对策}` uses the theme's default span effect; `{对策:alt}`
    names an entry in theme.effects. Braces are stripped from the rendered line.
    """
    spans = []
    def take(m):
        inner = m.group(1)
        text, _, eff = inner.partition(":")
        text = text.strip()
        if text:
            spans.append({"text": text, "effect": (eff.strip() or "rhyme")})
        return text
    return SPAN_RE.sub(take, body), spans

def parse_lyrics(lines):
    cues = []
    for line in lines:
        if not line.strip() or line.strip().startswith("#"):
            continue
        cue = {"lines": [], "emoji": [], "treatment": "caption"}
        m = re.search(r"@(\S+?)(?:,line([01]))?(?=\s|$)", line)
        if m:
            cue["emoji"] = [{"char": m.group(1), "line": int(m.group(2) or 0),
                             "scale": 1.35}]
            line = line[:m.start()] + line[m.end():]
        if line.strip().startswith("SHOUT TO:"):
            cue["treatment"] = "shout"
            cue["lines"] = [line.split("SHOUT TO:", 1)[1].strip()]
        else:
            body = line.rstrip("*")
            stars = len(line) - len(body)
            if stars >= 2:
                cue["treatment"] = "finale"
            elif stars == 1:
                cue["treatment"] = "3d"
            # a leading | marks a payoff-only single line (payoff color)
            if body.lstrip().startswith("|"):
                cue["payoff_only"] = True
            raw_lines = [p.strip() for p in body.split("|") if p.strip()]
            spans = []
            clean = []
            for li, raw in enumerate(raw_lines):
                text, found = extract_spans(raw)
                clean.append(text)
                for sp in found:
                    spans.append({**sp, "line": li})
            cue["lines"] = clean
            if spans:
                cue["spans"] = spans
        cues.append(cue)
    return cues

def align(cues, chars, starts, ends):
    out, cursor, unaligned = [], 0, []
    for cue in cues:
        pat = norm("".join(cue["lines"]))
        if not pat:
            continue
        win = min(len(pat) * 3, max(1, len(chars) - cursor))
        best_r, best_i = 0.0, None
        for i in range(cursor, max(cursor + 1, cursor + win - len(pat) + 1)):
            r = lcs_ratio(pat, chars[i:i + len(pat) + 2])
            if r > best_r:
                best_r, best_i = r, i
        if best_i is None or best_r < 0.55:
            est_start = starts[cursor] if cursor < len(starts) else 0.0
            dur = max(MIN_DUR, len(pat) / CHARS_PER_SEC_FALLBACK)
            out.append({**cue, "start": round(est_start, 3),
                        "end": round(est_start + dur, 3),
                        "line_starts": [est_start] * len(cue["lines"]),
                        "aligned": False, "match": round(best_r, 2)})
            unaligned.append(" | ".join(cue["lines"]))
            continue
        # split window per line to find line 2's sung onset
        seg = chars[best_i:best_i + len(pat) + 2]
        line_starts, acc = [], 0
        for li, ltext in enumerate(cue["lines"]):
            lnorm = norm(ltext)
            if li == 0:
                line_starts.append(starts[best_i])
            else:
                idx = find_sub(seg, lnorm, acc)
                ci = min(best_i + idx, len(starts) - 1)
                line_starts.append(starts[ci])
            acc += len(lnorm)
        st = max(0.0, starts[best_i] - PAD_IN)
        end_i = min(best_i + len(pat) - 1, len(ends) - 1)
        en = ends[end_i] + PAD_OUT
        if en - st < MIN_DUR:
            en = st + MIN_DUR
        cursor = best_i + len(pat)
        out.append({**cue, "start": round(st, 3), "end": round(en, 3),
                    "line_starts": [round(s, 3) for s in line_starts],
                    "aligned": True, "match": round(best_r, 2)})
    return out, unaligned

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript")
    ap.add_argument("lyrics")
    ap.add_argument("-o", "--out", default="cues.json")
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--canvas", default="1080x1920")
    ap.add_argument("--audio-ref", default="")
    a = ap.parse_args()

    words = read_json(a.transcript)["words"]
    cues = parse_lyrics(read_lyrics(a.lyrics))
    chars, starts, ends = build_char_stream(words)
    aligned, unaligned = align(cues, chars, starts, ends)

    w, h = a.canvas.lower().split("x")
    doc = {"version": 1, "fps": a.fps, "canvas": [int(w), int(h)],
           "audio_ref": a.audio_ref,
           "cues": aligned, "unaligned": unaligned}
    out = Path(a.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{'start':>7} {'end':>7} {'match':>6}  lines")
    for c in aligned:
        flag = "" if c["aligned"] else "  <-- FIX BY HAND"
        print(f"{c['start']:7.2f} {c['end']:7.2f} {c['match']:6.2f}  "
              f"[{c['treatment']}] " + " | ".join(c["lines"]) + flag)
    if unaligned:
        print(f"\nWARNING: {len(unaligned)} cue(s) not matched — "
              f"edit the cues file by hand before rendering.")
    print(f"\nwrote {out} ({len(aligned)} cues)")

if __name__ == "__main__":
    main()
