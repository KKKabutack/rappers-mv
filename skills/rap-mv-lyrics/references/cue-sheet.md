# Cue sheet — format, alignment, treatments

The cue sheet is the single source of truth for rendering. One JSON file per
song, produced by `helpers/make_cue_sheet.py` (from ASR) or
`helpers/from_ctl.py` (from human-tapped CatchTheLyrics timings) plus a lyrics
text file.

## Timing sources

Both producers read the same `lyrics.txt` and write the same `cues.json`, so
the renderer is indifferent to which one ran.

| Source | Producer | Cue starts | Cue ends |
|---|---|---|---|
| CatchTheLyrics (human-tapped) | `from_ctl.py song.json lyrics.txt` | exactly where the user pressed Enter | ASR phrase end with `--transcript`; otherwise character-count estimate |
| Word-level ASR | `make_cue_sheet.py transcript.json lyrics.txt` | matched ASR word boundary, −30 ms | matched ASR word end, +80 ms |

CatchTheLyrics exports one timestamp per pasted line — line-level only, with
no end times and no word timings:

```json
{
  "version": 1,
  "tool": "catch-the-lyrics",
  "media": "song.mp3",
  "offset": -0.2,
  "lines": [
    {"text": "I'm killing it", "time": 3.71},
    {"text": "I'm pushing it", "time": 4.45}
  ]
}
```

Times already include the tool's global offset, so `from_ctl.py` applies no
arithmetic — it maps each tapped row onto a display line. Paste each stacked
line on its own row and every line gets its own human-exact onset; paste a
stacked cue on one row and the adapter keeps the cue, gives line 2 line 1's
onset, and warns.

Estimated ends (no transcript) use `0.32 s` per CJK char plus `0.14 s` per
Latin char, clamped to 0.4–4.0 s and truncated 0.1 s before the next onset.
They keep captions off instrumental gaps but are approximate — pass
`--transcript` when a word-level transcript exists.

## Lyrics text format (`lyrics.txt`)

One cue per line. Blank lines and `#` comment lines are ignored. The
annotation syntax:

| Syntax | Meaning |
|---|---|
| `first\|second` | two stacked caption lines (max 2); line 1 gets `setup`, line 2 gets `payoff` |
| `\|payoff line` | leading `\|` marks a single line that IS the payoff, so it renders in the payoff colour |
| `{word}` | lift part of a line into the theme's default span effect (`rhyme`) |
| `{word:name}` | lift into a named effect from `theme.effects` |
| trailing `*` | tier-2 emphasis cue (`treatment: "3d"`) |
| trailing `**` | tier-3 finale cue (`treatment: "finale"`; grade the footage separately) |
| `@emoji` | attach a sticker, optionally `@👥,line0` or `@👥,line1` to pick the line |
| `SHOUT TO: name` | outro cue |

Span lifts are the tool for rhyme emphasis. Two bars that land on the same
rhyme get that rhyme lifted in both, so the pair reads as a pair:
`Ten outta ten | I'm {killing} it` and `That girl so bad | I'm {pushing} it`.
Those words can then carry a different fill, glow, stroke, or shadow than the
rest of the line. Braces are stripped before alignment and rendering, so they
never reach the screen.

Spans apply to `caption` cues. The `3d`, `finale`, and `shout` tiers render the
whole line in one treatment by design, so a span inside them has no effect —
keep braces out of those cues.

Example cue sheet source (English-heavy track; nearly every bar needs two
stacked lines to fit the usable width):

```text
My bros ten|toes down
My rap goes|outta the town
No cap I ain't|no {faking} it @🏙
At the right spot,|I'm {making} it
Ten outta ten|I'm {killing} it*
That girl so bad|I'm {pushing} it
Put in work hustle|忘记礼拜几
搞点穿搭|今天买点纪梵希
I see that bag|I'm getting it**
SHOUT TO: CREW
```

A mixed-language bar like `Put in work hustle 忘记礼拜几` is the hard case: no
two-way split fits both halves, so it becomes two cues. A measurement pass shows
this; the operator decides which side gives way.

The `SHOUT TO:` outro gets its own smaller type size, so its text is measured
against a larger budget than a caption line — a name that would overflow as a
caption can be fine there.

- A line must fit the usable width (canvas minus both margins). Run
  `helpers/check_fit.py lyrics.txt` — it measures with the real font and reports
  each line's width, share of the budget, and pixels over. Where to break an
  overlong line is the operator's call; the tool does not propose splits. Counts
  are a poor proxy anyway: mixed CJK/Latin lines advance at very different rates,
  and the cap shifts with `theme.scale` and `margin_pct`.
- Choose emoji from THIS song's own imagery (`style-soul.md` P5).
- Sticker rendering mode comes from `theme.sticker.mode`
  (`silhouette`/`duotone`/`color`/`none`) and is overridable per cue.

## Alignment algorithm (what make_cue_sheet.py does)

1. Normalize: strip punctuation/spaces from each lyric line; same for the
   ASR word stream (concatenate all words with timestamps into one char
   stream with per-char times).
