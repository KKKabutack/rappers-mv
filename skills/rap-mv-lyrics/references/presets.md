# Presets — named theme starting points

A preset is a `theme` block (schema in `style-soul.md` §3) plus guidance on
when it fits. Paste the JSON into cues.json (or pass via the renderer's
`--theme-file`), then tune per song. Composing a custom theme is always
allowed and often better.

`flex-golden` is fully measured from a real reference MV — those measurements
are the appendix at the end of this file. It is also the renderer's built-in
default: an empty/absent theme reproduces it.

---

## 1. flex-golden — measured reference (default)

Douyin-style flex/trap short-video look: golden-hour outdoor performance,
two-tone white→lemon captions, white-silhouette stickers, gold 3D hooks,
B&W+red finale.

```json
"theme": {
  "name": "flex-golden",
  "setup": "#FFFFFF", "payoff": "#EDEE19", "accent": "#D61114",
  "glow": {"color": "#FFFFFF", "radius_pct": 0.025, "strength": 1.0},
  "shadow_alpha": 110, "stroke": null,
  "sticker": {"mode": "silhouette", "tint": "#FCFBF1"},
  "motion": "hardcut", "scale": 1.0,
  "band": 0.53, "margin_pct": 0.057, "line_gap": 1.18,
  "materials": {
    "gold":  {"face": "#D8A93E", "side": "#6C4C12"},
    "silver":{"face": "#E8E8EC", "side": "#82828C"},
    "chrome-red": {"face": "#D61114", "side": "#6E0A0A"},
    "olive": {"face": "#B8BE6A", "side": "#5A6030"}
  }
}
```

Fits: flex/trap lyrics (money, ambition, crew), warm outdoor or stage
footage, 130–160 BPM. Font: Songti SC Black / Noto Serif SC Black.
Full measured DNA (timing table, sticker behaviour, transitions): appendix
below.

## 2. melodic-emo — melodic / emo rap

Soft, melancholic; lines fade in; tinted stickers; no hard sell.

```json
"theme": {
  "name": "melodic-emo",
  "setup": "#F2EDE2", "payoff": "#7FB4E0", "accent": "#8E2B3E",
  "glow": {"color": "#FFFFFF", "radius_pct": 0.018, "strength": 0.8},
  "shadow_alpha": 90, "stroke": null,
  "sticker": {"mode": "duotone", "tint": "#D8CFC2"},
  "motion": "fade", "scale": 0.92,
  "band": 0.53, "margin_pct": 0.057, "line_gap": 1.18,
  "materials": {
    "ice":        {"face": "#BFE3FF", "side": "#4A6E8E"},
    "rose-gold":  {"face": "#E0B296", "side": "#78504C"},
    "smoke":      {"face": "#D9D9DE", "side": "#5C5C66"}
  }
}
```

Fits: melodic rap, emo rap, love/loss themes; night city, rain, interior
footage. Font: LXGW WenKai Bold (soft) or Noto Serif SC. Sticker imagery
from the song (rain→🌧 as duotone, hearts→🫀/💜), used even more sparingly
than flex. Tier-3 finale: desaturated warm grade + wine-red serif.

## 3. old-school-boombap — retro hip-hop

Flat, graphic, poster-like: thick strokes, no glow, no metal, no stickers.

```json
"theme": {
  "name": "old-school-boombap",
  "setup": "#FFFFFF", "payoff": "#FFC400", "accent": "#E03A2F",
  "glow": {"color": "#FFFFFF", "radius_pct": 0.0, "strength": 0.0},
  "shadow_alpha": 0,
  "stroke": {"color": "#111111", "width_px": 6},
  "sticker": {"mode": "none"},
  "motion": "hardcut", "scale": 0.95,
  "band": 0.55, "margin_pct": 0.06, "line_gap": 1.12,
  "materials": {
    "flat-white": {"face": "#F5F0E6", "side": "#111111"},
    "flat-red":   {"face": "#E03A2F", "side": "#111111"}
  }
}
```

Fits: boom-bap, jazz-rap, cypher/studio footage, warm film grain grade.
Font: heavy grotesque — PingFang SC Heavy / Noto Sans SC Black. Payoff
realized as amber; finale grade: sepia or a slight over-exposure punch when
B&W would read as cliché for the track.

