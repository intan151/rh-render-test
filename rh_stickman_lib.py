"""Library bersama untuk render stickman webtoon 3D Ruang Healing (Hari 11+).
Berasal dari render_rh04_stickman_v3.py (Hari 4 v3, terverifikasi) + ekstensi:
- kamera variatif: push / drift / zoomout / track / pan (zoom maks 1.03, cx~360)
- toon(): blink berkala, pose baru (shrug, hand_chest, reach, drink, wipe, yawn,
  lift), mood baru (tired, confused), head_dy (angguk)
- helper: dust (partikel debu), battery, sun, hourglass, fog
Aturan presisi v3 berlaku: semua elemen utuh dalam frame, margin >=40px.
"""
import math, json, re
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 720, 1280, 24
BG = (14, 42, 51); CARD = (22, 62, 70); WHITE = (248, 250, 252)
TEAL = (94, 234, 212); YELLOW = (253, 230, 138); CORAL = (251, 113, 133)
MUTED = (148, 184, 193); GREEN = (74, 222, 128); DIM = (10, 30, 37)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
def font(s, bold=True): return ImageFont.truetype(FB if bold else FR, s)
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def lerp(a, b, t): return a + (b - a) * t
def ease(t): t = clamp(t); return t * t * (3 - 2 * t)
def lerp_col(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))

def wrap(draw, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def text_block(draw, cx, y, lines, fnt, fill=WHITE, lh=None, stroke=0):
    lh = lh or int(fnt.size * 1.28)
    if isinstance(lines, str): lines = [lines]
    for ln in lines:
        w = draw.textlength(ln, font=fnt)
        draw.text((cx - w / 2, y), ln, font=fnt, fill=fill,
                  stroke_width=stroke, stroke_fill=BG)
        y += lh
    return y

def draw_title(d, cx, y, parts, size, maxw=600):
    """Judul multi-baris dengan auto-fit ke lebar maks 600px."""
    s = size
    while s > 20:
        f = font(s)
        if all(d.textlength(t, font=f) <= maxw for t, _ in parts):
            break
        s -= 2
    f = font(s)
    lh = int(s * 1.28)
    for t, fill in parts:
        w = d.textlength(t, font=f)
        d.text((cx - w / 2, y), t, font=f, fill=fill)
        y += lh
    return y

def pill(draw, cx, y, text, fnt, bg, fg):
    w = draw.textlength(text, font=fnt) + 44
    draw.rounded_rectangle([cx - w / 2, y, cx + w / 2, y + fnt.size + 26], radius=28, fill=bg)
    draw.text((cx - draw.textlength(text, font=fnt) / 2, y + 13), text, font=fnt, fill=fg)

# ---------- subtitle ----------
_MEAS = ImageDraw.Draw(Image.new("RGB", (10, 10)))
_DELIMS = ["; ", " — ", ": ", ", "]

def _nlines(text):
    return len(wrap(_MEAS, text, font(24, False), 640))

def _split_long(part):
    """Pecah kalimat yang butuh >3 baris subtitle di delimiter terdekat tengah,
    supaya tidak ada kata yang terpotong oleh [:3] di draw_subtitle.
    (Disalin dari rh_render_base.py — perbaikan sistemik 24 Nov.)"""
    if _nlines(part) <= 3:
        return [part]
    best = None
    for dl in _DELIMS:
        start = 0
        while True:
            i = part.find(dl, start)
            if i < 0:
                break
            a, b = part[:i + len(dl)].strip(), part[i + len(dl):].strip()
            if a and b:
                la, lb = _nlines(a), _nlines(b)
                if la <= 3 and lb <= 3:
                    score = abs(len(a) - len(b))
                    if best is None or score < best[0]:
                        best = (score, a, b)
            start = i + 1
    if best is None:
        return [part]
    _, a, b = best
    return _split_long(a) + _split_long(b)

def make_sents(segs):
    sents = []
    for s in segs:
        parts = [p.strip() for p in re.split(r'(?<=[.!?…])\s+', s["text"]) if p.strip()]
        parts = [q for p in parts for q in _split_long(p)]
        tot = sum(len(p) for p in parts) or 1
        cur = s["start"]
        for p in parts:
            d = s["duration"] * len(p) / tot
            sents.append((cur, cur + d, p))
            cur += d
    return sents

def draw_subtitle(d, t, sents, lead):
    nt = t - lead
    txt = None
    for (a, b, x) in sents:
        if a <= nt < b:
            txt = x
            break
    if not txt:
        return
    lines = wrap(d, txt, font(24, False), 640)[:3]
    y = 1145
    for ln in lines:
        w = d.textlength(ln, font=font(24, False))
        d.text((360 - w / 2, y), ln, font=font(24, False), fill=WHITE,
               stroke_width=3, stroke_fill=BG)
        y += 30

def seg_idx(bounds, t):
    for i in range(len(bounds) - 1):
        if bounds[i] <= t < bounds[i + 1]:
            return i, (t - bounds[i]) / (bounds[i + 1] - bounds[i])
    return len(bounds) - 2, 1.0

# ---------- kamera ----------
def camera(img, t, bounds, mode, cx=360, cy=600, track=10):
    """mode: push (zoom 1.0->1.03), drift (1.02, +/-8px), zoomout (1.03->1.0),
    track (1.02, cx geser +/-track px), pan (1.02, cy 630->650).
    Zoom maks 1.03 + cx~360 menjaga konten di zona aman (aturan v3)."""
    si, lp = seg_idx(bounds, t)
    if mode == "push":
        z = 1.0 + 0.03 * ease(lp)
        dx = dy = 0
    elif mode == "zoomout":
        z = 1.03 - 0.03 * ease(lp)
        dx = dy = 0
    elif mode == "drift":
        z = 1.02
        dx = int(lerp(-8, 8, lp)); dy = 0
    elif mode == "track":
        z = 1.02
        dx = int(lerp(-track, track, lp)); dy = 0
    elif mode == "pan":
        z = 1.02
        dx = 0; dy = int(lerp(0, 20, lp))
    else:
        return img
    w, h = int(W / z), int(H / z)
    x0 = int(clamp(cx + dx - w / 2, 0, W - w))
    y0 = int(clamp(cy + dy - h / 2, 0, H - h))
    return img.crop((x0, y0, x0 + w, y0 + h)).resize((W, H), Image.LANCZOS)

# ---------- karakter webtoon 3D ----------
SKIN = (244, 203, 164); HAIR = (96, 64, 48); HAIR_HI = (140, 100, 74)
DARK = (28, 44, 52)
SWEATER = (44, 139, 130); SWEATER_DK = (32, 110, 103); SWEATER_LT = (86, 178, 168)
PANTS = (38, 58, 74); SHOE = (26, 38, 48); COLLAR = (246, 241, 226)
BLUSH = (251, 150, 140)

def capsule(d, p0, p1, w, fill, outline=None, ow=0):
    if outline is not None:
        d.line([p0, p1], fill=outline, width=w + 2 * ow)
        r = (w + 2 * ow) // 2
        for p in (p0, p1):
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=outline)
    d.line([p0, p1], fill=fill, width=w)
    r = w // 2
    for p in (p0, p1):
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=fill)

