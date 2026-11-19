# Style soul — the portable DNA of rap MV lyric captions

This layer transfers across genres, moods, footage, and users. Everything
concrete — colours, fonts, emoji sets, easing — is a **dial** with a range,
set per song. `presets.md` holds ready-made dial settings; its appendix holds
a full measurement of one preset (flex-golden) as a worked example of the
method.

## 1. What transfers

| The soul (always true) | The skin (set per song) |
|---|---|
| Lyrics are the protagonist | exact palette |
| Setup/payoff semantic mapping | which two colours realize it |
| Word-onset sync, phrase-level display | motion vocabulary (hardcut/fade) |
| Escalation tiers: caption → emphasis → finale → outro | what each tier looks like |
| Semantic stickers anchored to lyric words, behind text | sticker set + rendering mode |
| A legibility system per footage | glow vs outline vs shadow combo |
| Rhythm density: regular visual events | event interval, by genre/BPM |
| Restraint: one emphasis per cue | — |

Technique parameters for the skin column live in `motion.md`.

## 2. The eight principles

### P1 — Lyrics are the protagonist
Caption type is display-scale: 10–13% of canvas width per CJK glyph (Latin
matched by optical cap-height). A full line spans up to ~86% of frame width, so
the caption reads as a composed layer of the frame rather than an annotation
over it.

Line length is a **width budget, not a character count**. A line fits when its
rendered advance is under the canvas width minus both margins. At the default
scale and 5.7% margins that works out to about 7 CJK glyphs — but the number
moves with `scale` and `margin_pct` (scale 0.8 admits ~9, scale 1.2 admits ~6),
and mixed CJK/Latin lines break any count-based rule entirely: a Latin run
advances roughly half a glyph per character. Measure with the real font via
`helpers/check_fit.py`; split what overflows into two stacked lines or two cues,
or lower the theme scale.

The hierarchy comes from treatment, not area: a two-line block covers ~12% of
the canvas, and a performer framed mid-shot covers far more. The caption holds
attention through colour, contrast, glow, and motion landing on the beat.

*Range:* minimal presets sit at 8–9%, maximal ones at 13%+. Below ~7% the
type reads as a small safe-area label and the style collapses.

### P2 — Break the lyric, lift what carries it
A caption does not have to be one uniform treatment across the whole line.
Rap lyrics carry their own structure — rhyme words, punchlines, the word the
bar lands on — and the caption can expose that structure visually by giving
part of a line a different treatment from the rest. The most common target is
the rhyme: two bars that land on 对策 / 配合 read as a pair when those words
share a treatment the surrounding text does not.

Mark the lifted part in the lyrics file with braces:

```text
正确的对策        → 正确的{对策}
Vibe check 你必须配合  → Vibe check 你必须{配合}
```

`{word}` takes the theme's default span effect; `{word:name}` picks a named
effect from `theme.effects`. An effect is a full treatment override, not just
a colour: fill, glow, stroke, and shadow can each be set independently, so the
rhyme can be neon-on-glow in a glow theme, outline-and-flat in a graphic one,
or a different face weight where the renderer supports it.

The two full-line colour roles still exist for styles that want them: line 1
takes `setup`, line 2 takes `payoff`, and a single line marked with a leading
`|` takes `payoff`. Both mechanisms compose — a theme can use line roles, span
effects, or both.

*Range:* the split is a design choice offered to the user, not a rule. Options
worth presenting: colour only; colour plus glow; stroke plus no shadow
(graphic, print-like); size or weight change on the rhyme; the whole second
line lifted rather than one word. Ask which one fits the track — picks are the
user's. Whatever is chosen, apply it consistently for the whole song so the
lifted treatment stays meaningful.

### P3 — Word-onset sync
Each line enters on its own sung onset of its first word (a second line
typically lands 0.15–0.35 s after the first), and the whole cue cuts out at
the phrase end. Cue edges snap to ASR word boundaries, or to the onset the
user tapped, padded −30/+80 ms. Phrase timing is what makes captions feel
performed rather than pasted.

*Range:* pad values shift with mix cleanliness — tighter on a dry vocal, wider
over a loud beat. The sync itself holds.

### P4 — Escalation tiers
Regular captions are tier 1. Structure gives emphasis three rungs, used
sparingly:

- **Tier 2 emphasis** — hook phrases, brand lines, punchline words. Takes a
  distinct material or treatment (extruded 3D, foil, sticker-outline,
  inverted block) plus entrance motion: fly-in with easing, landing on the
  word's onset, holding 0.8–1.5 s. This is the only place easing belongs.
- **Tier 3 finale** — the emotional pivot near the end. Changes the FOOTAGE
  (grade: B&W, bleach, freeze+spotlight, negative) and displays the line in a
  dedicated finale face. The caption overlay carries only the text; the grade
  happens in the grade step.
- **Outro** — a signature sign-off block (SHOUT TO / thanks / artist card)
  over a darkened final scene.

*Range:* each tier's look is a dial. Fixed: one emphasis treatment per cue;
tiers escalate in order, so a finale look belongs on a finale, never on a
random verse line; tier 2 may overlap a regular caption by ≤0.5 s and never
stacks two emphases.

### P5 — Semantic stickers, anchored
A sticker goes where a lyric word has an obvious pictogram — build the whole
set from THIS song's imagery. The pairs used across this skill (a crew line →
👥, a city name → its map, a money line → 💰) illustrate the method and are not
a dictionary to reuse. Stickers anchor to the semantic word's line, layer
BEHIND the caption text, appear with their line, and exit with the cue, at
most ~1 per 1–2 cues.

*Range:* the rendering mode is a dial — `silhouette` (flat white), `duotone`
(tinted), `color` (original art), `none`. Dark and monochrome looks carry
silhouette or duotone; maximalist night looks carry colour.

