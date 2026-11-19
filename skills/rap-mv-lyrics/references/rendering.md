# Rendering — engines, alpha formats, compositing

## Cue sheet sources

Both timing paths converge on one `cues.json`, so rendering never varies by
source. See `cue-sheet.md` for the formats; the commands are:

```bash
# human-tapped (no ASR needed)
python3 helpers/from_ctl.py song.json lyrics.txt -o cues.json [--transcript asr.json]
# word-level ASR
python3 helpers/make_cue_sheet.py transcript.json lyrics.txt -o cues.json
```

## Engine selection

| Need | Engine |
|---|---|
| Core caption style (any theme: two-tone, glow/stroke, hardcut/fade, stickers) | `helpers/render_captions.py` (PIL + ffmpeg). Theme-aware — reads the cues.json `theme` block and per-cue overrides. Fast, deterministic, iterates in seconds. |
| Tier-2 3D emphasis with real perspective/material | Remotion or HyperFrames sub-agent (one slot per cue, parallel), OR the script's pseudo-3D if budget is tight. Pseudo-3D reads correctly at phone size — try it first (`motion.md`). |
| Karaoke word-by-word motion | Remotion/HyperFrames sub-agent only — not in the bundled script. |
| Props (money rain, mic, bag — any sticker props the theme's imagery calls for) | sticker assets / sprite sequences, composited as separate overlays; not the caption renderer's job. |
| AI-painterly transition frame | image style-transfer on a still, 1-frame insert on the cut. |

Output target of the caption renderer is always a **transparent overlay**.
Captions go onto footage in the composite step, at the end of the pipeline.

## Alpha formats

- `webm` (default): VP9 `yuva420p`, `libvpx-vp9 -lossless 0 -crf 10
  -pix_fmt yuva420p`. Plays with ffmpeg `overlay`; ~half the size of MOV.
- `mov`: ProRes 4444 (`prores_ks -profile:v 4 -pix_fmt yuva444p10le`) when
  going into an NLE or when VP9 banding shows on the glow gradients.
- `pngseq`: fallback for debugging individual frames.

## Compositing rules (order is correctness, not preference)

1. Grade/trim/stitch footage FIRST (per-segment extract → concat if cutting,
   30 ms audio fades at boundaries).
2. Props/sticker overlays next.
3. **Caption overlay LAST** in the filter chain, so nothing covers lyrics.
   The renderer prints both commands and also saves them to
   `<out>_commands.txt`. Three hard-won details, all verified on a real
   session:
   - `-start_number` (and other input options) go **before** `-i`.
   - Force the overlay decoder: `-c:v libvpx-vp9 -i captions.webm`. Without
     it, a full-length transcode can pick the native vp9 decoder, which
     DROPS ALPHA — every overlay frame becomes an opaque black frame and
     the background disappears wherever captions are. Symptom: composite
     is black with text, fine only before the first cue.
   - The overlay's first PNG frame may not be t=0; align with
     `[1:v]setpts=PTS+{first_frame/fps}/TB[ov]` before `overlay` (the
     renderer prints the exact command with the right offset).

   `ffmpeg -i graded.mp4 -c:v libvpx-vp9 -i captions.webm -filter_complex \
     "[0:v]fps=60,scale=W:H[bg];[1:v]setpts=PTS+0.783/TB[ov];\
      [bg][ov]overlay=0:0:shortest=1,format=yuv420p" \
     -map "0:a?" -c:v libx264 -crf 17 -c:a copy out.mp4`
   Quote `"0:a?"` in shells that glob `?` (zsh).
4. Accessibility subtitles, if the user wants them, sit in a different area
   after the caption overlay. In this style the captions ARE the subtitles,
   so a second burned subtitle track over them is a defect.
5. Rebase cue times when compositing into a cut timeline:
   `output_time = source_time - segment_start + segment_offset`. Keep one
   master cues.json in source time and generate a rebased copy per timeline —
   edit times in one place only.

## Legibility verification (render → look before delivering)

- Sample frames at: every cue in-point (+1 frame), every line-2 onset, and
  2 random hold frames. Check: glow legible on bright sky AND dark scene,
  emoji behind text, no caption in B&W-red zone, cut-in is instant.
- The reference look tolerates glow clipping to near-white — the bloom peak
  `#FFFE75` on yellow IS the look; don't "fix" it with tone mapping.
- Fonts: assert glyph coverage (script does). A tofu box in a 133 px char is
  instantly visible — check one frame per unique font/material combo.
- The script's default font paths are macOS system fonts (Songti, Apple Color
  Emoji). On another platform, pass `--font` and `--emoji-font` explicitly.

## Performance notes

- PIL renders ~60fps 1080×1920 frames at roughly 5–15 fps; a 22s overlay is
  ~1300 frames ≈ 2–4 min. Render only the union of cue windows (script
  default) and let ffmpeg pad the gaps as transparent stills.
- Glow is the expensive op: one GaussianBlur per text layer per frame.
  Cache glyph bitmaps per (char, size, material) — the script does this.
- For sub-agent 3D slots: give each agent the exact cue times, canvas,
  material hex values, enter direction, and output path; require ffprobe
  duration verification in the deliverable (video-use parallel-slot brief).