def toon(d, x, y_feet, s=1.0, phase=0.0, pose="stand", mood="smile", brows="flat",
         face_dx=0, blink=False, head_dy=0):
    """Karakter webtoon 3D ala Hari 14. phase = waktu animasi (nafas/langkah).
    blink=True -> mata tertutup sekejap. head_dy -> anggukan kepala (px)."""
    bob = math.sin(phase) * 3 * s if pose in ("walk", "stand", "lift") else 0
    hy = y_feet - 118 * s + bob + head_dy; hx = x + face_dx
    r = 30 * s
    hip = y_feet - 52 * s
    sh = hy + 30 * s
    ow = max(2, int(3 * s))
    d.ellipse([hx - 34 * s, y_feet - 4 * s, hx + 34 * s, y_feet + 8 * s], fill=(0, 0, 0, 90))
    if pose == "walk":
        sw = math.sin(phase) * 22 * s
        legs = [((hx, hip), (hx - sw, y_feet - 6 * s)), ((hx, hip), (hx + sw, y_feet - 6 * s))]
        feet = [(hx - sw, y_feet - 6 * s), (hx + sw, y_feet - 6 * s)]
    elif pose == "sit":
        legs = [((hx, hip), (hx - 30 * s, y_feet - 6 * s)), ((hx, hip), (hx + 30 * s, y_feet - 6 * s))]
        feet = []
    elif pose == "sleep":
        legs = [((hx, hip), (hx - 14 * s, y_feet - 6 * s)), ((hx, hip), (hx + 14 * s, y_feet - 6 * s))]
        feet = [(hx - 14 * s, y_feet - 6 * s), (hx + 14 * s, y_feet - 6 * s)]
    else:
        legs = [((hx, hip), (hx - 12 * s, y_feet - 6 * s)), ((hx, hip), (hx + 12 * s, y_feet - 6 * s))]
        feet = [(hx - 12 * s, y_feet - 6 * s), (hx + 12 * s, y_feet - 6 * s)]
    for p0, p1 in legs:
        capsule(d, p0, p1, max(8, int(13 * s)), PANTS, DARK, ow)
    if pose == "sit":
        capsule(d, (hx - 30 * s, y_feet - 6 * s), (hx + 30 * s, y_feet - 6 * s),
                max(8, int(13 * s)), PANTS, DARK, ow)
    for fx, fy in feet:
        d.ellipse([fx - 13 * s, fy - 5 * s, fx + 13 * s, fy + 7 * s], fill=SHOE, outline=DARK,
                  width=max(2, int(2 * s)))
    top = sh; bot = hip + 22 * s
    d.rounded_rectangle([hx - 32 * s, top, hx + 32 * s, bot], radius=int(18 * s),
                        fill=SWEATER, outline=DARK, width=max(3, int(4 * s)))
    d.rounded_rectangle([hx + 14 * s, top + 4 * s, hx + 32 * s - 2, bot - 2],
                        radius=int(14 * s), fill=SWEATER_DK)
    d.ellipse([hx - 26 * s, top + 6 * s, hx - 8 * s, top + 22 * s], fill=SWEATER_LT)
    # kerah krem — radius 7*s (bukan 8*s): Pillow 10.2 membalik strip dalam
    # kalau 2*radius+2 > tinggi (16*s) dan full_y tidak terpicu (s=0.95)
    d.rounded_rectangle([hx - 20 * s, top - 4 * s, hx + 20 * s, top + 12 * s],
                        radius=int(7 * s), fill=COLLAR, outline=DARK, width=max(2, int(3 * s)))
    shl_y = sh + 12 * s
    if pose == "write":
        arms = [((hx - 28 * s, shl_y), (hx - 34 * s, shl_y + 30 * s)),
                ((hx + 28 * s, shl_y), (hx + 44 * s, shl_y + 26 * s))]
    elif pose == "happy":
        arms = [((hx - 28 * s, shl_y), (hx - 44 * s, shl_y - 30 * s)),
                ((hx + 28 * s, shl_y), (hx + 44 * s, shl_y - 30 * s))]
    elif pose == "point":
        arms = [((hx + 28 * s, shl_y), (hx + 58 * s, shl_y + 2 * s)),
                ((hx - 28 * s, shl_y), (hx - 34 * s, shl_y + 30 * s))]
    elif pose == "tear":
        arms = [((hx + 28 * s, shl_y), (hx + 40 * s, shl_y - 34 * s)),
                ((hx - 28 * s, shl_y), (hx - 34 * s, shl_y + 30 * s))]
    elif pose == "sit":
        arms = [((hx - 28 * s, shl_y), (hx - 34 * s, bot - 8 * s)),
                ((hx + 28 * s, shl_y), (hx + 34 * s, bot - 8 * s))]
    elif pose == "sad":
        arms = [((hx - 28 * s, shl_y), (hx - 36 * s, shl_y + 34 * s)),
                ((hx + 28 * s, shl_y), (hx + 36 * s, shl_y + 34 * s))]
    elif pose == "shrug":
        arms = [((hx - 28 * s, shl_y), (hx - 50 * s, shl_y - 22 * s)),
                ((hx + 28 * s, shl_y), (hx + 50 * s, shl_y - 22 * s))]
    elif pose == "hand_chest":
        arms = [((hx + 28 * s, shl_y), (hx + 14 * s, shl_y + 24 * s)),
                ((hx - 28 * s, shl_y), (hx - 34 * s, shl_y + 30 * s))]
    elif pose == "reach":
        arms = [((hx + 28 * s, shl_y), (hx + 64 * s, shl_y + 4 * s)),
                ((hx - 28 * s, shl_y), (hx - 34 * s, shl_y + 30 * s))]
    elif pose == "drink":
        arms = [((hx + 28 * s, shl_y), (hx + 30 * s, hy + 14 * s)),
                ((hx - 28 * s, shl_y), (hx - 34 * s, shl_y + 30 * s))]
    elif pose == "wipe":
        sw = math.sin(phase * 2) * 16 * s
        arms = [((hx + 28 * s, shl_y), (hx - 6 * s + sw, hy - 6 * s)),
                ((hx - 28 * s, shl_y), (hx - 34 * s, shl_y + 30 * s))]
    elif pose == "yawn":
        arms = [((hx - 28 * s, shl_y), (hx - 20 * s, hy + 12 * s)),
                ((hx + 28 * s, shl_y), (hx + 36 * s, shl_y + 28 * s))]
    elif pose == "lift":
        # angkat beban di ATAS kepala: lengan lurus ke atas (tangan di shl_y-88s,
        # di atas puncak kepala ~hy-30s) supaya barbel tidak menutupi wajah
        arms = [((hx - 28 * s, shl_y), (hx - 30 * s, shl_y - 88 * s)),
                ((hx + 28 * s, shl_y), (hx + 30 * s, shl_y - 88 * s))]
    else:
        sw = math.sin(phase) * 10 * s if pose == "walk" else math.sin(phase) * 5 * s
        arms = [((hx - 28 * s, shl_y), (hx - 34 * s - sw, shl_y + 30 * s)),
                ((hx + 28 * s, shl_y), (hx + 34 * s + sw, shl_y + 30 * s))]
    for p0, p1 in arms:
        capsule(d, p0, p1, max(7, int(11 * s)), SWEATER, DARK, ow)
        d.ellipse([p1[0] - 6 * s, p1[1] - 6 * s, p1[0] + 6 * s, p1[1] + 6 * s],
                  fill=SKIN, outline=DARK, width=max(2, int(2 * s)))
    if pose == "write":
        d.rectangle([hx + 30 * s, shl_y + 22 * s, hx + 76 * s, shl_y + 56 * s],
                    fill=YELLOW, outline=DARK, width=2)
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=SKIN, outline=DARK, width=max(3, int(4 * s)))
    d.ellipse([hx - 24 * s, hy + 6 * s, hx - 10 * s, hy + 16 * s], fill=BLUSH)
    d.ellipse([hx + 10 * s, hy + 6 * s, hx + 24 * s, hy + 16 * s], fill=BLUSH)
    d.pieslice([hx - r - 2, hy - r - 2, hx + r + 2, hy + 2 * s], 180, 360, fill=HAIR)
    d.polygon([(hx - 6 * s, hy - r + 2 * s), (hx + 2 * s, hy - r - 14 * s),
               (hx + 10 * s, hy - r + 2 * s)], fill=HAIR)
    d.arc([hx - r + 6 * s, hy - r + 4 * s, hx - 2 * s, hy - r + 22 * s], 200, 320,
          fill=HAIR_HI, width=max(2, int(3 * s)))
    ey = hy - 4 * s
    if pose == "look_up":
        ey = hy - 10 * s
    if mood == "sleep" or pose == "sit" or blink:
        d.line([(hx - 16 * s, ey), (hx - 6 * s, ey)], fill=DARK, width=max(2, int(3 * s)))
        d.line([(hx + 6 * s, ey), (hx + 16 * s, ey)], fill=DARK, width=max(2, int(3 * s)))
    elif mood == "tired":
        for ex in (-11 * s, 11 * s):
            d.ellipse([hx + ex - 7 * s, ey - 4 * s, hx + ex + 7 * s, ey + 6 * s],
                      fill=(255, 255, 255), outline=DARK, width=max(2, int(2 * s)))
            d.ellipse([hx + ex - 3 * s, ey - 1 * s, hx + ex + 3 * s, ey + 5 * s], fill=DARK)
            d.line([(hx + ex - 7 * s, ey - 5 * s), (hx + ex + 7 * s, ey - 5 * s)], fill=DARK, width=max(2, int(2 * s)))
    else:
        for ex in (-11 * s, 11 * s):
            d.ellipse([hx + ex - 7 * s, ey - 9 * s, hx + ex + 7 * s, ey + 9 * s],
                      fill=(255, 255, 255), outline=DARK, width=max(2, int(2 * s)))
            d.ellipse([hx + ex - 3.5 * s, ey - 3.5 * s, hx + ex + 3.5 * s, ey + 3.5 * s], fill=DARK)
    if brows == "worried":
        d.line([(hx - 17 * s, hy - 18 * s), (hx - 5 * s, hy - 13 * s)], fill=DARK, width=max(2, int(3 * s)))
        d.line([(hx + 5 * s, hy - 13 * s), (hx + 17 * s, hy - 18 * s)], fill=DARK, width=max(2, int(3 * s)))
    elif brows == "flat":
        d.line([(hx - 17 * s, hy - 16 * s), (hx - 5 * s, hy - 16 * s)], fill=DARK, width=max(2, int(3 * s)))
        d.line([(hx + 5 * s, hy - 16 * s), (hx + 17 * s, hy - 16 * s)], fill=DARK, width=max(2, int(3 * s)))
    elif brows == "raised":
        d.line([(hx - 17 * s, hy - 20 * s), (hx - 5 * s, hy - 20 * s)], fill=DARK, width=max(2, int(3 * s)))
        d.line([(hx + 5 * s, hy - 14 * s), (hx + 17 * s, hy - 14 * s)], fill=DARK, width=max(2, int(3 * s)))
    if mood == "smile":
        d.arc([hx - 11 * s, hy + 6 * s, hx + 11 * s, hy + 20 * s], 20, 160, fill=DARK, width=max(2, int(3 * s)))
    elif mood == "sad":
        d.arc([hx - 11 * s, hy + 10 * s, hx + 11 * s, hy + 24 * s], 200, 340, fill=DARK, width=max(2, int(3 * s)))
    elif mood == "wow":
        d.ellipse([hx - 6 * s, hy + 8 * s, hx + 6 * s, hy + 18 * s], fill=(120, 40, 40), outline=DARK, width=2)
    elif mood == "yawn":
        d.ellipse([hx - 7 * s, hy + 8 * s, hx + 7 * s, hy + 20 * s], fill=(120, 40, 40), outline=DARK, width=2)
    elif mood == "confused":
        d.ellipse([hx - 4 * s, hy + 9 * s, hx + 4 * s, hy + 17 * s], fill=(120, 40, 40), outline=DARK, width=2)
    elif mood == "sleep":
        pass
    else:
        d.line([(hx - 9 * s, hy + 13 * s), (hx + 9 * s, hy + 13 * s)], fill=DARK, width=max(2, int(3 * s)))

