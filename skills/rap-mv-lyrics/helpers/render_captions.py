#!/usr/bin/env python3
"""render_captions.py — render rap-MV lyric caption overlay FRAMES.

Theme-aware: reads the optional `theme` block in cues.json (schema in
references/style-soul.md §3, presets in references/presets.md) plus per-cue
overrides, and renders a transparent PNG frame sequence in that style. With
no theme, output matches the measured flex-golden reference look exactly.
Writes the exact ffmpeg encode + composite commands to <out>_commands.txt
(ffmpeg runs as a separate step — see references/rendering.md).

Usage:
    python3 render_captions.py --cues cues.json \
        [-o captions] [--font path.ttc] [--emoji-font path.ttc] \
        [--theme-file theme.json] [--setup-color #FFF] [--payoff-color #FF0] \
        [--accent-color #F00] [--glow-color #FFF] [--glow-radius 0.02] \
        [--glow-strength 1.0] [--shadow-alpha 110] \
        [--sticker-mode silhouette|duotone|color|none] \
        [--motion hardcut|fade] [--scale 1.0] \
        [--from 3.5] [--to 6.5]

Output: <out>_frames/f_00001.png ... (RGBA) + <out>_commands.txt
"""
import argparse
import json
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------- theme
DEF_THEME = {
    "setup": "#FFFFFF",            # tier-1 line-1 / single-line color
    "payoff": "#EDEE19",           # tier-1 line-2 / payoff-only color
    "accent": "#D61114",           # tier-3 finale text color
    "glow": {"color": "#FFFFFF", "radius_pct": 0.025, "strength": 1.0},
    "shadow_alpha": 110,           # 0 disables the drop shadow
    "stroke": None,                # {"color": "#111", "width_px": 6} or null
    "sticker": {"mode": "silhouette", "tint": "#FCFBF1"},
    "motion": "hardcut",           # hardcut | fade  (karaoke → sub-agent)
    "scale": 1.0,                  # multiplies every type size
    "band": 0.53,                  # caption block top, fraction of height
    "margin_pct": 0.057,           # line-1 left margin, fraction of width
    "line_gap": 1.18,
    "materials": {},               # extra/overriding 3D materials by name
    # Named in-line treatments for {rhyme} spans. Each may set fill,
    # glow (partial), shadow_alpha, stroke — anything glow_text honours.
    # Empty by default: {word} then simply inherits the line's own treatment.
    "effects": {},
}
FADE_IN = 0.10  # seconds a line takes to reach full opacity in fade motion

MATERIALS = {
    "gold":       {"face": "#D8A93E", "side": "#6C4C12"},
    "silver":     {"face": "#E8E8EC", "side": "#82828C"},
    "chrome-red": {"face": "#D61114", "side": "#6E0A0A"},
    "olive":      {"face": "#B8BE6A", "side": "#5A6030"},
}

def merge_theme(*layers):
    """Deep-merge theme dicts over the defaults; later layers win."""
    out = json.loads(json.dumps(DEF_THEME))
    for layer in layers:
        if not layer:
            continue
        for k, v in layer.items():
            if isinstance(v, dict) and isinstance(out.get(k), dict):
                out[k] = {**out[k], **v}
            else:
                out[k] = v
    return out

def hex_color(v, fallback=(255, 255, 255)):
    """'#RGB'/'#RRGGBB' or list/tuple → (r, g, b, 255)."""
    if isinstance(v, (tuple, list)):
        t = tuple(int(c) for c in v)
        return t[:3] + ((255,) if len(t) == 3 else t[3:4])
    s = str(v).strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    try:
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
    except ValueError:
        return tuple(fallback) + (255,)

def resolve_material(ctx, name):
    m = (ctx["theme"]["materials"].get(name) or MATERIALS.get(name)
         or MATERIALS["gold"])
    return {"face": hex_color(m["face"])[:3], "side": hex_color(m["side"])[:3]}

def ease_out_cubic(t):
    return 1 - (1 - t) ** 3

def has_cjk(s):
    return any(0x2E00 < ord(ch) < 0xA000
               and unicodedata.category(ch).startswith("Lo") for ch in s)

