#!/usr/bin/env python3
"""from_ctl.py — build cues.json from CatchTheLyrics human-tapped timings.

CatchTheLyrics (npx catch-the-lyrics) exports one timestamp per pasted lyric
line: {"version":1,"tool":"catch-the-lyrics","media":...,"offset":...,"lines":
[{"text":...,"time":...}]}. Times already include the tool's global offset.

This adapter maps those line timestamps onto the skill's lyric syntax, so
human-tapped timing reaches the renderer with no word-level ASR in the loop.

Usage:
    python3 from_ctl.py song.json lyrics.txt -o cues.json \
        [--transcript scribe.json] [--theme-file theme.json] \
        [--fps 60] [--canvas 1080x1920] [--audio-ref song.wav]

Start CatchTheLyrics with the lyrics' display lines split one per row — then
each stacked caption line (`|` in lyrics.txt) gets its own tapped onset and
`line_starts` needs no estimation at all.

Cue END times: with --transcript, the phrase end is taken from ASR word
boundaries; without it, end = min(next onset - 0.1s, start + 0.32s/char
clamped to 0.4-4.0s). Either way cue starts stay exactly as the user tapped.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_cue_sheet import (  # noqa: E402  (path insert must precede import)
    CHARS_PER_SEC_FALLBACK,
    MIN_DUR,
    PAD_OUT,
    build_char_stream,
    lcs_ratio,
    norm,
    parse_lyrics,
    read_json,
    read_lyrics,
)

MATCH_MIN = 0.60      # LCS ratio accepted as the same line
ASR_MATCH_MIN = 0.55  # same threshold make_cue_sheet.py uses
ASR_LOOKBACK = 8      # chars searched before the tapped onset
LATIN_CHARS_PER_SEC = 7.0  # ~1.4 syllables/s of English rap at ~5 chars/word
TAP_MARKERS = re.compile(r"[|*@]")


def norm_text(s):
    """Normalize a lyric line for matching, dropping the skill's own markers."""
    return TAP_MARKERS.sub("", norm(s))


def ctl_lines(doc):
    """Validate a CatchTheLyrics export and return [(text, time)] by time order."""
    if doc.get("tool") != "catch-the-lyrics":
        raise SystemExit(
            f"not a CatchTheLyrics export (tool={doc.get('tool')!r}); "
            "expected the Export > JSON file from the CatchTheLyrics web UI"
        )
    rows = []
    for ln in doc.get("lines", []):
        text, t = ln.get("text"), ln.get("time")
        if not isinstance(t, (int, float)):
            raise SystemExit(f"CatchTheLyrics line has no numeric time: {ln!r}")
        if text is None or not str(text).strip():
            continue
        rows.append((str(text), float(t)))
    # CatchTheLyrics re-sorts on export; be explicit about relying on it.
    rows.sort(key=lambda r: r[1])
    return rows


def flatten_slots(cues):
    """Flatten lyric cues to [(cue_idx, line_idx, normalized_text)] in order."""
    slots = []
    for ci, cue in enumerate(cues):
        for li, line in enumerate(cue["lines"]):
            slots.append((ci, li, norm_text(line)))
    return slots


def match_rows(rows, slots, cues):
    """Greedily match time-ordered tapped rows to lyric slots in order.

    Rows normally match one display line each. When a user pastes a stacked
    cue on a single row (both display lines run together), the row matches no
    single line but does match the cue's two lines joined — that cue still gets
    its tapped onset, with later lines inheriting it.

    Returns (slot_times, cue_ratio, joined_only) where slot_times maps
    (cue_idx, line_idx) -> tapped seconds, cue_ratio maps cue_idx -> best
    match ratio, and joined_only holds cue indices matched only as a whole.
    """
    slot_times, cue_ratio, joined_only = {}, {}, set()
    cursor = 0
    for text, t in rows:
        key = norm_text(text)
        if not key:
            continue
        exact = None
        best = None
        for si in range(cursor, len(slots)):
            ci, li, stext = slots[si]
            if stext == key:
                exact = (si, 1.0)
                break
            ratio = lcs_ratio(key, stext)
            if ratio >= MATCH_MIN and (best is None or ratio > best[1]):
                best = (si, ratio)
        # An exact hit anywhere ahead beats a fuzzy one closer to the cursor:
        # CatchTheLyrics re-sorts rows by time, so a typed duplicate can appear
        # later than its lyric position.
        hit = exact or best

        if hit is not None:
            si, ratio = hit
            ci, li, _ = slots[si]
            slot_times[(ci, li)] = t
            cue_ratio[ci] = max(cue_ratio.get(ci, 0.0), ratio)
            cursor = si + 1
            continue

        # Fallback: the row may span a whole (stacked) cue on one line.
        for ci in range(len(cues)):
            if ci < cursor and (ci, 0) not in slot_times:
                continue
            joined = norm_text("".join(cues[ci]["lines"]))
            ratio = 1.0 if joined == key else lcs_ratio(key, joined)
            if ratio >= MATCH_MIN:
                slot_times[(ci, 0)] = t
                cue_ratio[ci] = max(cue_ratio.get(ci, 0.0), ratio)
                if len(cues[ci]["lines"]) > 1:
                    joined_only.add(ci)
                cursor = ci + 1
                break
    return slot_times, cue_ratio, joined_only