def bed(d, x, y, w=420):
    d.rounded_rectangle([x - w / 2, y, x + w / 2, y + 46], radius=18, fill=CARD, outline=DARK, width=4)
    d.rounded_rectangle([x - w / 2 + 12, y - 26, x - w / 2 + 130, y + 8], radius=14, fill=(255, 255, 255), outline=DARK, width=3)

def lie_man(d, x, y, s=1.0):
    hx, hy = x - 130, y - 38
    d.rounded_rectangle([hx + 30, hy - 8, hx + 195, hy + 36], radius=16, fill=SWEATER, outline=DARK, width=4)
    d.ellipse([hx + 60, hy + 26, hx + 100, hy + 36], fill=SWEATER_DK)
    d.ellipse([hx - 26 * s, hy - 26 * s, hx + 26 * s, hy + 26 * s], fill=SKIN, outline=DARK, width=4)
    d.pieslice([hx - 28, hy - 28, hx + 28, hy - 2], 180, 360, fill=HAIR)
    d.line([(hx - 12, hy - 8), (hx - 6, hy - 8)], fill=DARK, width=3)
    d.line([(hx + 6, hy - 8), (hx + 12, hy - 8)], fill=DARK, width=3)
    d.arc([hx - 10, hy + 2, hx + 10, hy + 14], 20, 160, fill=DARK, width=3)
    d.ellipse([hx + 168, hy + 8, hx + 196, hy + 24], fill=SHOE, outline=DARK, width=3)