# ---------------------------------------------------------------- fonts
CJK_CANDIDATES = [
    ("/System/Library/Fonts/Supplemental/Songti.ttc", 0),  # Songti SC Black
    ("/System/Library/Fonts/Supplemental/Songti.ttc", 1),  # Songti SC Bold
    ("/System/Library/Fonts/Supplemental/STHeiti Light.ttc", 0),
]
LATIN_CANDIDATES = [
    ("/System/Library/Fonts/Supplemental/Times New Roman.ttf", 0),
    ("/System/Library/Fonts/Supplemental/Songti.ttc", 3),
]
EMOJI_CANDIDATES = ["/System/Library/Fonts/Apple Color Emoji.ttc"]

def pick_cjk(path_hint, size):
    if path_hint:
        return ImageFont.truetype(path_hint, size)
    for path, idx in CJK_CANDIDATES:
        try:
            f = ImageFont.truetype(path, size, index=idx)
            if f.getmask("说").getbbox():
                return f
        except Exception:
            continue
    raise SystemExit("no usable CJK display font; pass --font /path/to/font.ttc")

def pick_latin(path_hint, size):
    if path_hint:
        return ImageFont.truetype(path_hint, size)
    for path, idx in LATIN_CANDIDATES:
        try:
            f = ImageFont.truetype(path, size, index=idx)
            if f.getmask("A").getbbox():
                return f
        except Exception:
            continue
    return pick_cjk(None, size)

def pick_emoji(path_hint):
    path = path_hint or EMOJI_CANDIDATES[0]
    for size in (137, 109, 96, 64):
        try:
            f = ImageFont.truetype(path, size, index=0)
            if f.getmask("👥", mode="1").getbbox():
                return f, size
        except Exception:
            continue
    return None, 0

def assert_glyphs(font, text, label):
    missing = sorted({ch for ch in set(text)
                      if not ch.isspace() and not font.getmask(ch).getbbox()})
    if missing:
        raise SystemExit(label + " font missing glyphs: " + "".join(missing))

def font_path(f):
    return getattr(f, "path", CJK_CANDIDATES[0][0])

def text_size(font, s):
    b = font.getbbox(s)
    return b[2] - b[0], b[3] - b[1]

def glow_text(layer, xy, s, font, fill, glow_r, ctx, effect=None):
    """Theme's shadow + outer glow, then crisp fill (optional stroke) on top.

    `effect` overrides any of the theme's legibility keys for this run of text,
    so a rhyme word can carry a different treatment (colour, glow, stroke,
    shadow) than the line it sits in.
    """
    th = ctx["theme"] if not effect else {**ctx["theme"], **effect}
    x, y = xy
    sh_alpha = int(th["shadow_alpha"])
    if sh_alpha > 0:
        sh = Image.new("L", layer.size, 0)
        ImageDraw.Draw(sh).text((x + glow_r * 0.2, y + glow_r * 0.25), s,
                                font=font, fill=sh_alpha)
        sh = sh.filter(ImageFilter.GaussianBlur(max(glow_r * 0.35, 1)))
        shadow_img = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        shadow_img.putalpha(sh)
        layer.alpha_composite(shadow_img)
    k = float(th["glow"]["strength"])
    if glow_r > 0 and k > 0:
        gl = Image.new("L", layer.size, 0)
        ImageDraw.Draw(gl).text((x, y), s, font=font, fill=255)
        gl = gl.filter(ImageFilter.GaussianBlur(glow_r))
        glow_img = Image.new("RGBA", layer.size, hex_color(th["glow"]["color"])[:3] + (0,))
        glow_img.putalpha(gl.point(lambda v: min(255, int(v * k))))
        layer.alpha_composite(glow_img)
    stroke = th.get("stroke")
    if stroke:
        ImageDraw.Draw(layer).text((x, y), s, font=font, fill=fill,
                                   stroke_width=max(1, int(stroke["width_px"])),
                                   stroke_fill=hex_color(stroke["color"]))
    else:
        ImageDraw.Draw(layer).text((x, y), s, font=font, fill=fill)

