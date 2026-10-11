# -*- coding: utf-8 -*-
"""INFJ 剑姿方案对照 + v15 背景虚影清理"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "assets", "char", "_gen", "char_INFJ_v15")
SRC = os.path.join(GEN, "Image_to_image_edit_of_an_anim_2026-10-11T03-30-35.png")
CLEAN = os.path.join(GEN, "v15_clean.png")
OUT = os.path.join(ROOT, "_deliver")

# ---------- 1. 清理左上背景残留虚影（x130-316, y415-680，仅抬升极浅灰） ----------
im = Image.open(SRC).convert("RGB")
a = np.asarray(im).astype(np.float32)

x0, y0, x1, y1 = 130, 415, 316, 680
h, w = a.shape[:2]
lum = a[..., :3].mean(axis=2)

sub = lum[y0:y1, x0:x1]
t = np.clip((sub - 228.0) / 10.0, 0.0, 1.0)          # <=228 完全不动，>=238 全白

# 边缘羽化，避免出现硬边
yy, xx = np.mgrid[0:y1 - y0, 0:x1 - x0]
edge = np.minimum.reduce([xx, (x1 - x0 - 1) - xx, yy, (y1 - y0 - 1) - yy]).astype(np.float32)
feather = np.clip(edge / 16.0, 0.0, 1.0)
t = t * feather

patch = a[y0:y1, x0:x1, :3]
a[y0:y1, x0:x1, :3] = patch + (255.0 - patch) * t[..., None]

clean = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
clean.save(CLEAN)
print("cleaned ->", CLEAN)

# ---------- 2. 三版对照 ----------
v13 = Image.open(os.path.join(ROOT, "_deliver", "立绘概念稿_INFJ_v13_后倾反握.png")).convert("RGB")
v14 = Image.open(os.path.join(ROOT, "assets", "char", "_gen", "char_INFJ_v14", "v14a.png")).convert("RGB")
v15 = clean

panels = [
    ("v13  原稿：剑垂直在腿前", v13),
    ("v14  误读：斜跨身前（压腿）", v14),
    ("v15  斜垂身后（腿挡中段）", v15),
]

W_FULL = 380
full_imgs = []
for label, img in panels:
    s = W_FULL / img.width
    full_imgs.append((label, img.resize((W_FULL, int(img.height * s)), Image.LANCZOS)))

# 下半身特写：统一切到胯以下
ZOOM = (90, 400, 950, 1430)   # 1024x1536 坐标系
ZW = 500
zoom_imgs = []
for label, img in panels:
    c = img.crop(ZOOM)
    s = ZW / c.width
    zoom_imgs.append((label, c.resize((ZW, int(c.height * s)), Image.LANCZOS)))

try:
    F = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 20)
    F2 = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 24)
except Exception:
    F = F2 = ImageFont.load_default()

def build(rows, font, gap=24, pad=30, bg="white"):
    cw = max(sum(i.width for _, i in r) + gap * (len(r) - 1) for r in rows)
    rh = [max(i.height for _, i in r) + 46 for r in rows]
    canvas = Image.new("RGB", (cw + pad * 2, sum(rh) + gap * (len(rows) - 1) + pad * 2), bg)
    d = ImageDraw.Draw(canvas)
    y = pad
    for r, hh in zip(rows, rh):
        x = pad
        for label, img in r:
            d.text((x + 4, y + 8), label, fill=(40, 40, 40), font=font)
            canvas.paste(img, (x, y + 42))
            x += img.width + gap
        y += hh + gap
    return canvas

build([full_imgs, zoom_imgs], F).save(os.path.join(OUT, "立绘概念稿_INFJ_剑姿_身前vs身后.png"))
zoom_only = build([zoom_imgs], F2)
zoom_only.save(os.path.join(OUT, "立绘概念稿_INFJ_剑姿_下半身对照.png"))
print("saved cmp")