def wall_clock(d, cx, cy, r=64, hour=23, minute=5):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=DARK, width=5)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255))
    for h in range(12):
        a = math.radians(h * 30 - 90)
        x1 = cx + math.cos(a) * (r - 8); y1 = cy + math.sin(a) * (r - 8)
        x2 = cx + math.cos(a) * (r - 16); y2 = cy + math.sin(a) * (r - 16)
        d.line([(x1, y1), (x2, y2)], fill=BG, width=3)
    ah = math.radians((hour % 12) * 30 + minute * 0.5 - 90)
    am = math.radians(minute * 6 - 90)
    d.line([(cx, cy), (cx + math.cos(ah) * r * 0.5, cy + math.sin(ah) * r * 0.5)], fill=BG, width=5)
    d.line([(cx, cy), (cx + math.cos(am) * r * 0.75, cy + math.sin(am) * r * 0.75)], fill=BG, width=4)
    d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=BG)

def dust(d, t, seed=0, n=14, x0=70, x1=650, y0=120, y1=1120):
    """Partikel debu halus yang melayang pelan — micro-motion di semua adegan."""
    for i in range(n):
        h1 = (seed * 7919 + i * 104729) % 1000 / 1000.0
        h2 = (seed * 104729 + i * 7919) % 1000 / 1000.0
        px = x0 + (h1 * (x1 - x0) + t * (6 + h2 * 10)) % (x1 - x0)
        py = y0 + (h2 * (y1 - y0) + t * (4 + h1 * 8)) % (y1 - y0)
        a = 60 + int(40 * math.sin(t * 0.8 + i))
        r = 2 + (i % 3)
        d.ellipse([px - r, py - r, px + r, py + r], fill=(148, 184, 193, a))

