#!/usr/bin/env python3
"""Ruang Healing stickman (Hari 31-40) — template generik mengikuti Hari 13.
Gaya: karakter webtoon 3D ala Hari 14 + aturan presisi v3 (margin >=40px, zoom<=1.03).
Narasi: avocado_v2:MAI_03 speed 95. Musik bed Hari 14 vol 0.06 (dip 0.03 latihan).
Format: 720x1280, 24fps, H.264+AAC, faststart.
Adegan digerakkan data SPEC (judul, prop, kamera, rencana karakter) per hari.
"""
import math, os, subprocess, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rh_stickman_lib import *
from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.abspath(__file__))
NAR = f"{BASE}/narasi.mp3"
SEG = f"{BASE}/segments.json"
MUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music-bed.wav")
OUT = os.path.join(BASE, os.path.basename(BASE).replace("video-", "") + ".mp4")

LEAD, TAIL = 0.7, 3.0
SEGJ = json.load(open(SEG))
segs = SEGJ["segments"]; pause_after = SEGJ["pause_after"]
SMAP = json.load(open(f"{BASE}/scene_map.json"))
bounds = [LEAD]; _t = 0.0
for sc in SMAP["scenes"]:
    for j in range(sc["chunks"][0], sc["chunks"][1]):
        _t += segs[j]["duration"]
        if segs[j]["id"] == pause_after:
            _t += 15.0
    bounds.append(LEAD + _t)
NAR_DUR = _t
DUR = int(math.ceil(LEAD + _t + TAIL))
bounds.append(float(DUR))
SCENES = [s["name"] for s in SMAP["scenes"]] + ["tail"]
SENTS = make_sents(segs)
SPEC = {'title': 'Minggu Malam, Perutmu Sudah Mulas Duluan?', 'scenes': [{'title': [('Minggu malam, akhir pekan', 'WHITE'), ('belum selesai. Tapi kepalamu', 'WHITE'), ('sudah masuk hari Senin.', 'YELLOW')], 'size': 38, 'cam': 'zoomout', 'prop': 'clock', 'char': [('stand', 'smile', 'flat', 0), ('stand', 'sad', 'worried', 0)]}, {'title': [('Senin belum datang,', 'WHITE'), ('tapi tubuhmu sudah tegang.', 'YELLOW')], 'cam': 'drift', 'prop': 'thought', 'params': {'words': ['rapat', 'tugas', 'pesan']}, 'char': [('stand', 'smile', 'flat', 0), ('stand', 'confused', 'raised', 14), ('stand', 'sad', 'worried', 0)]}, {'title': [('Otakmu takut pada yang', 'WHITE'), ('belum pasti.', 'YELLOW')], 'cam': 'push', 'prop': 'calendar', 'char': [('reach', 'tired', 'worried', 0), ('stand', 'sad', 'worried', 0)]}, {'title': [('Langkah 1 —', 'YELLOW'), ('Tutup Minggu dengan', 'YELLOW'), ('satu kalimat.', 'WHITE')], 'cam': 'pan', 'prop': 'paper', 'params': {'line': 'Mingguku sudah cukup.'}, 'char': [('write', 'smile', 'flat', 0), ('hand_chest', 'smile', 'flat', 0)]}, {'title': [('Langkah 2 —', 'YELLOW'), ('Siapkan satu hal kecil', 'YELLOW'), ('untuk Senin.', 'WHITE')], 'cam': 'push', 'prop': 'bag', 'params': {'items': ['buku', 'air', 'catatan']}, 'char': [('stand', 'smile', 'flat', 0), ('happy', 'smile', 'flat', 0)]}, {'title': [('Langkah 3 —', 'YELLOW'), ('Buat Senin pagi', 'YELLOW'), ('yang ramah.', 'WHITE')], 'cam': 'track', 'prop': 'tea', 'char_move': 'walk_right', 'char': [('drink', 'smile', 'flat', 0), ('walk', 'smile', 'flat', 0)]}, {'title': [('Tulis 1 tugas pertama', 'WHITE'), ('untuk Senin.', 'WHITE')], 'cam': 'push', 'prop': 'timer', 'params': {'total': 60}, 'char': [('sit', 'sleep', 'flat', 0)]}, {'title': [('Senin bisa menunggu', 'WHITE'), ('sampai besok.', 'YELLOW')], 'prop': None}]}
print(f"narasi {NAR_DUR:.1f}s -> video {DUR}s ({FPS*DUR} frames)", flush=True)
print("bounds:", [round(b, 1) for b in bounds], flush=True)

def blink(t):
    return (t % 3.7) < 0.12

