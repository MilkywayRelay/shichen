# -*- coding: utf-8 -*-
"""INFJ 定稿 v3 —— 肤质修复（两层保边平滑）+ 非皮肤区保持原有锐化

思路：
  旧交付在整张图上做了 UnsharpMask + 中间调对比，那会把脸上的斑块一起放大。
  这次：皮肤区用「两层保边平滑」的干净结果，皮肤以外的区域沿用原来的锐化，
  两者用羽化掩膜合成 -> 脸干净、头发大衣依旧锐利。
"""
import os
import sys
import numpy as np
import cv2
from PIL import Image, ImageFilter, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from skin_smooth import build_skin_mask  # noqa

G17 = os.path.join(ROOT, "assets", "char", "_gen", "char_INFJ_v17")
HD = os.path.join(ROOT, "assets", "char", "_hd")
OUT = os.path.join(ROOT, "_deliver")
os.makedirs(HD, exist_ok=True)


def grad(im):
    a = np.asarray(im.convert("L")).astype(np.float32)
    return round(float(abs(np.diff(a, axis=0)).mean() + abs(np.diff(a, axis=1)).mean()), 2)


raw = Image.open(os.path.join(G17, "v17b_fixface.png")).convert("RGB")
skin = Image.open(os.path.join(G17, "v17e_skin_smooth.png")).convert("RGB")
assert raw.size == skin.size

mask = build_skin_mask(np.asarray(raw))
w = mask[..., None]

# 非皮肤区：沿用原来的锐化配方
sharp = raw.filter(ImageFilter.UnsharpMask(radius=1.0, percent=62, threshold=2))
s = np.asarray(sharp).astype(np.float32)
k = np.asarray(skin).astype(np.float32)
final15 = (s * (1 - w) + k * w).round().clip(0, 255).astype(np.uint8)
fin = Image.fromarray(final15)
print("1536 最终 g =", grad(fin), " (原皮肤区 g =", grad(skin), ")")

p1536 = os.path.join(HD, "INFJ_v17_skin_1536.png")
fin.save(p1536)

big = fin.resize((2048, 3072), Image.LANCZOS)
big = big.filter(ImageFilter.UnsharpMask(radius=1.0, percent=55, threshold=2))
p2048 = os.path.join(HD, "INFJ_v17_skin_2048.png")
big.save(p2048)

# ---------- 对照图 ----------
FB = (690, 285, 990, 555)
a = raw.crop(FB)
b = fin.crop(FB)
try:
    F = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 20)
except Exception:
    F = ImageFont.load_default()
GAP = 44
canvas = Image.new("RGB", (a.width * 2 + GAP, a.height + 46), "white")
cd = ImageDraw.Draw(canvas)
cd.text((8, 12), "修复前：脸上一块块发白 / 发灰", fill=(185, 30, 30), font=F)
cd.text((a.width + GAP - 8 + 8, 12), "修复后：肤色均匀、线稿保留", fill=(20, 125, 60), font=F)
canvas.paste(a, (0, 44))
canvas.paste(b, (a.width + GAP - 4, 44))
canvas.save(os.path.join(OUT, "立绘概念稿_INFJ_肤质修复对比.png"))

# 4 倍局部（脸颊）
box2 = (710, 370, 880, 500)
s5 = 4
aa = raw.crop(box2).resize(((box2[2] - box2[0]) * s5, (box2[3] - box2[1]) * s5), Image.LANCZOS)
bb = fin.crop(box2).resize(((box2[2] - box2[0]) * s5, (box2[3] - box2[1]) * s5), Image.LANCZOS)
c2 = Image.new("RGB", (aa.width * 2 + GAP, aa.height + 46), "white")
d2 = ImageDraw.Draw(c2)
d2.text((8, 12), "修复前（4×）", fill=(185, 30, 30), font=F)
d2.text((aa.width + GAP - 4, 12), "修复后（4×）", fill=(20, 125, 60), font=F)
c2.paste(aa, (0, 44))
c2.paste(bb, (aa.width + GAP - 4, 44))
c2.save(os.path.join(OUT, "立绘概念稿_INFJ_肤质修复局部4x.png"))

# ---------- 交付 ----------
fin.save(os.path.join(OUT, "立绘概念稿_INFJ_定稿_推荐1536原生.png"))
big.save(os.path.join(OUT, "立绘概念稿_INFJ_定稿_放大2048.png"))
print("delivered ->", OUT)