def battery(d, x, y, w, h, frac, label, fill_col, blink=False, t=0.0):
    """Baterai: kotak + isi sesuai frac (0..1) + label di bawah. blink=True:
    berkedip merah saat frac rendah (dipakai untuk baterai hampir kosong)."""
    d.rounded_rectangle([x, y, x + w, y + h], radius=10, outline=WHITE, width=4)
    d.rectangle([x + w, y + h * 0.3, x + w + 10, y + h * 0.7], fill=WHITE)
    if frac > 0.02:
        col = fill_col
        if blink and frac < 0.25 and (int(t * 2) % 2 == 0):
            col = CORAL
        iw = int((w - 12) * clamp(frac))
        d.rounded_rectangle([x + 6, y + 6, x + 6 + iw, y + h - 6], radius=6, fill=col)
    tw = d.textlength(label, font=font(20))
    d.text((x + w / 2 - tw / 2, y + h + 8), label, font=font(20), fill=WHITE)

def sun(d, cx, cy, r, t, ray_spin=0.0):
    """Matahari + sinar yang berputar sangat pelan."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=YELLOW)
    for k in range(8):
        a = math.radians(k * 45 - 90 + ray_spin * t)
        x1 = cx + math.cos(a) * (r + 12); y1 = cy + math.sin(a) * (r + 12)
        x2 = cx + math.cos(a) * (r + 34); y2 = cy + math.sin(a) * (r + 34)
        d.line([(x1, y1), (x2, y2)], fill=YELLOW, width=5)

def hourglass(d, cx, cy, w, h, frac, t):
    """Jam pasir: pasir atas berkurang, pasir bawah bertambah, butir jatuh.
    Pasir digambar sebagai segitiga sebangun yang tingginya mengikuti frac
    (dulu: segitiga selalu penuh sehingga level pasir tidak pernah berubah)."""
    d.polygon([(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx, cy - 6)], fill=(255, 255, 255), outline=DARK)
    d.polygon([(cx - w / 2, cy + h / 2), (cx + w / 2, cy + h / 2), (cx, cy + 6)], fill=(255, 255, 255), outline=DARK)
    half = h / 2 - 10  # tinggi pasir maksimum
    # pasir atas: segitiga kecil di leher, menyusut saat frac 0 -> 1
    th = half * (1 - frac)
    if th > 2:
        hw = (w / 2 - 8) * th / half
        d.polygon([(cx - hw, cy - 6 - th), (cx + hw, cy - 6 - th), (cx, cy - 6)], fill=YELLOW)
    # pasir bawah: timbunan dari dasar, membesar saat frac 0 -> 1
    bh = half * frac
    if bh > 2:
        hw = (w / 2 - 8) * bh / half
        d.polygon([(cx - hw, cy + h / 2 - 6), (cx + hw, cy + h / 2 - 6),
                   (cx, cy + h / 2 - 6 - bh)], fill=YELLOW)
    sy = cy - 6 + ((t * 60) % (h - 20))
    d.ellipse([cx - 3, sy - 3, cx + 3, sy + 3], fill=YELLOW)