### P6 — A legibility system, not just a fill
The style lives outdoors and on graded footage: every text element is fill
plus one or more of glow, drop shadow, or stroke. Derive the combination from
THIS footage's brightest and darkest graded frames — white fill on bright sky
needs a shadow or stroke to survive; neon fill on night footage wants glow.
Verify on both extremes before rendering the batch.

*Range:* glow radius 1.5–3% of width; stroke 2–6 px; shadow alpha 60–130. A
bloom that clips to near-white on the payoff colour can BE the look — keep it
when the preset calls for it. Full parameter table: `motion.md`.

### P7 — Rhythm density
Something visual happens every ~2–4 s: a caption switch counts, as do
stickers, emphasis landings, and transitions. Density scales with energy —
140+ BPM trap sits at the fast end; boom-bap and melodic cuts breathe.

*Range:* the interval is a dial; the "never static past ~4–5 s" ceiling holds
for every theme.

### P8 — Motion vocabulary matches the genre
The dominant treatment's motion is a genre signature:

- `hardcut` — punchy, percussive genres (trap, drill, flex). Default.
- `fade` — melodic, emo, lofi; lines breathe in over ~80–120 ms.
- `karaoke` — word-by-word fill highlight, rendered by a sub-agent; the
  bundled script covers `hardcut` and `fade`.
- slide/whip entrances for retro or playful styles.

Entrance easing belongs to tier-2 fly-ins. Tier-1 motion is binary and synced
to the onset.

## 3. The `theme` block (all dials, one place)

Optional top-level object in cues.json. Every field falls back to the
flex-golden default, so `{}` reproduces the reference look.

```json
"theme": {
  "name": "melodic-emo",
  "setup": "#F2EDE2",          // tier-1 line-1 / single-line colour
  "payoff": "#7FB4E0",         // tier-1 line-2 / payoff-only colour
  "accent": "#8E2B3E",         // tier-3 finale text colour
  "glow":   {"color": "#FFFFFF", "radius_pct": 0.018, "strength": 0.8},
  "shadow_alpha": 90,          // 0 disables the drop shadow
  "stroke": {"color": "#1A1A1A", "width_px": 4},   // null = no stroke
  "sticker": {"mode": "duotone", "tint": "#D8CFC2"}, // silhouette|duotone|color|none
  "motion": "fade",            // hardcut|fade  (karaoke → sub-agent)
  "scale": 0.92,               // multiplies all type sizes
  "band": 0.53,                // caption block top, fraction of height
  "margin_pct": 0.057,         // line-1 left margin, fraction of width
  "line_gap": 1.18,            // line-2 baseline offset × line height
  "materials": {               // extends/overrides built-in 3d materials
    "ice": {"face": "#BFE3FF", "side": "#4A6E8E"}
  },
  "effects": {                 // named in-line treatments for {rhyme} spans
    "rhyme": {"fill": "#EDEE19"},
    "rhyme-hard": {"fill": "#FF6B2C",
                   "stroke": {"color": "#1A1A1A", "width_px": 6},
                   "shadow_alpha": 0}
  }
}
```

Each `effects` entry may set `fill`, `glow` (partial, merged over the theme's),
`shadow_alpha`, and `stroke`. An effect with no `glow`/`stroke`/`shadow_alpha`
keys inherits the line's own legibility system and only changes colour — the
bare `{word}` form then behaves like a plain colour swap.

Per-cue overrides beat the theme: `colors: ["#..","#.."]` on any cue,
`spans: [{"text": "...", "effect": "...", "line": 0}]` for in-line lifts,
`material`/`enter`/`enter_dur` on 3d cues, `style`/`tint`/`scale`/`line` on
emoji entries, `motion` per cue. The renderer reads all of these.

## 4. Derivation procedure (how to pick dials)

Run this once per song, before the cue sheet; record the result as the theme
block and confirm it with the user together with the lyric sheet.

1. **Listen/genre pass.** BPM, drum character, mood. Trap/drill/flex →
   hardcut, high density, display CJK serif or heavy sans. Boom-bap →
   hardcut, warm palette, heavy grotesque, sticker `none`. Melodic/emo/lofi
   → fade, lower density (3–5 s events), serif/kai faces, muted palette.
2. **Lyric imagery pass.** Extract the song's own noun imagery (money, city,
   love, rain, cars…) → sticker candidates and tier-2 word list (hooks, brand
   lines, punchlines). A love song gets its own props, whatever the reference
   MV used.
3. **Footage pass.** Sample brightest and darkest graded frames. Choose the
   setup colour that survives the brightest region; choose glow vs stroke vs
   shadow to match (bright bg → shadow/stroke; dark bg → glow). Warm golden
   footage makes cool payoffs pop; neon night footage pairs a near-neutral
   setup with one neon payoff.
4. **User pass.** Explicit user choices (colours, fonts, emoji, "不要 emoji",
   "颜色淡一点") override everything derived above — put them in the theme
   verbatim and say what you overrode.
5. **Check against P1–P8.** A dial that violates a principle (payoff colour
   ≈ setup colour, a finale look with no footage grade) gets fixed, or the
   user accepts the deviation knowingly.

Named starting points for steps 1–3 live in `presets.md`. Composing a theme
from scratch is always allowed.

## 5. What the bundled renderer covers

`helpers/render_captions.py` renders every tier for any theme (PIL, fast,
deterministic): tier-1 hardcut/fade, silhouette/duotone/colour stickers,
pseudo-3D tier-2 with motion blur + RGB fringe, tier-3 finale text (the
footage grade is done separately), and the outro. Karaoke word-highlight,
true perspective/material 3D, and prop sprite animation (money rain) route to
sub-agents or separate overlay assets — see `motion.md` and `rendering.md`.