def resolve_effect(theme, name):
    """Look up an effect name from theme.effects.

    Returns the spec dict as written (fill and/or legibility overrides), or
    None. `fill` is handled separately by the caller; everything else is
    passed to glow_text as a legibility override.
    """
    if not name:
        return None
    spec = (theme.get("effects") or {}).get(name)
    return spec if isinstance(spec, dict) and spec else None

def effect_legibility(theme, spec):
    """Legibility-only part of an effect spec, with glow merged over theme."""
    if not spec:
        return None
    out = {k: v for k, v in spec.items() if k != "fill"}
    if isinstance(out.get("glow"), dict):
        out["glow"] = {**theme["glow"], **out["glow"]}
    return out or None

def split_spans(text, spans):
    """Split a rendered line into [(substring, effect_name|None)] runs.

    `spans` are [{"text": "...", "effect": "rhyme"}] as written in the cue
    sheet; each is located in `text` in order. Text outside any span renders
    with the line's base treatment. Text that occurs twice takes the first
    unclaimed occurrence, so repeated rhyme words stay in reading order.
    """
    if not spans:
        return [(text, None)]
    marks, cursor = [], 0
    for sp in spans:
        needle = sp.get("text") or ""
        if not needle:
            continue
        at = text.find(needle, cursor)
        if at < 0:
            continue
        marks.append((at, at + len(needle), sp.get("effect")))
        cursor = at + len(needle)
    if not marks:
        return [(text, None)]
    runs, pos = [], 0
    for a, b, eff in marks:
        if a > pos:
            runs.append((text[pos:a], None))
        runs.append((text[a:b], eff))
        pos = b
    if pos < len(text):
        runs.append((text[pos:], None))
    return runs

# ---------------------------------------------------------------- emoji
def build_emoji(ch, target, font, font_px, mode="silhouette", tint="#FCFBF1"):
    """Return (body, glow) sprites. Modes: silhouette | duotone | color."""
    try:
        pad = 24
        side = font_px + pad * 2
        tmp = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        ImageDraw.Draw(tmp).text((pad, pad), ch, font=font, embedded_color=True)
        bbox = tmp.getbbox()
        if not bbox:
            return None
        glyph = tmp.crop(bbox)
        s = target / max(glyph.size)
        glyph = glyph.resize((max(1, int(glyph.width * s)),
                              max(1, int(glyph.height * s))), Image.LANCZOS)
    except Exception:
        return None
    a_any = glyph.split()[3].point(lambda v: 255 if v > 8 else 0)
    if mode == "color":
        body = glyph
        shape = a_any
    else:
        lum_th = glyph.convert("L").point(lambda v: 255 if v > 60 else 0)
        mask = Image.composite(a_any, Image.new("L", glyph.size, 0), lum_th)
        body = Image.new("RGBA", glyph.size, hex_color(tint)[:3] + (0,))
        body.putalpha(mask)
        shape = mask
    # The glow must have room to decay: blur inside a padded canvas, then pad
    # the body by the same amount so the two sprites stay aligned. Blurring a
    # glyph-cropped sprite leaves the whole rectangle at partial alpha, which
    # reads as a grey box behind the sticker.
    blur_r = max(2, int(target * 0.045))
    margin = blur_r * 3
    pw, ph = glyph.width + margin * 2, glyph.height + margin * 2

    # Pad the L-mode mask itself. Converting it to RGBA first would set alpha
    # to 255 everywhere and blur a solid rectangle instead of the glyph.
    ga = Image.new("L", (pw, ph), 0)
    ga.paste(shape, (margin, margin))
    ga = ga.filter(ImageFilter.GaussianBlur(blur_r))
    glow = Image.new("RGBA", (pw, ph), (255, 255, 255, 0))
    glow.putalpha(ga.point(lambda v: min(255, int(v * 0.7))))
    body_pad = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    body_pad.alpha_composite(body, (margin, margin))
    body = body_pad
    return (body, glow)