## 4. night-trap — neon night

Dark footage, neon payoff, color emoji allowed, strong glow.

```json
"theme": {
  "name": "night-trap",
  "setup": "#EAEAEA", "payoff": "#52FF7E", "accent": "#FF2E4C",
  "glow": {"color": "#52FF7E", "radius_pct": 0.03, "strength": 1.2},
  "shadow_alpha": 60,
  "stroke": null,
  "sticker": {"mode": "color"},
  "motion": "hardcut", "scale": 1.0,
  "band": 0.52, "margin_pct": 0.057, "line_gap": 1.18,
  "materials": {
    "ice":       {"face": "#BFE3FF", "side": "#3A5C7A"},
    "purple":    {"face": "#C9A6FF", "side": "#4A2E6E"},
    "chrome-red":{"face": "#FF2E4C", "side": "#5C0A18"}
  }
}
```

Fits: drill/trap at night, car interiors, neon signage. Glow color follows
the payoff hue (set `glow.color` = payoff for a true neon bleed). Emoji in
`color` mode — on dark footage original-color stickers read as premium, not
noisy (verify against P6 on a real frame). Finale grade: crush blacks +
accent-red text.

## 5. minimal-lofi — minimal lofi

Small quiet type, muted palette, no stickers, everything fades.

```json
"theme": {
  "name": "minimal-lofi",
  "setup": "#F4F1EC", "payoff": "#C9B79C", "accent": "#6B4F3A",
  "glow": {"color": "#FFFFFF", "radius_pct": 0.012, "strength": 0.5},
  "shadow_alpha": 70, "stroke": null,
  "sticker": {"mode": "none"},
  "motion": "fade", "scale": 0.8,
  "band": 0.56, "margin_pct": 0.08, "line_gap": 1.15,
  "materials": {
    "kraft":  {"face": "#C9B79C", "side": "#6B4F3A"},
    "ink":    {"face": "#3A342C", "side": "#191613"}
  }
}
```

Fits: lofi/jazzy rap, bedroom performance footage, vlog-style cuts. Type:
LXGW WenKai / Songti (lighter weight if available). Visual events every
3–5s; tier-2 can be as quiet as the `ink` material — still lands on the
hook word (P4 holds even when everything else is quiet).

---

## Composing a custom theme (recipe)

1. Start from the closest preset above; with none fitting, start from
   flex-golden and change deliberately, one dial at a time.
2. Palette: pick setup to survive the footage's brightest region; pick
   payoff clearly distinct from setup (different hue, saturation, or
   weight); accent stays reserved for the finale (P2, P6).
3. Type: serif/kai reads lyrical/traditional; heavy grotesque reads
   percussive/modern. Latin faces match the CJK weight, sized by cap-height.
4. Motion + density from BPM (style-soul.md P7–P8): <100 fade/relaxed,
   100–135 either, 135+ hardcut/fast.
5. Sticker set built from the song's own imagery; mode by aesthetic
   (dark footage → silhouette/duotone; maximalist → colour; graphic looks →
   none).
6. Record the theme in cues.json; verify P1–P8 before rendering
   (style-soul.md §4 step 5).

---

# Appendix: flex-golden measured reference

How preset 1 was measured, kept as a worked example of the method — every
number below is a portable percentage, ready to reuse or rescale.

Reference: a 22.4 s vertical rap MV — 1320×2868, 60 fps, outdoor golden-hour
performance with crew. Measured by frame sampling (1 fps full pass, 8 fps
windows on cue boundaries, 24 fps micro-window on a caption entrance) plus
word-level ASR. Pixel values are measured at 1320 px width; percentages are
the portable numbers — use those against the delivery canvas.

## Canvas & footage grammar

- Vertical 9:19.5 (1320×2868 source). Deliver at source res or 1080×1920.
- 60 fps source; whip pans and fly-ins rely on it. Keep 60 when the footage
  allows; check transitions before halving to 30.
- One rap scene = one camera setup, handheld, subject centred, crew standing
  behind-left/right. 5 setups in 22 s ⇒ average shot 2.5–4 s. Golden hour,
  warm highlights, saturated blue sky, crushed blacks on darker setups.
