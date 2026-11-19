# Rappers MV

Rap and hip-hop music-video craft, packaged as an agent plugin.

One skill today:

| Skill | What it does |
|---|---|
| [`rap-mv-lyrics`](skills/rap-mv-lyrics/SKILL.md) | Kinetic lyric captions — derive a theme from the track and footage, time it to the vocal, render a transparent overlay |

The plugin is a home for this kind of work rather than a single skill. More
rap-MV skills (title cards, beat-synced transitions, cover art) can land in
`skills/` and ship in the same install.

## Install

### ZCode

Add this repository as a plugin marketplace, then install `rappers-mv`:

```
Plugin Marketplace → Add → Add Plugin Marketplace
https://github.com/KKKabutack/rappers-mv
```

Then **Personal → rappers-mv → Install**.

### Claude Code

```
/plugin marketplace add KKKabutack/rappers-mv
/plugin install rappers-mv@rappers-mv
```

### Any other Agent Skills client

The skills follow the [Agent Skills](https://agentskills.io) format — a folder
with `SKILL.md` plus optional scripts and references. Copy or symlink
`skills/rap-mv-lyrics/` into that client's skills directory:

```bash
git clone https://github.com/KKKabutack/rappers-mv ~/Developer/rappers-mv
ln -sfn ~/Developer/rappers-mv/skills/rap-mv-lyrics ~/.agents/skills/rap-mv-lyrics
```

## Requirements

- **Python 3** with **Pillow** — the caption renderer
- **ffmpeg** on `PATH` — encoding the overlay and compositing it
- Fonts: the renderer defaults to macOS system fonts (Songti, Apple Color
  Emoji). On other platforms pass `--font` and `--emoji-font`.

Optional, and detected rather than assumed:

- **CatchTheLyrics** (`npx catch-the-lyrics`) for hand-tapped timing
- A word-level ASR transcript, if you have one, for cue end times

## What the caption skill contains

```
skills/rap-mv-lyrics/
├── SKILL.md              # style contract, dials, 8-step workflow, guardrails
├── helpers/
│   ├── check_fit.py      # measure lines against the usable caption width
│   ├── from_ctl.py       # CatchTheLyrics JSON → cues.json
│   ├── make_cue_sheet.py # ASR transcript + lyrics → cues.json
│   └── render_captions.py# cues.json → transparent overlay + ffmpeg commands
└── references/
    ├── style-soul.md     # the eight principles, theme schema, derivation
    ├── presets.md        # five named themes + a measured reference appendix
    ├── motion.md         # how each technique is built
    ├── cue-sheet.md      # lyrics syntax, timing sources, cues.json schema
    └── rendering.md      # engines, alpha formats, compositing order
```

## Quick start

```bash
# 1. write lyrics (one cue per line; `|` stacks two lines, `{word}` lifts a rhyme)
# 2. time them — either hand-tapped or from ASR
python3 skills/rap-mv-lyrics/helpers/from_ctl.py song.json lyrics.txt -o cues.json
# 3. check every line fits the frame
python3 skills/rap-mv-lyrics/helpers/check_fit.py lyrics.txt
# 4. render the overlay
python3 skills/rap-mv-lyrics/helpers/render_captions.py --cues cues.json -o captions
# 5. composite captions LAST onto graded footage (command is printed and saved)
```

## License

MIT — see [LICENSE](LICENSE).