def draw_emoji(layer, em, line_end_x, line_top_y, char_size, ctx, fresh):
    if ctx["emoji"][0] is None:
        return
    st = ctx["theme"]["sticker"]
    mode = em.get("style", st["mode"])
    tint = em.get("tint", st.get("tint", DEF_THEME["sticker"]["tint"]))
    if mode == "none":
        return
    target = int(char_size * em.get("scale", 1.35))
    key = (em["char"], target, mode, tint)
    pair = ctx["emoji_cache"].get(key)
    if pair is None:
        pair = build_emoji(em["char"], target, ctx["emoji"][0], ctx["emoji"][1],
                           mode, tint)
        if pair is None:
            return
        ctx["emoji_cache"][key] = pair
    body, glow = pair
    if fresh:
        glow = brighten(glow, 1.3)
    x = max(16, min(int(line_end_x - target * 0.55),
                    layer.size[0] - target - 16))
    y = int(line_top_y + char_size * 0.55)
    layer.alpha_composite(glow, (x, y))
    layer.alpha_composite(body, (x, y))

def brighten(img, k):
    a = img.split()[3].point(lambda v: min(255, int(v * k)))
    out = Image.new("RGBA", img.size, (255, 255, 255, 0))
    out.putalpha(a)
    return out

# ---------------------------------------------------------------- caption
def caption_frame(layer, cue, t, ctx):
    """Tier-1: up to 2 staggered lines; each line enters at its sung onset.

    Motion comes from the theme (per-cue override wins): hardcut appears
    instantly; fade ramps each line in over FADE_IN seconds after its onset.
    """
    th = ctx["theme"]
    W, H = layer.size
    size = ctx["cjk_size"]
    glow_r = max(0, int(float(th["glow"]["radius_pct"]) * W))
    x = int(float(th["margin_pct"]) * W)
    y = int(float(th["band"]) * H)
    line_gap = float(th["line_gap"])
    motion = cue.get("motion", th["motion"])
    cols = [hex_color(c) for c in
            (cue.get("colors") or [th["setup"], th["payoff"]])]

    for i, text in enumerate(cue["lines"]):
        if i < len(cue["line_starts"]) and t < cue["line_starts"][i]:
            break
        f = ctx["cjk"] if has_cjk(text) else ctx["latin"]
        if len(cue["lines"]) == 1 and cue.get("payoff_only") and len(cols) > 1:
            fill = cols[1]
        else:
            fill = cols[min(i, len(cols) - 1)]
        fade = 1.0
        if motion == "fade" and i < len(cue["line_starts"]):
            fade = max(0.0, min(1.0, (t - cue["line_starts"][i]) / FADE_IN))
        target, tmp = layer, None
        if fade < 0.999:
            tmp = Image.new("RGBA", layer.size, (0, 0, 0, 0))
            target = tmp
        line_w = text_size(f, text)[0]
        for em in cue.get("emoji", []):
            if em.get("line", 0) == i:
                fresh = t - cue["line_starts"][i] < 0.25
                draw_emoji(target, em, x + line_w, y, size, ctx, fresh)
        # Draw in runs so a rhyme word (or any span) can carry its own effect.
        # Runs advance by their own advance width, so spacing stays natural.
        spans = [sp for sp in (cue.get("spans") or []) if sp.get("line", 0) == i]
        run_x = x
        for run_text, eff_name in split_spans(text, spans):
            spec = resolve_effect(th, eff_name)
            eff_fill = (spec or {}).get("fill")
            run_fill = hex_color(eff_fill) if eff_fill else fill
            glow_text(target, (run_x, y), run_text, f, run_fill, glow_r, ctx,
                      effect=effect_legibility(th, spec))
            run_x += text_size(f, run_text)[0]
        if tmp is not None:
            tmp.putalpha(tmp.split()[3].point(lambda v: int(v * fade)))
            layer.alpha_composite(tmp)
        y = int(y + ctx["line_h"] * line_gap)
        x = int(x + line_w * 0.25)