- B-roll insert: a single object in macro, with one lyric line riding on it.
- Transitions between setups: whip pan with heavy directional motion blur +
  RGB chromatic aberration fringe (blue/red channel split). One full whiteout
  flash. One AI-painterly style-transfer frame as a transition beat.
  Transitions land on drum hits.

## The caption system

### Layout

- Max 2 stacked lines visible per cue. Line 2 is indented right (its left
  edge ≈ 30–60% into line 1's width — follows text length, creating a
  staircase rhythm) and sits ~1.15 line-heights below line 1.
- Block position: line 1 top edge ≈ 53% of frame height; the block occupies
  the 53–66% vertical band, just below mid-frame over the subject's chest.
- Left margin of line 1 ≈ 5.7% of width.
- CJK glyph size ≈ 12.3% of frame width per char (~165 px @1320, ~133 px
  @1080). Latin glyphs render ~15% smaller optically (match cap-height).
- Up to 7 CJK chars per line in this preset (measured at 12.3% scale and 5.7%
  margins on 1080 width); the reference never exceeds 7. This cap is a width
  budget, so it moves with scale and margin — measure with
  `helpers/check_fit.py` rather than counting characters.

### Colours & treatments (sampled)

| Element | Core | Peak (with bloom) |
|---|---|---|
| Setup line | `#FFFFFF` | `#FFFFFF` |
| Payoff line | `#EDEE19` (lemon, slight green tint) | `#FFFE75` |
| Emoji sticker | `#FCFBF1` silhouette | `#FFFFFF` glow |
| Finale text | `#D61114` | — |
| Outro serif | `#FFFFFF` + thin black outline | — |

- Both caption lines: soft white outer glow (bloom) at ~2.5% of width radius,
  plus a faint soft dark drop shadow (offset ~0.5% width, blur ~1%) — the
  shadow is what keeps the white line legible against bright sky.
- The two-tone is semantic: white = narrative setup, yellow = payoff/key
  phrase. Confirmed pattern across all cues: line 1 white, line 2 yellow. A
  single-line cue is white unless it IS the payoff (then yellow).

### Motion

- **Hard cut-in, hold, hard cut-out.** Verified at 24 fps: a line appears
  full-size and fully opaque between consecutive frames. No scale tween, no
  fade. Treat ≤40 ms as instant.
- Each line enters on its own sung onset (line 2 typically 0.2–0.3 s after
  line 1); all lines cut out together at the phrase end.
- Cue durations 0.5–2.2 s following vocal phrasing; typical ~1.2 s.
- No karaoke word highlighting anywhere in the reference.

### Emoji stickers (semantic, silhouette)

- Used ~once per 1–2 cues, only where a lyric word has an obvious pictogram:
  a crew line → 👥 (two people), a city name → map silhouette + ✈️ airplane
  with contrail crossing the sky, money lines → 3D cash props.
- Rendering: white silhouette + white glow, never original colours.
- Size 1.2–1.5× char height (~200 px @1320). Position: overlapping the end of
  the semantic word's line, tucked between the two caption lines, layered
  behind the text (line 2 renders over it).
- Appears (hard cut) with its line, disappears with the cue.
- The glow pulses subtly (bloom intensity oscillates) while the cue holds.

## Emphasis tiers

Regular captions are tier 1. Punch/hook words escalate.

### Tier 2 — 3D metallic emphasis text

- Trigger: hook phrase, brand line, punchline word — the bar the section
  lands on.
- Look: extruded 3D characters with metallic material — gold with dark
  outline (opening), silver-white with gold rim, glossy red chrome, or
  olive-green metal — slight perspective tilt, drop shadow on the scene.
- Motion: flies in from bottom or right with strong directional motion blur
  and RGB fringe, decelerates, holds 0.8–1.5 s, exits with the cut. Easing:
  ease-out landing; enter duration ~0.25–0.4 s.
- Text width spans 50–90% of frame; may coexist with a regular caption
  elsewhere in frame for ~0.5 s (verified).
- Build recipe: `motion.md` (pseudo-3D extrusion, velocity blur, RGB fringe).

### Tier 3 — finale punchline

