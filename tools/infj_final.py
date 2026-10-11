# -*- coding: utf-8 -*-
"""INFJ 定稿清晰版：v17 原生 1536x2304 提清 + 2048 放大版 + 三版对照"""
import os
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G15 = os.path.join(ROOT, "assets", "char", "_gen", "char_INFJ_v15")
G17 = os.path.join(ROOT, "assets", "char", "_gen", "char_INFJ_v17")
HD = os.path.join(ROOT, "assets", "char", "_hd")
OUT = os.path.join(ROOT, "_deliver")
os.makedirs(HD, exist_ok=True)


def grad(im):
    a = np.asarray(im.convert("L")).astype(np.float32)
    return round(float(abs(np.diff(a, axis=0)).mean() + abs(np.diff(a, axis=1)).mean()), 2)


def clarify(im, hi=238.0, span=14.0, black=8):
    """抬白场去灰雾 + 轻压黑场，保护中间调"""
    a = np.asarray(im).astype(np.float32)
    t = np.clip((a - (hi - span)) / span, 0, 1)
    a = a + (255.0 - a) * t
    a = np.clip((a - black) / (255.0 - black) * 255.0, 0, 255)
    return Image.fromarray(a.astype(np.uint8))


src = Image.open(os.path.join(G17, "v17a.png")).convert("RGB")
print("v17 原生", src.size, "g =", grad(src))

v15 = Image.open(os.path.join(G15, "v15_clean.png")).convert("RGB")
v15c = Image.open(os.path.join(G15, "v15_clarify_2x.png")).convert("RGB")

# ---- 1. 原生 1536 提清 ----
n = clarify(src)
n = n.filter(ImageFilter.UnsharpMask(radius=1.1, percent=72, threshold=2))
p1536 = os.path.join(HD, "INFJ_v17_clarify_1536.png")
n.save(p1536)
print("1536 提清 g =", grad(n))

# ---- 2. 2048 放大版（1.333x Lanczos + 轻 USM，只为出大图，不指望增细节） ----
big = n.resize((2048, 3072), Image.LANCZOS)
big = big.filter(ImageFilter.UnsharpMask(radius=1.0, percent=60, threshold=2))
p2048 = os.path.join(HD, "INFJ_v17_clarify_2048.png")
big.save(p2048)
print("2048 g =", grad(big))

big.save(os.path.join(OUT, "立绘概念稿_INFJ_清晰版_2048.png"))
n.save(os.path.join(OUT, "立绘概念稿_INFJ_清晰版_1536原生.png"))

# ---- 3. 三版对照（同显示高度，含 100% 局部） ----
try:
    F = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 22)
    Fs = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 19)
except Exception:
    F = Fs = ImageFont.load_default()

panels = [
    ("① 旧版 1024 提清到 2048   g=4.78", "（放大不产生细节）", v15c),
    ("② 重出 1536 原生 + 提清   g=%.2f" % grad(n), "（线条真实生成）", n),
]

H = 760
tiles = []
for t, s, im in panels:
    tiles.append((t, s, im.resize((int(im.width * H / im.height), H), Image.LANCZOS)))

# 局部 100% 裁切：脸
FB = (640, 260, 1060, 580) if True else None
zoom = []
for t, s, im in panels:
    sc = im.width / 1024.0
    box = tuple(int(v * sc) for v in (430, 180, 700, 380))
    z = im.crop(box).resize((470, 340), Image.LANCZOS)
    zoom.append(z)
zoom_src = v15.resize((1024, 1536), Image.LANCZOS).crop((430, 180, 700, 380)).resize((470, 340), Image.LANCZOS)

row1_h = H + 46
row2_h = 340 + 46
W = max(sum(z.width for z in zoom) + 24 * (len(zoom)) + 24, sum(tw.width for _, _, tw in tiles) + 24 * len(tiles) + 24)
canvas = Image.new("RGB", (W, row1_h + row2_h + 20), "white")
d = ImageDraw.Draw(canvas)

x = 24
for t, s, im in tiles:
    d.text((x + 4, 10), t, fill=(30, 30, 30), font=F)
    canvas.paste(im, (x, 46))
    x += im.width + 24

y = row1_h + 14
x = 24
d.text((x + 4, y), "脸部 1:1 局部  —— 左：旧放大版（糊）", fill=(30, 30, 30), font=Fs)
canvas.paste(zoom_src, (x, y + 26))
x += zoom_src.width + 24
d.text((x + 4, y), "右：新重出版（清晰）", fill=(30, 30, 30), font=Fs)
canvas.paste(zoom[1], (x, y + 26))

canvas.save(os.path.join(OUT, "立绘概念稿_INFJ_清晰化对比.png"))
print("对照图 ->", canvas.size)