# ---------------------------------------------------------------- 3D emphasis
def build_3d_sprite(text, font, mat, W):
    tw, th = text_size(font, text)
    depth = 6
    dx = int(0.003 * W)
    dy = int(0.006 * W)
    pad = depth * max(dx, dy) + 8
    img = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i in range(depth, 0, -1):
        shade = 0.55 + 0.45 * i / depth
        col = tuple(int(c * shade) for c in mat["side"]) + (255,)
        d.text((pad + dx * i, pad + dy * i), text, font=font, fill=col)
    d.text((pad, pad), text, font=font, fill=mat["face"] + (255,))
    band = Image.new("RGBA", img.size, (255, 255, 255, 70))
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).text((pad, pad), text, font=font, fill=255)
    band.putalpha(Image.composite(band.split()[3], Image.new("L", img.size, 0), mask))
    img.alpha_composite(band)
    return img

def fringe_tint(img, rgb):
    out = Image.new("RGBA", img.size, rgb + (0,))
    out.putalpha(img.split()[3].point(lambda v: int(v * 0.5)))
    return out

def three_d_frame(layer, cue, t, ctx):
    """Tier-2 pseudo-3D emphasis: fly-in with motion blur + RGB fringe."""
    W, H = layer.size
    text = " ".join(cue["lines"])
    size = int(0.16 * W * float(ctx["theme"]["scale"]))
    f = ctx["cjk"] if has_cjk(text) else ctx["latin"]
    tw, th = text_size(f, text)
    if tw > int(0.9 * W):
        size = max(12, int(size * 0.9 * W / tw))
        f = ImageFont.truetype(font_path(f), size)
    mat = resolve_material(ctx, cue.get("material", "gold"))
    key = (text, size, mat["face"])
    sprite = ctx["sprite_cache"].get(key)
    if sprite is None:
        sprite = build_3d_sprite(text, f, mat, W)
        ctx["sprite_cache"][key] = sprite

    enter = cue.get("enter", "bottom")
    enter_dur = float(cue.get("enter_dur", 0.35))
    st = cue["start"]
    prog = min(1.0, max(0.0, (t - st) / max(enter_dur, 0.01)))
    e = ease_out_cubic(prog)
    off = 1 - e
    if enter == "bottom":
        ox, oy = 0, int(off * 0.35 * H)
    elif enter == "right":
        ox, oy = int(off * 0.6 * W), 0
    else:
        ox, oy = 0, int(off * 0.2 * H)
    moving = prog < 0.85

    sw, sh = sprite.size
    x = (W - sw) // 2
    y = int(0.42 * H)
    if moving:
        for alpha, back in ((0.30, -12), (0.18, -26), (0.10, -44)):
            gx = int(ox * back / 44.0)
            gy = int(oy * back / 44.0)
            ghost = fringe_tint(sprite, (60, 60, 255) if back == -44 else (255, 60, 60))
            ghost.putalpha(ghost.split()[3].point(lambda v: int(v * alpha)))
            layer.alpha_composite(ghost, (x + gx, y + oy + gy))
        layer.alpha_composite(fringe_tint(sprite, (255, 70, 70)), (x + ox - 3, y + oy - 1))
        layer.alpha_composite(fringe_tint(sprite, (60, 70, 255)), (x + ox + 3, y + oy + 1))
    layer.alpha_composite(sprite, (x + ox, y + oy))

# ---------------------------------------------------------------- finale red
def red_frame(layer, cue, t, ctx):
    """Tier-3 finale: accent-colored display text, oversized, per-line
    rotation jitter, no glow. The footage grade (B&W etc.) happens in the
    grade step — this overlay carries only the text."""
    W, H = layer.size
    lines = cue["lines"] or ["?"]
    fill = hex_color(ctx["theme"]["accent"])
    size = int(0.185 * W * float(ctx["theme"]["scale"]))
    f = ImageFont.truetype(font_path(ctx["cjk"]), size)
    tw_all = max(text_size(f, ln)[0] for ln in lines)
    x = (W - tw_all) // 2
    y = int(0.28 * H)
    for i, ln in enumerate(lines):
        tw, th = text_size(f, ln)
        img = Image.new("RGBA", (tw + 40, th + 40), (0, 0, 0, 0))
        ImageDraw.Draw(img).text((20, 20), ln, font=f, fill=fill)
        img = img.rotate(3 if i % 2 else -3, expand=True, resample=Image.BICUBIC)
        cx = x + (tw_all - tw) // 2
        layer.alpha_composite(img, (int(cx - 20), y))
        y += int(th * 1.12)