2. Walk cues in order with a cursor. For each cue, slide a window over the
   remaining char stream, score by matched chars (longest-common-subsequence
   ratio; ASR mis-hears mean exact match is wrong — expect ≥60% similarity
   on the best window). Take the best window within a max lookahead of
   3× the cue's char count.
3. Cue start = start of first matched char (minus 30ms pad), end = end of
   last matched char (plus 80ms pad), clamped ≥ 400ms duration.
4. Unmatched cues: flag `"aligned": false`, estimate start at cursor with
   0.32s/char duration, and **report them** — the operator fixes these by
   hand in cues.json before rendering. Never silently ship unaligned cues.
5. For two-line cues, split at the `|`: find line 2's first char inside the
   matched window to get its onset (`line_starts`). This is what makes
   line 2 appear on its own sung onset.

## Matching algorithm (what from_ctl.py does)

1. Flatten the lyric cues to ordered `(cue, line)` slots, normalized the same
   way.
2. Walk the tapped rows in time order (CatchTheLyrics re-sorts on export)
   against those slots, keeping a cursor. A row takes the first slot whose
   text matches exactly; failing that, the best LCS match ≥ 0.60.
3. A row that matches no single line is retried against each cue's joined
   lines — this keeps a stacked cue whose two lines were typed on one row,
   gives line 2 line 1's onset, and warns.
4. Slots with no tapped row are listed as unaligned rather than dropped.
5. End times: ASR phrase end if `--transcript` was passed, otherwise the
   character-count estimate described under Timing sources.

## cues.json schema

Top-level optional `theme` block sets the style for the whole song (full
schema + dial semantics: `style-soul.md` §3; ready-made presets:
`presets.md`). Every field falls back to the measured flex-golden default,
so an absent theme reproduces the reference look exactly. The renderer also
accepts `--theme-file theme.json` and single-dial CLI flags, which merge
over the file's theme.

```json
{
  "version": 1,
  "fps": 60,
  "canvas": [1080, 1920],
  "audio_ref": "song.wav",
  "theme": {
    "name": "melodic-emo",
    "setup": "#F2EDE2", "payoff": "#7FB4E0", "accent": "#8E2B3E",
    "glow": {"color": "#FFFFFF", "radius_pct": 0.018, "strength": 0.8},
    "shadow_alpha": 90,
    "stroke": {"color": "#1A1A1A", "width_px": 4},
    "sticker": {"mode": "duotone", "tint": "#D8CFC2"},
    "motion": "fade",
    "scale": 0.92,
    "band": 0.53, "margin_pct": 0.057, "line_gap": 1.18,
    "materials": {"ice": {"face": "#BFE3FF", "side": "#4A6E8E"}}
  },
  "cues": [
    {
      "start": 3.71, "end": 5.58,
      "lines": ["Ten outta ten", "I'm killing it"],
      "line_starts": [3.71, 4.45],
      "colors": ["#FFFFFF", "#EDEE19"],
      "spans": [{"text": "killing", "effect": "rhyme", "line": 1}],
      "treatment": "caption",
      "emoji": [{"char": "🏙", "line": 0, "scale": 1.35,
                 "style": "duotone", "tint": "#D8CFC2"}],
      "motion": "fade",
      "aligned": true
    },
    {
      "start": 5.75, "end": 6.47,
      "lines": ["I see that bag"],
      "line_starts": [5.75],
      "treatment": "3d",
      "material": "gold",
      "enter": "bottom", "enter_dur": 0.35,
      "aligned": true
    },
    {
      "start": 19.81, "end": 21.05,
      "lines": ["Faking it", "till I'm making it"],
      "treatment": "finale",
      "aligned": true
    }
  ],
  "unaligned": []
}
```

Fields the renderer actually reads: `start`, `end`, `lines`, `line_starts`,
`colors` (per-cue palette override, hex strings), `payoff_only` (set by the
producer from a leading `|`; single line renders in payoff colour),
`treatment` (`caption` | `3d` | `finale` | `shout`; the legacy value `red` is
still accepted as an alias for `finale`), `motion` (per-cue `hardcut` |
`fade`, default from theme), `material` (built-in
`gold|silver|chrome-red|olive` or any `theme.materials` key), `enter`
(`bottom|right|scale`), `enter_dur`, `emoji[]` (`char`, `line`, `scale`,
`style` override, `tint` override), `aligned`. A `timing` block recording the
source is written by `from_ctl.py` and ignored by the renderer.

## Timing rules

- Cue edges sit on matched word boundaries or a tapped onset; pad
  −30 ms/+80 ms on ASR-derived edges.
- Never overlap two regular captions; tier-2 3D cues MAY overlap a caption by
  ≤0.5 s (the reference does).
- Minimum cue duration 400 ms; merge shorter neighbours instead.
- Cue cut-out = min(next cue start, vocal phrase end). Cut captions out at
  phrase end rather than holding them over silent gaps > 0.5 s.
- After cutting or concatenating footage, rebase times:
  `output_time = source_time - segment_start + offset`.