- Trigger: the emotional punchline near the end.
- Treatment: footage graded B&W (saturation 0) with radial/zoom blur; text in
  a distressed/thorn-serif display font, red `#D61114`, ~1.5× caption size,
  stacked vertically (2 chars per line group for CJK, or 1–3 short words per
  line for Latin), slight per-char rotation jitter (±3°). Holds ~1.5 s over the
  blurred bg. No glow, no emoji.
- The B&W grade is a footage treatment — done in the grade step; the overlay
  carries only the red text.

### Outro — SHOUT TO

- Last 1–2 s: `SHOUT TO <name>` in Roman serif caps (Trajan/Times-like),
  white with thin black outline, slight white glow, ~8% width cap-height,
  single line, left-of-centre at ~58% height, hard cut-in. Scene darkened to
  ~40% brightness.

## Props & overlays

- 3D prop stickers with physical motion: vintage microphone, money bag
  ($ sack), flying US-dollar bills filling the frame depth, fan of cash in
  hand. Opening hook stacks: gold 3D title + mic + bag + money rain.
- Semantic flat stickers: airplane (flies across sky with contrail over
  ~2 s), map silhouette behind a city-name caption.
- Ambient: golden dust particles drifting in one scene (tier-2 moment).
- These are assets, not text: source from sticker packs or render sprites;
  keep them consistent with the track's own theme.

## Typography categories (exact commercial fonts unverified)

- Caption display CJK: high-contrast KaiTi/Songti hybrid, sharp flared stroke
  terminals, condensed. Free stand-ins that hold the vibe: **Songti SC Black**
  (macOS built-in `/System/Library/Fonts/Songti.ttc`), **Noto Serif SC
  Black**, **LXGW WenKai Bold** (softer). If the user has CapCut, the look
  matches its 高对比楷体/宋体 display presets.
- Finale: distressed horror/thorn display CJK (e.g. 演示佛系体-like); free
  stand-in: Noto Serif SC Black with a rough-edge mask, or any grunge CJK
  display the user licenses.
- Outro serif: any Roman serif caps (Songti SC for CJK names, Times/Georgia
  for Latin).
- Always assert glyph coverage: CJK fonts must cover every char in the cue
  sheet before rendering (the script checks).

## Timing summary (reference cue sheet)

An English-heavy bar needs two stacked lines to fit the usable width, so the
rhyme lander usually ends up alone on line 2 — which is exactly where a span
lift wants it.

| t (s) | Lines | Treatment |
|---|---|---|
| 22.67–24.60 | My bros ten toes down | caption |
| 24.60–26.75 | My rap goes / outta the town | caption |
| 26.75–28.79 | No cap I ain't / no {faking} it | caption, rhyme lift |
| 28.79–30.60 | At the right spot, / I'm {making} it | caption, rhyme lift |
| 30.60–32.77 | Ten outta ten / I'm {killing} it | 3D gold hook |
| 32.77–34.85 | That girl so bad / I'm {pushing} it | 3D silver fly-in |
| 34.85–36.95 | Shooting that shot / like KD | caption |
| 36.95–38.95 | She got shined by / my wrist that's AP | caption |
| 38.95–40.75 | Put in work hustle / 忘记礼拜几 | caption, mixed-language bar |
| 40.75–42.85 | 搞点穿搭 / 今天买点纪梵希 | caption |
| 42.85–44.85 | Holding a party / I need KYC | caption |
| 44.85–46.84 | Seeking for verified / PYTs | caption |
| 46.84–48.85 | 4 by 4 hop in / Mercedes | caption |
| 48.85–50.86 | 3 Bs in the back / wearing CCs | caption |
| 50.86–52.90 | I got rizz, / I'm a VIP | caption |
| 52.90–58.86 | Very Intriguing / Human Being | 3D hook |
| 58.86–68.91 | I see that bag / I'm getting it | caption, 5× repeat |
| 68.91–end | Faking it / till I'm {making} it | B&W + red thorn text |

Rhythm: verse → repeated hook → rhyme-pair payoff → finale. The five-peat hook
is the density test: at ~2 s per cue it already meets the "a visual event every
2–4 s" floor, so the repeats need variation (sticker, emphasis, or material
change) rather than five identical cuts.
