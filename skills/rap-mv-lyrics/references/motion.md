# Motion recipes

How each caption technique is built, with working parameter ranges. Every
value here is a starting range measured from real rap MV captions — pick
within it, or go outside it deliberately.

A technique belongs to a tier (`style-soul.md` P4). Tier 1 covers the
regular caption; tier 2 is the emphasis treatment; tier 3 is the finale.

## Engines

| Technique | Engine |
|---|---|
| Hard cut, fade, caption layout, glow / stroke / shadow, sticker compositing | `helpers/render_captions.py` — theme-aware, deterministic, iterates in seconds |
| Pseudo-3D extrusion + velocity blur + RGB fringe | same script (`treatment: "3d"`) |
| Finale text (accent colour, rotation jitter, oversized) | same script (`treatment: "finale"`) |
| True perspective / metallic-material 3D | sub-agent per slot (Remotion or HyperFrames), one cue per agent, in parallel |
| Karaoke word-by-word fill | sub-agent only — the bundled script has no word-level fill |
| Prop sprites (money rain, mic, bag) | separate overlay assets composited in their own pass |

## Hard cut

The caption appears full-size and fully opaque between consecutive frames.
No scale tween, no fade, no slide. Any transition under ~40 ms reads as
instant to the viewer; verify at 24 fps by stepping two frames.

- Enter and exit are both binary, at the cue boundaries.
- Sync is what carries the energy — the cut landing on the vocal onset does
  the work that easing would otherwise do.
- `motion: hardcut` (the default; percussive genres: trap, drill, flex).

## Fade

Lines breathe in over 80–120 ms and hold. Still binary at the exit.

- `motion: fade` — melodic, emo, lofi, bedroom-pop tracks.
- The short 80–120 ms window is the point: long fades read as a video
  slideshow rather than as lyric motion.

## Fly-in (tier-2 entrance)

The only place easing is allowed. The word lands on its own sung onset.

- Direction: from bottom or from the right (`enter: "bottom" | "right" |
  "scale"`).
- Duration: 0.25–0.4 s (`enter_dur`), ease-out landing.
- Hold after landing: 0.8–1.5 s.
- Motion blur along the travel direction and an RGB fringe sell the speed —
  see pseudo-3D below, which applies both automatically.

## Pseudo-3D extrusion

Reads correctly at phone size and costs a fraction of a true 3D render. Try
this before spawning a sub-agent.

- **Extrusion**: stack 6–10 copies of the glyphs offset along one fixed
  diagonal; darken each deeper layer to make the side face. The top copy
  carries a specular gradient.
- **Velocity blur**: during fly-in frames, 4–6 direction-offset pastes with
  alpha decaying linearly (`1.0, 0.8, 0.6, …`).
- **RGB fringe**: red and blue copies channel-shifted by ±0.3% of canvas
  width. Blue and red split in opposite directions along the travel axis.
- **Material**: `face` + `side` colour pair. Define custom pairs under
  `theme.materials`; built-ins are `gold`, `silver`, `chrome-red`, `olive`.
- Text spans 50–90% of canvas width. A 3D cue may overlap a regular caption
  by up to 0.5 s elsewhere in frame.

## Bloom / glow

Every text element is fill **plus** at least one of glow, shadow, or stroke —
that combination is what makes display type survive graded footage.

| Layer | Range | Notes |
|---|---|---|
| Glow radius | 1.5–3% of canvas width | one Gaussian blur per text layer per frame; the expensive operation |
| Glow strength | 0.5–1.2 | above 1.0 the bloom clips toward white |
| Drop shadow | alpha 60–130 | offset ~0.5% width, blur ~1% width; this is what saves white type on bright skies |
| Stroke | 2–6 px | the flat/graphic alternative to glow — pick one, they fight |

A bloom clipping to near-white on the payoff colour **is** the look in
high-energy presets. Keep it.

Derive the combination from the footage: bright backgrounds want
shadow/stroke, dark backgrounds want glow. Verify on the brightest and
darkest graded frames before rendering the batch.

## Stickers

Semantic pictograms anchored to a lyric word, layered **behind** the caption
text, entering and exiting with their cue. The set comes from the song's own
imagery — see `style-soul.md` P5 for how to build it.

- Size 1.2–1.5× glyph height.
- Position overlapping the end of the semantic word's line.
- At most roughly one per 1–2 cues.
- Modes: `silhouette` (flat white fill + glow), `duotone` (tinted to a
  palette colour), `color` (original emoji art), `none`.
- High-energy looks can pulse the bloom intensity subtly while the cue holds.

## Finale text (tier 3)

Oversized display type in `theme.accent`, ~1.5× caption size, stacked in
short lines, per-character rotation jitter within ±3°. No glow, no stickers.
Holds ~1.5 s.

The footage grade (B&W, bleach, freeze, negative) happens in the **grade
step** — this overlay carries only the text.

## Outro signature

Artist card / shout-out block in Roman serif caps, white with a thin dark
outline and slight glow, ~8% canvas width cap-height, single line,
left-of-centre around 58% height, hard cut-in. The final scene is darkened
to ~40% brightness under it.

## Rhythm

One visual event every 2–4 s — a caption switch counts, as do stickers,
emphasis landings, and transitions. Density tracks energy: 140+ BPM wants
the fast end, boom-bap and melodic tracks can breathe. Nothing holds static
past ~4–5 s.

## Verification

Sample frames at every cue in-point (+1 frame), every second-line onset, and
two random hold frames. Check the entrance lands on the onset, the text reads
on both the brightest and darkest graded frames, the sticker sits behind the
text, and no caption appears inside the finale-grade zone.
