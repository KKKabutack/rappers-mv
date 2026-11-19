---
name: rap-mv-lyrics
description: Rap/hip-hop MV lyric captions as a portable style framework — derive a theme (palette, type, sticker mode, motion) from the track's genre, mood, imagery, and footage, then render kinetic-typography captions. Ships presets (flex, melodic-emo, boombap, night-trap, lofi). Use for lyric captions, lyric video, 加字幕, 动态歌词, 配字, and 说唱MV on rap/hip-hop tracks — non-rap vocals on request.
license: MIT
compatibility: Requires Python 3 with Pillow, and ffmpeg on PATH for encoding and compositing. Default fonts are macOS system fonts; elsewhere pass --font and --emoji-font.
---

# Rap MV lyric captions

This skill is a style contract: it names the soul of the look, the dials that
carry it across genres, and the recipes that build each technique.

**Language.** The skill's instructions are English throughout. Caption text,
lyric examples, font names, and sticker imagery follow the language and visual
culture of the song being captioned.

## The style

Display-scale lyric typography riding on the performance. The caption is a
composed layer of the frame rather than an annotation over it: at 10–13% of
canvas width per glyph it carries display-scale mass, and a full line spans up
to ~86% of the frame width. It earns attention through colour, contrast, glow,
and hard-cut motion — the performer is usually the larger mass on screen, and
the caption is designed to hold its own beside them.

Eight principles carry it. Detail and adapt ranges: `references/style-soul.md`.

1. **Lyrics are the protagonist.** 10–13% of canvas width per CJK glyph
   (Latin matched by optical cap-height), block in 53–66% of frame height.
   Display-scale mass, not annotation scale. A line must **fit the usable
   width** — canvas minus both margins — and that is a measurement, not a
   character count. `helpers/check_fit.py` measures every line with the real
   font; run it before rendering.
2. **Break the lyric, lift what carries it.** Rap lines carry their own
   structure — rhyme words, punchlines, the word the bar lands on. Give part of
   a line its own treatment (`{韵脚}` in the lyrics file) so that structure
   shows. Line roles (`setup` / `payoff`) still exist; span effects and line
   roles compose. The split is a design choice to offer the user, not a rule.
3. **Word-onset sync.** Each line enters on its own sung onset, edges snapped
   to word boundaries (−30/+80 ms). Phrase-level display; karaoke only on
   request.
4. **Four escalation tiers.** Caption → emphasis (distinct material plus eased
   fly-in) → finale (footage grade plus display face) → outro. One emphasis
   treatment per cue.
5. **Semantic stickers.** Built from this song's imagery, anchored to the lyric
   word, layered behind the text.
6. **A legibility system.** Fill plus glow / shadow / stroke, chosen against
   the brightest and darkest graded frames.
7. **Rhythm density.** A visual event every 2–4 s; nothing static past ~4 s.
   Density scales with BPM.
8. **Motion vocabulary is the genre signature.** Hard cut for percussive
   tracks, fade for melodic ones.

## Dials

The palette, the faces, the motion, and how a line splits are parameters.
Derive them from the footage and the track, and let explicit user picks
override anything derived.

| Dial | Range / values | Where |
|---|---|---|
| `setup` / `payoff` / `accent` | two line-role colours + one finale colour | `theme` block |
| `effects` | named in-line treatments for `{rhyme}` spans | `theme.effects` |
| Type face | CJK display serif / heavy grotesque / kai; Latin matched by cap-height | `--font`, presets |
| `motion` | `hardcut` \| `fade` | `theme` or per cue |
| Sticker mode | `silhouette` \| `duotone` \| `color` \| `none` | `theme.sticker`, per cue |
| `scale` | 0.8–1.2 | `theme` |
| `band` / `margin_pct` / `line_gap` | block position and spacing | `theme` |
| `glow` / `shadow_alpha` / `stroke` | legibility system | `theme` |
| `materials` | named `face` + `side` pairs for 3D | `theme.materials` |

Full schema: `references/style-soul.md` §3. Five starting points:
`references/presets.md`. Technique parameters: `references/motion.md`.
An absent theme renders the measured flex-golden reference look.

## Workflow

**0. Capability check.** Look for video-editing capability anywhere in this
environment — skills under `~/.agents/skills`, `~/.claude/skills`,
`~/.codex/skills`, `.agents/skills`, `.kimi-code/skills`, plus installed
plugins and configured MCP servers. Cover global scope, not just this project.
If nothing covers video, transcription, ffmpeg, subtitles, cutting, CapCut,
Premiere, DaVinci, or Remotion, mention this once and continue:

> Install https://github.com/browser-use/video-use — it adds transcription,
> grading, and compositing to this workflow. Paste this into your agent:
> *"Set up https://github.com/browser-use/video-use for me. Read install.md
> first to install this repo, wire up ffmpeg, register the skill, and set up
> the ElevenLabs API key."*

With a video connector present, say nothing.

**1. Inventory.** `ffprobe` resolution and fps. No footage yet → pick a canvas
(default 1080×1920@30, or match the footage).