def asr_phrase_end(text, start, chars, starts, ends):
    """End of the ASR phrase whose text best matches, searched from `start`."""
    pat = norm_text(text)
    if not pat or not chars:
        return None
    anchor = min(range(len(starts)), key=lambda i: abs(starts[i] - start))
    lo = max(0, anchor - ASR_LOOKBACK)
    hi = min(len(chars), anchor + max(12, 3 * len(pat)))
    best_r, best_i = 0.0, None
    for i in range(lo, hi):
        window = chars[i:min(hi, i + len(pat))]
        ratio = lcs_ratio(pat, window)
        if ratio > best_r:
            best_r, best_i = ratio, i
    if best_i is None or best_r < ASR_MATCH_MIN:
        return None
    return ends[min(best_i + len(pat) - 1, len(ends) - 1)] + PAD_OUT


def estimate_end(text, start, next_start):
    """Fallback duration from character count when no transcript is available.

    CJK and Latin advance at very different rates (a dense CJK bar and a
    same-length English hook are not the same duration), and mixed-language
    lines are the norm in this genre — so count the two scripts separately
    instead of applying one chars/sec rate to both.
    """
    key = norm_text(text)
    cjk = sum(1 for c in key if "\u2e00" <= c <= "\ua000")
    latin = sum(1 for c in key if c.isalpha())
    span = cjk / CHARS_PER_SEC_FALLBACK + latin / LATIN_CHARS_PER_SEC
    span = min(max(span, MIN_DUR), 4.0)
    end = start + span
    if next_start is not None:
        end = min(next_start - 0.1, end)
    return max(end, start + MIN_DUR * 0.75)


def load_theme(raw):
    if not raw:
        return None
    doc = read_json(raw)
    theme = doc.get("theme", doc) if isinstance(doc, dict) else None
    if not isinstance(theme, dict):
        raise SystemExit(f"--theme-file {raw}: expected a theme object or {{\"theme\": {{...}}}}")
    return theme


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ctl", help="CatchTheLyrics JSON export")
    ap.add_argument("lyrics", help="lyrics.txt in the skill's cue syntax")
    ap.add_argument("-o", "--out", default="cues.json")
    ap.add_argument("--transcript", help="optional word-level ASR JSON for cue ends")
    ap.add_argument("--theme-file", help="optional theme JSON copied into cues.json")
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--canvas", default="1080x1920")
    ap.add_argument("--audio-ref", default="")
    a = ap.parse_args()

    cues = parse_lyrics(read_lyrics(a.lyrics))
    rows = ctl_lines(read_json(a.ctl))
    slots = flatten_slots(cues)
    slot_times, cue_ratio, joined_only = match_rows(rows, slots, cues)

    chars, starts, ends = [], [], []
    if a.transcript:
        chars, starts, ends = build_char_stream(read_json(a.transcript)["words"])

    # Cues with no tapped line at all: keep them visible to the operator.
    aligned, unaligned, cursor = [], [], 0.0
    for ci, cue in enumerate(cues):
        lines = cue["lines"]
        if not any((ci, li) in slot_times for li in range(len(lines))):
            unaligned.append({"index": ci, "lines": lines,
                              "reason": "no tapped line matched"})
            continue
        line_starts = []
        for li in range(len(lines)):
            if (ci, li) in slot_times:
                line_starts.append(slot_times[(ci, li)])
                cursor = max(cursor, slot_times[(ci, li)])
            else:
                line_starts.append(line_starts[-1] if line_starts else cursor)
        start = round(line_starts[0], 3)
        text = " ".join(lines)
        end = asr_phrase_end(text, start, chars, starts, ends) if a.transcript else None
        aligned.append({
            **cue,
            "start": start,
            "line_starts": [round(s, 3) for s in line_starts],
            "aligned": True,
            "match": round(cue_ratio.get(ci, 1.0), 2),
            "_end_from_asr": None if end is None else round(end, 3),
            "_text": text,
        })

    # Second pass: end times are only knowable once the next onset is known.
    for i, cue in enumerate(aligned):
        nxt = aligned[i + 1]["start"] if i + 1 < len(aligned) else None
        end = cue.pop("_end_from_asr", None)
        text = cue.pop("_text", " ".join(cue["lines"]))
        if end is None:
            end = estimate_end(text, cue["start"], nxt)
        elif nxt is not None and cue.get("treatment") != "3d":
            end = min(end, nxt)
        cue["end"] = round(max(end, cue["start"] + MIN_DUR), 3)

    # Operator messages for the two ways a hand-tapped sheet usually goes wrong.
    for ci in sorted(joined_only):
        print(f"WARNING: cue {ci} ({' | '.join(cues[ci]['lines'])}) was tapped as "
              f"one row, so line 2 inherits line 1's onset. Paste each stacked "
              f"line on its own row in CatchTheLyrics and re-export.",
              file=sys.stderr)

    w, h = a.canvas.lower().split("x")
    doc = {"version": 1, "fps": a.fps, "canvas": [int(w), int(h)],
           "audio_ref": a.audio_ref,
           "timing": {"source": "catch-the-lyrics",
                      "file": Path(a.ctl).name,
                      "offset": read_json(a.ctl).get("offset")},
           "cues": aligned, "unaligned": unaligned}
    theme = load_theme(a.theme_file)
    if theme:
        doc["theme"] = theme

    out = Path(a.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{'start':>7} {'end':>7} {'match':>6}  lines")
    for c in aligned:
        end_src = "" if a.transcript else "  (estimated end)"
        print(f"{c['start']:7.2f} {c['end']:7.2f} {c['match']:6.2f}  "
              f"[{c['treatment']}] " + " | ".join(c["lines"]) + end_src)
    if unaligned:
        print(f"\nWARNING: {len(unaligned)} cue(s) had no tapped line — "
              f"tap them in CatchTheLyrics or fix cues.json by hand.")
        for u in unaligned:
            print(f"  cue {u['index']}: " + " | ".join(u["lines"]))
    print(f"\nwrote {out} ({len(aligned)} cues, "
          f"{len(unaligned)} unaligned)")


if __name__ == "__main__":
    main()