# ---------------------------------------------------------------- shout outro
def shout_frame(layer, cue, t, ctx):
    """Outro: serif caps in the setup color with a thin dark outline."""
    W, H = layer.size
    text = cue["lines"][0]
    base = ctx["latin"] if not has_cjk(text) else ctx["cjk"]
    size = int(0.085 * W * float(ctx["theme"]["scale"]))
    f = ImageFont.truetype(font_path(base), size)
    tw, th = text_size(f, text)
    x = int(0.16 * W)
    y = int(0.55 * H)
    ImageDraw.Draw(layer).text((x, y), text, font=f,
                               fill=hex_color(ctx["theme"]["setup"]),
                               stroke_width=max(2, int(size * 0.035)),
                               stroke_fill=(0, 0, 0, 220))

TREATMENTS = {
    "caption": caption_frame,
    "3d": three_d_frame,
    "finale": red_frame,
    "shout": shout_frame,
}
# Legacy cue sheets (and lyrics marked with `**`) used "red" for this tier.
# The name was a flex-golden colour leak: the visible fill comes from
# theme.accent, so "finale" is the honest name. Alias kept for old cue files.
TREATMENTS["red"] = red_frame

# ---------------------------------------------------------------- pipeline
def frame_windows(cues, fps, duration):
    wins = {}
    for c in cues:
        f0 = max(0, int(c["start"] * fps) - 1)
        f1 = min(int(duration * fps) - 1, int(c["end"] * fps) + 1)
        for fi in range(f0, f1 + 1):
            wins.setdefault(fi, []).append(c)
    return wins

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cues", required=True)
    ap.add_argument("-o", "--out", default="captions")
    ap.add_argument("--font", default=None)
    ap.add_argument("--emoji-font", default=None)
    ap.add_argument("--theme-file", default=None,
                    help="JSON theme (or {\"theme\": {...}}) merged over the cues.json theme")
    ap.add_argument("--setup-color", default=None)
    ap.add_argument("--payoff-color", default=None)
    ap.add_argument("--accent-color", default=None)
    ap.add_argument("--glow-color", default=None)
    ap.add_argument("--glow-radius", type=float, default=None,
                    help="glow radius as a fraction of canvas width (e.g. 0.02)")
    ap.add_argument("--glow-strength", type=float, default=None)
    ap.add_argument("--shadow-alpha", type=int, default=None)
    ap.add_argument("--sticker-mode", default=None,
                    choices=["silhouette", "duotone", "color", "none"])
    ap.add_argument("--motion", default=None, choices=["hardcut", "fade"])
    ap.add_argument("--scale", type=float, default=None)
    ap.add_argument("--from", dest="t_from", type=float, default=None)
    ap.add_argument("--to", dest="t_to", type=float, default=None)
    args = ap.parse_args()

    doc = json.loads(Path(args.cues).resolve(strict=True).read_text(encoding="utf-8"))
    override = {}
    for flag, key in (("setup_color", "setup"), ("payoff_color", "payoff"),
                      ("accent_color", "accent"), ("motion", "motion"),
                      ("scale", "scale"), ("shadow_alpha", "shadow_alpha")):
        val = getattr(args, flag)
        if val is not None:
            override[key] = val
    if args.glow_color:
        override["glow"] = {**DEF_THEME["glow"], "color": args.glow_color}
    if args.glow_radius is not None:
        override["glow"] = {**override.get("glow", DEF_THEME["glow"]),
                            "radius_pct": args.glow_radius}
    if args.glow_strength is not None:
        override["glow"] = {**override.get("glow", DEF_THEME["glow"]),
                            "strength": args.glow_strength}
    if args.sticker_mode:
        override["sticker"] = {**DEF_THEME["sticker"], "mode": args.sticker_mode}
    theme_file = None
    if args.theme_file:
        tdoc = json.loads(Path(args.theme_file).resolve(strict=True)
                          .read_text(encoding="utf-8"))
        theme_file = tdoc.get("theme") if isinstance(tdoc.get("theme"), dict) else tdoc
    theme = merge_theme(doc.get("theme"), theme_file, override)

    W, H = doc["canvas"]
    fps = doc["fps"]
    cues = doc["cues"]
    if args.t_from is not None or args.t_to is not None:
        cues = [c for c in cues
                if (args.t_to is None or c["start"] < args.t_to)
                and (args.t_from is None or c["end"] > args.t_from)]
    if not cues:
        raise SystemExit("no cues in the requested window")
    # Span effects only exist in caption_frame; warn rather than drop them
    # silently on the tiers that render a whole line in one treatment.
    for c in cues:
        if c.get("spans") and c.get("treatment", "caption") != "caption":
            print(f"warning: cue at {c['start']:.2f}s is '{c.get('treatment')}' "
                  f"— span effects apply to caption cues only, ignoring "
                  f"{len(c['spans'])} span(s)", file=sys.stderr)
    duration = max(c["end"] for c in cues) + 1.0

    size = int(0.123 * W * float(theme["scale"]))
    ctx = {
        "W": W, "H": H, "fps": fps, "theme": theme,
        "cjk_size": size, "line_h": int(size * 1.15),
        "cjk": pick_cjk(args.font, size),
        "latin": pick_latin(args.font, size),
        "emoji": pick_emoji(args.emoji_font),
        "emoji_cache": {},
        "sprite_cache": {},
    }
    all_text = " ".join(t for c in cues for t in c["lines"])
    assert_glyphs(ctx["cjk"], all_text, "CJK")
    assert_glyphs(ctx["latin"], all_text, "Latin")
    if ctx["emoji"][0] is None:
        print("warning: emoji font unavailable, emoji stickers will be skipped")

    wins = frame_windows(cues, fps, duration)
    frames_dir = Path(args.out + "_frames")
    frames_dir.mkdir(parents=True, exist_ok=True)

    t0 = min(c["start"] for c in cues)
    f_first = max(0, int(t0 * fps) - 1)
    f_last = int(duration * fps)
    n_written = 0
    for fi in range(f_first, f_last):
        t = fi / fps
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for cue in wins.get(fi, []):
            fn = TREATMENTS[cue.get("treatment", "caption")]
            fn(frame, cue, t, ctx)
        # contiguous numbering incl. transparent gap frames (ffmpeg requirement)
        path = frames_dir / ("f_%05d.png" % fi)
        frame.save(path)
        n_written += 1

    first_cmd = ("ffmpeg -framerate {fps} -start_number {n0} -i {dir}/f_%05d.png "
                 "-c:v libvpx-vp9 -pix_fmt yuva420p -crf 10 -b:v 0 "
                 "-auto-alt-ref 0 {base}.webm").format(
                     fps=int(fps), dir=frames_dir, n0=f_first, base=args.out)
    offset = f_first / fps
    composite_cmd = (
        "ffmpeg -i FOOTAGE.mp4 -c:v libvpx-vp9 -i {base}.webm -filter_complex "
        "\"[0:v]fps={fps},scale={W}:{H}[bg];[1:v]setpts=PTS+{off:.3f}/TB[ov];"
        "[bg][ov]overlay=0:0:shortest=1,format=yuv420p\" -map \"0:a?\" "
        "-c:v libx264 -crf 17 -c:a copy {base}.mp4"
        .format(base=args.out, fps=int(fps), W=W, H=H, off=offset))
    cmds_txt = Path(args.out + "_commands.txt")
    cmds_txt.parent.mkdir(parents=True, exist_ok=True)
    cmds_txt.write_text(
        "# encode the transparent overlay\n" + first_cmd + "\n\n"
        "# composite it LAST (captions on top of graded footage)\n"
        + composite_cmd + "\n", encoding="utf-8")
    print("overlay frames:", n_written, "in", frames_dir)
    print("theme:", theme.get("name", "custom"))
    print("next step (encode overlay):")
    print("  " + first_cmd)
    print("then composite (captions LAST; force libvpx decode for alpha):")
    print("  " + composite_cmd)
    print("commands written to:", cmds_txt)

if __name__ == "__main__":
    main()