def phone(d, x, y, glow=0.0, w=64, h=110):
    if glow > 0:
        d.rounded_rectangle([x - w / 2 - 6, y - h / 2 - 6, x + w / 2 + 6, y + h / 2 + 6],
                            radius=14, outline=(94, 234, 212, int(120 * glow)), width=3)
    d.rounded_rectangle([x - w / 2, y - h / 2, x + w / 2, y + h / 2], radius=10, fill=DARK, outline=WHITE, width=3)
    d.rectangle([x - w / 2 + 6, y - h / 2 + 6, x + w / 2 - 6, y + h / 2 - 6], fill=(60, 120, 140))

def desk(d, y=700, x0=110, x1=610):
    d.rounded_rectangle([x0, y, x1, y + 30], radius=10, fill=CARD, outline=DARK, width=3)

def book(d, x0=200, y0=580, x1=420, y1=700):
    d.rectangle([x0, y0, x1, y1], fill=(255, 255, 255), outline=DARK, width=3)
    d.line([( (x0+x1)//2, y0), ((x0+x1)//2, y1)], fill=MUTED, width=2)

def cup_tea(d, x, y, steam=True, t=0.0, s=1.0):
    d.rounded_rectangle([x - 34*s, y, x + 34*s, y + 44*s], radius=10, fill=(255, 255, 255), outline=DARK, width=3)
    d.arc([x + 30*s, y + 8*s, x + 52*s, y + 36*s], -90, 90, fill=DARK, width=3)
    if steam:
        for k in range(3):
            off = (t * 30 + k * 40) % 120
            yy = y - 6 - off * 0.35
            xx = x - 16 + k * 16 + math.sin(t * 2 + k) * 5
            d.line([(xx, yy), (xx + 4, yy - 12)], fill=(148, 184, 193, 180), width=3)

def bubble(d, x, y, r, text, t, bob=0):
    yy = y + math.sin(t * 1.5 + x) * 4 + bob
    d.ellipse([x - r, yy - r, x + r, yy + r], fill=(255, 255, 255), outline=DARK, width=3)
    f = font(20)
    tw = d.textlength(text, font=f)
    d.text((x - tw / 2, yy - 10), text, font=f, fill=DARK)

# ---------- props: tiap prop digambar di zona y 340-760, t=waktu global, lp=progres adegan ----------
def prop_clock(d, t, lp, p):
    wall_clock(d, 560, 330, r=56, hour=(t * 2) % 12, minute=(t * 120) % 60)
    desk(d); book(d)
    glow = 0.5 + 0.5 * math.sin(t * 4)
    phone(d, 520, 640, glow=glow)

def prop_thought(d, t, lp, p):
    words = p.get("words", ["rapat", "tugas", "pesan"])
    for k, w in enumerate(words):
        x = 200 + k * 160
        y = 420 + (k % 2) * 60
        r = 52 + 8 * math.sin(t * 2 + k)
        bubble(d, x, y, int(r), w, t)
    d.ellipse([312, 800, 332, 820], fill=(255, 255, 255), outline=DARK, width=2)
    d.ellipse([330, 845, 358, 873], fill=(255, 255, 255), outline=DARK, width=2)

def prop_calendar(d, t, lp, p):
    x0, y0, cw, ch = 72, 360, 84, 62
    days = ["SEN", "SEL", "RAB", "KAM", "JUM", "SAB", "MIN"]
    for k, dy in enumerate(days):
        x = x0 + k * cw
        hot = (dy == "SEN")
        grow = 1 + (0.25 * math.sin(t * 3) + 0.25 * lp) if hot else 1.0
        w2, h2 = cw * grow, ch * grow
        cx, cy = x + cw / 2, y0 + ch / 2
        fill = CORAL if hot else CARD
        d.rounded_rectangle([cx - w2/2, cy - h2/2, cx + w2/2, cy + h2/2], radius=10,
                            fill=fill, outline=WHITE if hot else DARK, width=3)
        f = font(22)
        tw = d.textlength(dy, font=f)
        d.text((cx - tw / 2, cy - 12), dy, font=f, fill=WHITE)
    d.text((360 - d.textlength("MINGGU INI", font=font(26)) / 2, 300),
           "MINGGU INI", font=font(26), fill=MUTED)
    # panah berdenyut menunjuk sel Senin dari atas
    ay = int(6 * math.sin(t * 3))
    d.polygon([(100, 330 + ay), (130, 330 + ay), (115, 352 + ay)], fill=YELLOW)

def prop_paper(d, t, lp, p):
    desk(d)
    d.rectangle([220, 560, 500, 700], fill=(255, 255, 255), outline=DARK, width=3)
    line = p.get("line", "Mingguku sudah cukup.")
    n = max(1, int(len(line) * clamp(lp * 1.4)))
    f = font(20)
    yy = 590
    for ln in wrap(d, line[:n], f, 240):
        d.text((240, yy), ln, font=f, fill=DARK)
        yy += 26
    d.line([(240, 660), (480, 660)], fill=MUTED, width=2)
    if lp > 0.7:  # kertas dilipat: sudut terlipat
        d.polygon([(460, 560), (500, 560), (500, 600), (480, 580)], fill=(200, 210, 215), outline=DARK)
    d.line([(520, 640), (580, 640)], fill=YELLOW, width=5)

def prop_bag(d, t, lp, p):
    items = p.get("items", ["buku", "air", "catatan"])
    for k, it in enumerate(items):
        show = lp > (k + 0.5) / (len(items) + 1)
        if not show:
            continue
        yy = 560 - k * 0 + int(6 * math.sin(t * 2 + k))
        d.rounded_rectangle([250 + k * 70, yy - 40, 320 + k * 70, yy + 40], radius=8,
                            fill=(255, 255, 255) if k % 2 == 0 else TEAL, outline=DARK, width=3)
        f = font(16)
        tw = d.textlength(it, font=f)
        d.text((285 + k * 70 - tw / 2, yy - 8), it, font=f, fill=DARK)
    d.rounded_rectangle([230, 620, 490, 740], radius=16, fill=(120, 90, 60), outline=DARK, width=4)
    d.arc([300, 560, 420, 660], 180, 360, fill=DARK, width=6)

def prop_tea(d, t, lp, p):
    d.rounded_rectangle([90, 330, 300, 560], radius=14, fill=(30, 80, 90), outline=WHITE, width=4)
    sun(d, 195, 480, 42, t, ray_spin=2.0)
    desk(d, y=700)
    cup_tea(d, 360, 600, steam=True, t=t)
    d.text((360 - d.textlength("teh hangat", font=font(24, False)) / 2, 745),
           "teh hangat", font=font(24, False), fill=MUTED)

def prop_timer(d, t, lp, p):
    total = p.get("total", 60)
    remain_s = max(0, total - int(lp * total))
    mm, ss = divmod(remain_s, 60)
    tstr = f"{mm}:{ss:02d}"
    cx, cy, r = 360, 480, 110
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=CARD, width=12)
    d.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * (1 - lp), fill=TEAL, width=12)
    d.text((cx - d.textlength(tstr, font=font(72)) / 2, cy - 48), tstr, font=font(72), fill=WHITE)
    d.text((cx - d.textlength("timer", font=font(26, False)) / 2, cy + 44), "timer",
           font=font(26, False), fill=MUTED)
    br = 18 + 12 * math.sin(2 * math.pi * t / 4)
    d.ellipse([360 - br, 962 - br, 360 + br, 962 + br], outline=TEAL, width=4)
    d.ellipse([360 - br * 0.55, 962 - br * 0.55, 360 + br * 0.55, 962 + br * 0.55],
              outline=(94, 234, 212, 120), width=3)

def prop_trophy(d, t, lp, p):
    # piala emas + topeng yang muncul di belakang (lp>0.4)
    d.polygon([(300, 420), (420, 420), (400, 520), (320, 520)], fill=YELLOW, outline=DARK, width=3)
    d.rectangle([340, 520, 380, 560], fill=YELLOW, outline=DARK, width=3)
    d.rectangle([310, 560, 410, 580], fill=YELLOW, outline=DARK, width=3)
    d.arc([300, 430, 340, 500], 90, 270, fill=YELLOW, width=8)
    d.arc([380, 430, 420, 500], 270, 90, fill=YELLOW, width=8)
    if lp > 0.35:
        a = int(255 * clamp((lp - 0.35) / 0.3))
        d.ellipse([480, 380, 620, 480], fill=(200, 170, 220, a), outline=DARK, width=3)
        d.ellipse([505, 415, 535, 435], fill=DARK)
        d.ellipse([565, 415, 595, 435], fill=DARK)
        d.arc([520, 440, 580, 470], 20, 160, fill=DARK, width=3)

def prop_scale(d, t, lp, p):
    # timbangan miring: kiri berat (kecil) vs kanan (besar) — sudut berubah dengan lp
    left = p.get("left", "10 keberhasilan")
    right = p.get("right", "1 kesalahan")
    tilt = lerp(-14, 14, clamp(lp)) if p.get("tilt_to", "right") == "right" else lerp(14, -14, clamp(lp))
    cx, cy = 360, 520
    d.line([(cx, cy - 120), (cx, cy + 120)], fill=WHITE, width=6)
    ang = math.radians(tilt)
    dx, dy = math.cos(ang) * 180, math.sin(ang) * 180
    d.line([(cx - dx, cy - 60 - dy), (cx + dx, cy - 60 + dy)], fill=WHITE, width=6)
    for sx, sy, lab in ((cx - dx, cy - 60 - dy, left), (cx + dx, cy - 60 + dy, right)):
        d.line([(sx, sy), (sx, sy + 60)], fill=MUTED, width=3)
        d.ellipse([sx - 60, sy + 55, sx + 60, sy + 75], fill=CARD, outline=WHITE, width=3)
        f = font(18)
        tw = d.textlength(lab, font=f)
        d.text((sx - tw / 2, sy + 84), lab, font=f, fill=WHITE)
    d.polygon([(cx - 30, cy + 120), (cx + 30, cy + 120), (cx, cy + 80)], fill=WHITE)

def prop_box(d, t, lp, p):
    items = p.get("items", ["terima kasih", "tugas selesai", "pujian"])
    n = min(len(items), int(lp * (len(items) + 1)))
    for k in range(n):
        yy = 520 - k * 46 + int(4 * math.sin(t * 2 + k))
        d.rounded_rectangle([260, yy - 18, 460, yy + 18], radius=8, fill=(255, 255, 255), outline=DARK, width=3)
        f = font(20)
        d.text((280, yy - 10), items[k], font=f, fill=DARK)
    d.rounded_rectangle([230, 620, 490, 740], radius=12, fill=(150, 110, 70), outline=DARK, width=4)
    d.line([(230, 620), (490, 620)], fill=DARK, width=3)

def prop_mirror(d, t, lp, p):
    d.rounded_rectangle([220, 330, 500, 640], radius=18, fill=(30, 80, 90), outline=WHITE, width=5)
    # pantulan: wajah tersenyum kecil di cermin (berdenyut pelan)
    r = 46 + 3 * math.sin(t * 1.5)
    d.ellipse([360 - r, 420 - r, 360 + r, 420 + r], fill=SKIN, outline=DARK, width=3)
    d.ellipse([330, 410, 344, 424], fill=DARK)
    d.ellipse([376, 410, 390, 424], fill=DARK)
    d.arc([340, 430, 380, 458], 20, 160, fill=DARK, width=3)
    if lp > 0.5:  # topeng jatuh ke lantai
        fy = int(lerp(660, 980, clamp((lp - 0.5) / 0.4)))
        d.ellipse([540, fy - 22, 620, fy + 22], fill=(200, 170, 220), outline=DARK, width=3)
        d.ellipse([555, fy - 8, 575, fy + 8], fill=DARK)
        d.ellipse([585, fy - 8, 605, fy + 8], fill=DARK)

def prop_bench(d, t, lp, p):
    # dua karakter duduk di bangku: gambar bangku + gelembung ucapan
    d.rounded_rectangle([150, 640, 570, 670], radius=10, fill=(120, 90, 60), outline=DARK, width=3)
    d.rectangle([180, 670, 200, 720], fill=DARK)
    d.rectangle([520, 670, 540, 720], fill=DARK)
    if lp > 0.3:
        bubble(d, 560, 420, 90, p.get("say", "Aku juga begitu."), t)
    toon(d, 460, 720, s=0.9, phase=t * 1.5, pose="sit", mood="smile", brows="flat", blink=blink(t))

def prop_erase(d, t, lp, p):
    d.rectangle([180, 480, 540, 640], fill=(255, 255, 255), outline=DARK, width=3)
    line = p.get("line", "Kalimat yang sempurna...")
    a = int(255 * (1 - clamp(lp * 1.1)))
    f = font(24)
    d.text((210, 540), line, font=f, fill=(40, 40, 40, a))
    ex = 220 + int(280 * (0.5 + 0.5 * math.sin(t * 3)))
    d.rounded_rectangle([ex, 500, ex + 70, 540], radius=8, fill=(251, 113, 133), outline=DARK, width=3)
    if lp > 0.8:  # kertas sobek
        d.line([(360, 480), (370, 560), (355, 640)], fill=DARK, width=3)

def prop_magnifier(d, t, lp, p):
    d.rectangle([200, 520, 520, 660], fill=(255, 255, 255), outline=DARK, width=3)
    d.ellipse([290, 560, 330, 600], fill=CORAL)  # kesalahan kecil di kertas
    lx = 360 + int(60 * math.sin(t * 0.8))
    ly = 580
    r = 90 + int(20 * lp)
    d.ellipse([lx - r, ly - r, lx + r, ly + r], outline=TEAL, width=6)
    d.ellipse([lx - r, ly - r, lx + r, ly + r], fill=(94, 234, 212, 40))
    d.line([(lx + r * 0.7, ly + r * 0.7), (lx + r + 50, ly + r + 50)], fill=TEAL, width=10)
    dr = int(20 + 40 * lp)  # kesalahan terlihat raksasa lewat kaca
    d.ellipse([lx - dr, ly - dr, lx + dr, ly + dr], fill=CORAL)

def prop_hourglass(d, t, lp, p):
    hourglass(d, 360, 520, 130, 260, lp, t)
    lab = "WAKTU REVISI" if lp < 0.85 else "SELESAI — LETAKKAN PENA"
    f = font(28)
    d.text((360 - d.textlength(lab, font=f) / 2, 700), lab, font=f, fill=TEAL if lp < 0.85 else GREEN)

def prop_envelope(d, t, lp, p):
    d.rounded_rectangle([200, 480, 520, 640], radius=10, fill=(230, 200, 150), outline=DARK, width=3)
    d.polygon([(200, 480), (520, 480), (360, 580)], outline=DARK, width=3)
    ly = int(lerp(0, -120, clamp(lp * 1.2)))
    d.rectangle([240, 460 + ly, 480, 580 + ly], fill=(255, 255, 255), outline=DARK, width=3)
    line = p.get("line", "Kirim versi pertamamu.")
    f = font(22)
    d.text((260, 500 + ly), line, font=f, fill=DARK)
    if lp > 0.7:  # amplop melayang pergi
        d.polygon([(560, 400), (600, 380), (640, 420)], fill=YELLOW, outline=DARK)

def prop_plant(d, t, lp, p):
    h = int(40 + 160 * lp)
    d.line([(360, 700), (360, 700 - h)], fill=GREEN, width=8)
    for k in range(3):
        if lp > (k + 1) * 0.25:
            yy = 700 - h * (0.3 + k * 0.25)
            d.ellipse([360 - 40 + k * 10, yy - 16, 360 - 4 + k * 10, yy + 16], fill=GREEN, outline=DARK, width=2)
            d.ellipse([360 + 4 - k * 10, yy - 16, 360 + 40 - k * 10, yy + 16], fill=GREEN, outline=DARK, width=2)
    d.polygon([(300, 700), (420, 700), (400, 780), (320, 780)], fill=(180, 120, 80), outline=DARK, width=3)

def prop_battery(d, t, lp, p):
    frac = p.get("fill", False)
    f0, f1 = (0.08, 0.55) if frac else (0.95, 0.08)
    f = lerp(f0, f1, clamp(lp))
    battery(d, 210, 480, 300, 120, f, "BATERAI", GREEN if f > 0.3 else CORAL,
            blink=(f < 0.25), t=t)
    lab = p.get("label", "")
    if lab:
        ff = font(26)
        d.text((360 - d.textlength(lab, font=ff) / 2, 640), lab, font=ff, fill=WHITE)

def prop_deskcold(d, t, lp, p):
    desk(d)
    d.rectangle([200, 560, 440, 700], fill=(60, 70, 90), outline=WHITE, width=3)
    d.rectangle([220, 580, 420, 660], fill=(120, 160, 200))
    cup_tea(d, 520, 640, steam=False, t=t)
    d.text((520 - d.textlength("dingin", font=font(20, False)) / 2, 700),
           "dingin", font=font(20, False), fill=MUTED)

def prop_sieve(d, t, lp, p):
    good = p.get("good", ["jelas", "tepat waktu", "sabar"])
    d.polygon([(240, 420), (480, 420), (360, 560)], outline=WHITE, width=4)
    d.line([(240, 420), (480, 420)], fill=WHITE, width=4)
    for k, g in enumerate(good):
        if lp > (k + 1) * 0.25:
            yy = 600 + k * 40
            f = font(24)
            d.text((360 - d.textlength(g, font=f) / 2, yy), g, font=f, fill=GREEN)
    fy = int((t * 80) % 120)
    d.ellipse([352, 560 + fy, 368, 576 + fy], fill=MUTED)

def prop_shield(d, t, lp, p):
    s = 1.0 - 0.5 * lp
    w, h = int(150 * s), int(180 * s)
    cx, cy = 360, 560
    d.polygon([(cx - w//2, cy - h//2), (cx + w//2, cy - h//2), (cx + w//2, cy),
               (cx, cy + h//2), (cx - w//2, cy)], fill=TEAL, outline=DARK, width=4)
    d.text((cx - d.textlength("tenang", font=font(24)) / 2, cy - 14), "tenang", font=font(24), fill=DARK)

def prop_door(d, t, lp, p):
    d.rounded_rectangle([230, 380, 490, 700], radius=12, fill=(60, 40, 30), outline=WHITE, width=4)
    open_w = int(lerp(0, 200, clamp(lp)))
    d.rectangle([250, 400, 250 + open_w, 680], fill=YELLOW)
    for k in range(5):
        yy = 420 + k * 50
        d.line([(250, yy), (250 + open_w, yy + 20)], fill=(253, 230, 138, 120), width=4)
    d.ellipse([450, 520, 470, 540], fill=YELLOW)

def prop_eyes(d, t, lp, p):
    n = 6
    for k in range(n):
        x = 150 + (k % 3) * 210
        y = 400 + (k // 3) * 140
        s = 1.0 - 0.4 * lp
        r = int(34 * s)
        if (t * 1.2 + k * 0.7) % 3.7 < 0.15:
            d.line([(x - r, y), (x + r, y)], fill=WHITE, width=4)
        else:
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255), outline=DARK, width=3)
            d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=DARK)

def prop_spotlight(d, t, lp, p):
    w = int(lerp(120, 420, clamp(lp)))
    d.polygon([(360 - 40, 300), (360 + 40, 300), (360 + w//2, 700), (360 - w//2, 700)],
              fill=(253, 230, 138, 60))
    d.ellipse([330, 300, 390, 330], fill=YELLOW)
    if lp > 0.6:
        for x in (150, 570):
            d.ellipse([x - 20, 640, x + 20, 700], fill=MUTED, outline=DARK, width=2)
            d.ellipse([x - 14, 610, x + 14, 644], fill=SKIN, outline=DARK, width=2)

def prop_mountain(d, t, lp, p):
    h = int(lerp(320, 120, clamp(lp)))
    d.polygon([(150, 700), (360, 700 - h), (570, 700)], fill=(90, 110, 130), outline=WHITE, width=3)
    d.polygon([(330, 700 - h), (360, 700 - h), (390, 700 - h + 30)], fill=(255, 255, 255))
    if lp > 0.5:
        for k in range(3):
            x = 220 + k * 120
            d.polygon([(x - 30, 700), (x, 640), (x + 30, 700)], fill=(120, 140, 160), outline=DARK, width=2)

def prop_stairs(d, t, lp, p):
    for k in range(3):
        d.rectangle([180 + k * 120, 700 - (k + 1) * 60, 300 + k * 120, 700 - k * 60],
                    fill=CARD, outline=WHITE, width=3)
    d.text((360 - d.textlength("1 tangga dulu", font=font(24, False)) / 2, 740),
           "1 tangga dulu", font=font(24, False), fill=MUTED)

def prop_speaker(d, t, lp, p):
    cx, cy = 360, 520
    r = int(lerp(90, 30, clamp(lp)))
    d.polygon([(cx - 60, cy - 30), (cx - 10, cy - 30), (cx + 50, cy - 80), (cx + 50, cy + 80),
               (cx - 10, cy + 30), (cx - 60, cy + 30)], fill=(200, 170, 220), outline=DARK, width=3)
    for k in range(3):
        rr = r + 30 + k * 26 + int((t * 40) % 26)
        a = max(0, 160 - k * 50)
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], -50, 50, fill=(251, 113, 133, a), width=4)
    lab = p.get("label", "Si Kritikus")
    f = font(26)
    d.text((360 - d.textlength(lab, font=f) / 2, 660), lab, font=f, fill=WHITE)

def prop_chairs(d, t, lp, p):
    for x in (230, 490):
        d.rectangle([x - 50, 620, x + 50, 700], fill=(120, 90, 60), outline=DARK, width=3)
        d.rectangle([x - 50, 520, x - 30, 620], fill=(120, 90, 60), outline=DARK, width=3)
    toon(d, 490, 700, s=0.9, phase=t * 1.5, pose="sit", mood="smile", brows="flat", blink=blink(t))
    if lp > 0.4:
        bubble(d, 490, 420, 80, p.get("say", "Aku dengar kamu."), t)

def prop_strings(d, t, lp, p):
    cards = p.get("cards", ["rencana", "jadwal", "orang lain"])
    for k, c in enumerate(cards):
        x = 180 + k * 180
        y = 400 + (k % 2) * 40
        snap = (k == 1 and lp > 0.5)
        if not snap:
            d.line([(360, 780), (x, y + 40)], fill=MUTED, width=3)
        d.rounded_rectangle([x - 70, y - 30, x + 70, y + 30], radius=10, fill=CARD,
                            outline=WHITE if not snap else CORAL, width=3)
        f = font(20)
        tw = d.textlength(c, font=f)
        d.text((x - tw / 2, y - 10), c, font=f, fill=WHITE)

def prop_circles(d, t, lp, p):
    r1 = 70 + int(10 * lp)
    d.ellipse([360 - r1, 420 - r1, 360 + r1, 420 + r1], outline=TEAL, width=5)
    f = font(22)
    d.text((360 - d.textlength("BISA", font=f) / 2, 408), "BISA", font=f, fill=TEAL)
    r2 = 150
    d.ellipse([360 - r2, 420 - r2, 360 + r2, 420 + r2], outline=MUTED, width=3)
    d.text((360 - d.textlength("TIDAK BISA", font=f) / 2, 250), "TIDAK BISA", font=f, fill=MUTED)

def prop_boat(d, t, lp, p):
    for k in range(3):
        yy = 620 + k * 40
        d.arc([120, yy - 20, 600, yy + 20], 0, 180, fill=TEAL, width=4)
    bx = int(lerp(180, 540, clamp(lp)))
    by = 560 + int(6 * math.sin(t * 2))
    d.polygon([(bx - 40, by), (bx + 40, by), (bx + 20, by + 26), (bx - 20, by + 26)],
              fill=(255, 255, 255), outline=DARK, width=3)
    d.polygon([(bx, by - 44), (bx, by), (bx + 30, by)], fill=YELLOW, outline=DARK, width=2)

def prop_table(d, t, lp, p):
    desk(d, y=640)
    cup_tea(d, 240, 580, steam=True, t=t)
    sun(d, 360, 560, 36, t, ray_spin=1.0)
    bubble(d, 500, 540, 52, "terima kasih", t)
    pr = 30 + int(6 * math.sin(t * 2))
    d.ellipse([360 - pr, 600 - 8, 360 + pr, 600 + 8], outline=CORAL, width=4)
    f = font(20)
    d.text((360 - d.textlength("piring kosong", font=f) / 2, 620), "piring kosong", font=f, fill=CORAL)

def prop_jar(d, t, lp, p):
    d.rounded_rectangle([280, 480, 440, 680], radius=16, fill=(30, 80, 90), outline=WHITE, width=4)
    n = min(3, int(lp * 4))
    for k in range(n):
        x = 320 + k * 40
        y = 620 - k * 30
        d.polygon([(x, y - 16), (x + 5, y - 5), (x + 16, y - 5), (x + 8, y + 3),
                   (x + 11, y + 14), (x, y + 8), (x - 11, y + 14), (x - 8, y + 3),
                   (x - 16, y - 5), (x - 5, y - 5)], fill=YELLOW)
    d.text((360 - d.textlength("3 hal baik", font=font(24, False)) / 2, 700),
           "3 hal baik", font=font(24, False), fill=MUTED)

def prop_phonemsg(d, t, lp, p):
    phone(d, 300, 560, glow=0.4 + 0.3 * math.sin(t * 2))
    d.rounded_rectangle([380, 460, 620, 560], radius=16, fill=(255, 255, 255), outline=DARK, width=3)
    if lp < 0.6:
        for k in range(3):
            r = 5 + 2 * math.sin(t * 4 + k)
            d.ellipse([420 + k * 30 - r, 500 - r, 420 + k * 30 + r, 500 + r], fill=MUTED)
    else:
        f = font(20)
        d.text((400, 495), "Terima kasih ya!", font=f, fill=DARK)
        d.text((560, 560), "✓✓", font=font(28), fill=GREEN)

def prop_columns(d, t, lp, p):
    d.rectangle([150, 420, 350, 680], fill=(255, 255, 255), outline=DARK, width=3)
    d.rectangle([370, 420, 570, 680], fill=(255, 255, 255), outline=DARK, width=3)
    f = font(22)
    d.text((250 - d.textlength("FAKTA", font=f) / 2, 440), "FAKTA", font=f, fill=TEAL)
    d.text((470 - d.textlength("TAKUT", font=f) / 2, 440), "TAKUT", font=f, fill=CORAL)
    for k in range(3):
        if lp > (k + 1) * 0.25:
            yy = 500 + k * 50
            d.ellipse([430, yy, 510, yy + 26], fill=CORAL, outline=DARK, width=2)

PROPS = {"clock": prop_clock, "thought": prop_thought, "calendar": prop_calendar,
         "paper": prop_paper, "bag": prop_bag, "tea": prop_tea, "timer": prop_timer,
         "trophy": prop_trophy, "scale": prop_scale, "box": prop_box, "mirror": prop_mirror,
         "bench": prop_bench, "erase": prop_erase, "magnifier": prop_magnifier,
         "hourglass": prop_hourglass, "envelope": prop_envelope, "plant": prop_plant,
         "battery": prop_battery, "deskcold": prop_deskcold, "sieve": prop_sieve,
         "shield": prop_shield, "door": prop_door, "eyes": prop_eyes, "spotlight": prop_spotlight,
         "mountain": prop_mountain, "stairs": prop_stairs, "speaker": prop_speaker,
         "chairs": prop_chairs, "strings": prop_strings, "circles": prop_circles,
         "boat": prop_boat, "table": prop_table, "jar": prop_jar, "phonemsg": prop_phonemsg,
         "columns": prop_columns}

def char_plan(spec_scene, lp):
    """Pilih (pose, mood, brows, face_dx) dari rencana karakter berdasarkan lp."""
    plan = spec_scene.get("char", [("stand", "smile", "flat", 0)])
    idx = min(len(plan) - 1, int(lp * len(plan)))
    return plan[idx]

def char_xy(spec_scene, lp):
    mode = spec_scene.get("char_move", "static")
    if mode == "walk_right":
        return int(lerp(200, 520, clamp(lp))), 1080
    if mode == "climb":
        return int(lerp(220, 500, clamp(lp))), int(lerp(1080, 900, clamp(lp)))
    if mode == "walk_left":
        return int(lerp(520, 200, clamp(lp))), 1080
    return 360, 1080

def frame(t):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    si, lp = seg_idx(bounds, t)
    cam_mode = "push"
    cam_cx, cam_cy = 360, 600
    if si < 8:
        pill(d, 360, 48, "RUANG HEALING", font(26), TEAL, (14, 42, 51))
    dust(d, t, seed=si + 1, n=12)

    if si < 7:
        sc = SPEC["scenes"][si]
        cam_mode = sc.get("cam", "push")
        _y = 110
        _y = draw_title(d, 360, _y, [(tx, globals()[c]) for tx, c in sc["title"]], sc.get("size", 40))
        PROPS[sc["prop"]](d, t, lp, sc.get("params", {}))
        if sc["prop"] != "timer":
            pose, mood, brows, fdx = char_plan(sc, lp)
            if "char_pos" in sc:
                cx, cy = sc["char_pos"]
            else:
                cx, cy = char_xy(sc, lp)
            toon(d, cx, cy, s=sc.get("char_s", 0.95), phase=t * 2, pose=pose, mood=mood, brows=brows,
                 face_dx=fdx, blink=blink(t))
        if "extra" in sc:
            text_block(d, 360, sc.get("extra_y", 780), sc["extra"], font(28, False), MUTED)
        if sc["prop"] == "timer":
            toon(d, 360, 1020, s=1.0, phase=t, pose="sit", mood="sleep", brows="flat")
            text_block(d, 360, 1070, ["Tarik napas pelan..."], font(30, False), MUTED)
    elif si == 7:  # penutup (S7): matahari terbit + tagline
        sc = SPEC["scenes"][7]
        warm = lerp_col(BG, (24, 56, 48), lp)
        d.rectangle([0, 0, W, H], fill=warm)
        pill(d, 360, 48, "RUANG HEALING", font(26), TEAL, (14, 42, 51))
        d.rounded_rectangle([90, 330, 300, 560], radius=14, fill=(30, 80, 90), outline=WHITE, width=4)
        sun(d, 195, 480, 42, t, ray_spin=2.0)
        _y = 120
        _y = draw_title(d, 360, _y, [(tx, globals()[c]) for tx, c in sc["title"]], 42)
        if sc.get("prop"):
            PROPS[sc["prop"]](d, t, lp, sc.get("params", {}))
        toon(d, 360, 950, s=0.95, phase=t * 1.5, pose="write", mood="smile", brows="flat", blink=blink(t))
        pill(d, 360, 960, "RUANG HEALING", font(30), TEAL, (14, 42, 51))
        text_block(d, 360, 1025, ["Solusi Hadir Jika Pikiran", "Tenang dan Jernih"], font(26, False), MUTED)
        cam_mode = "zoomout"
    else:  # tail
        pill(d, 360, 480, "RUANG HEALING", font(40), TEAL, (14, 42, 51))
        text_block(d, 360, 600, ["Solusi Hadir Jika Pikiran", "Tenang dan Jernih"], font(36, False), MUTED)
        text_block(d, 360, 760, ["Sampai jumpa di video berikutnya."], font(30), YELLOW)
        text_block(d, 360, 900, ["Konten edukasi umum — bukan pengganti konseling."], font(22, False), MUTED)
        cam_mode = "push"

    out = camera(img, t, bounds, cam_mode, cam_cx, cam_cy)
    d2 = ImageDraw.Draw(out, "RGBA")
    if si < 9:
        draw_subtitle(d2, t, SENTS, LEAD)
    d2.rectangle([0, H - 14, W, H], fill=CARD)
    d2.rectangle([0, H - 14, W * clamp(t / DUR), H], fill=TEAL)
    return out

def main():
    dip_a, dip_b = bounds[6], bounds[7]
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", NAR, "-stream_loop", "-1", "-i", MUS,
           "-filter_complex",
           f"[1:a]adelay=700|700,apad[a0];"
           f"[2:a]atrim=0:{DUR},volume='0.06*if(between(t,{dip_a:.1f},{dip_b:.1f}),0.5,1)':eval=frame,afade=t=out:st={DUR-2}:d=2[mus];"
           "[a0][mus]amix=inputs=2:duration=first:normalize=0[aout]",
           "-map", "0:v", "-map", "[aout]", "-t", str(DUR),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    N = FPS * DUR
    for i in range(N):
        img = frame(i / FPS)
        try:
            p.stdin.write(img.tobytes())
        except BrokenPipeError:
            break
        if i % 480 == 0:
            print(f"frame {i}/{N} t={i/FPS:.1f}s", flush=True)
    p.stdin.close(); p.wait()
    print("ffmpeg rc", p.returncode)
    if p.returncode != 0:
        sys.exit(p.returncode)

if __name__ == "__main__":
    main()