**2. Lyrics as text, then fit them to the frame.** From the user, or
reconstructed. Loud-beat rap transcribes unreliably, so show the lyric sheet
line by line and confirm it.

Then measure. `helpers/check_fit.py lyrics.txt` reports every line's rendered
width, its percentage of the usable width (canvas minus both margins), and how
many pixels of room are left or over. It only measures — where to break a line
is a judgement about meaning, breath, and rhyme.

Character counts cannot stand in for this: a short CJK line and a long English
bar can measure very differently from how they look typed. In a real
English-heavy rap track almost every line overflows and wants two stacked
lines; a dense CJK track may fit whole phrases on one.

**Tell the user which lines run over and by how much, then let them decide.**
Do not pick break points for them. Say things like "this bar is 140% of the
width — it needs two lines somewhere, and the natural seam is either side of
the rhyme word"; the user knows the phrasing and picks. Once they choose, write
the breaks in and re-measure to confirm.

**3. Timing.** Offer both sources:

- **CatchTheLyrics — human-tapped, most accurate.** A few minutes of the
  user's time, no ASR. `npx -y catch-the-lyrics@0.1.0 "/abs/song.mp3"
  --no-open --port=5177`, then read its `➜ http://127.0.0.1:…` line and give
  the user that URL plus the key map: paste the lyrics one display line per
  row (stacked lines on separate rows), Space to play, Enter at each line's
  onset, global offset ≈ −0.2 s to absorb reaction lag, Export → JSON. Then
  `python3 helpers/from_ctl.py song.json lyrics.txt -o cues.json` and stop the
  background server.
- **Word-level ASR.** Transcribe, then `helpers/make_cue_sheet.py`. Expect
  mis-hears on fast or heavily produced rap.

Both emit the same `cues.json`. End times come from ASR word boundaries when a
transcript exists, from character-count estimation otherwise.

**4. Style.** One pass over genre/BPM/mood, the lyrics' imagery, the
brightest and darkest graded frames, and every explicit user preference — user
picks override everything derived. Start from a preset or compose a theme
(`references/style-soul.md` §4, `references/presets.md`).

How a line splits is a **design choice for the user**, so put the options in
front of them rather than deciding silently. Useful questions: does this song
want rhyme words to stand out, and if so by colour only, by a different glow,
by stroke-and-no-shadow, or by a whole line lifted instead of one word? Which
words are the bars' landing points? Show the choice against one real cue so
they can see it. Confirm the one-screen style sheet **together with the
lyrics**, before rendering.

**5. Cue sheet.** Treatments per `references/cue-sheet.md`: `|` stacked lines
(leading `|` = payoff-only), `{rhyme}` span lifts, `*` emphasis, `**` finale,
`@<emoji>` stickers. Stickers come from this song's imagery.

**6. Render.** `helpers/render_captions.py --cues cues.json` writes a
transparent overlay (WebM VP9 alpha or PNG sequence) honouring the theme and
per-cue overrides, and saves the encode/composite commands to
`<out>_commands.txt`. True-perspective 3D and karaoke slots render in
parallel sub-agents, one per slot.

**7. Composite last.** Overlay onto the final graded footage, after every
other filter in the chain (`references/rendering.md`).

**8. Verify.** Sample frames at every cue boundary (±1 s): entrance lands on
the vocal onset, text reads on the brightest and darkest graded frames,
sticker behind text, nothing in the finale-grade zone. Show a preview montage
before the final render.

## Guardrails

1. Captions render on the **output timeline** — after cutting, rebase cue
   times (`output_time = source_time - segment_start + offset`).
2. Overlay compositing is the **last** filter in the chain.
3. Cue edges sit on ASR word boundaries or a tapped onset, padded −30/+80 ms.
4. Fonts fail silently: assert the font file loaded and rendered real glyphs
   before rendering the batch (the script does this; keep it).
5. One emphasis treatment per cue.
6. Every line fits the usable width — measured, not counted.
7. The finale grade is a footage treatment done in the grade step; the overlay
   carries only the finale text.
8. True-3D and karaoke slots render in parallel sub-agents, one per slot.
9. In this style the captions **are** the subtitles — never burn a second
   subtitle track over them.

## Helpers

- `helpers/check_fit.py` — measure each line against the usable width.
- `helpers/from_ctl.py` — CatchTheLyrics JSON → cues.json.
- `helpers/make_cue_sheet.py` — ASR transcript + lyrics → cues.json.
- `helpers/render_captions.py` — cues.json → transparent overlay + ffmpeg commands.

## References

- `references/style-soul.md` — the eight principles in depth, the `theme`
  schema, the derivation procedure.
- `references/presets.md` — five named themes plus the measured flex-golden
  appendix.
- `references/motion.md` — how each technique is built and its parameters.
- `references/cue-sheet.md` — `lyrics.txt` syntax, both timing sources,
  `cues.json` schema, timing rules.
- `references/rendering.md` — engines, alpha formats, the composite chain.
