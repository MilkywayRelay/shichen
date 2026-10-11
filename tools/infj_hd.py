# -*- coding: utf-8 -*-
"""INFJ v15 高清化：enhance(已产出) -> 2x LANCZOS -> UnsharpMask"""
import os
import sys
import shutil
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "assets", "char", "_gen", "char_INFJ_v15")
HD = os.path.join(ROOT, "assets", "char", "_hd")
OUT = os.path.join(ROOT, "_deliver")
os.makedirs(HD, exist_ok=True)

src = sys.argv[1] if len(sys.argv) > 1 else None
if not src:
    cands = [f for f in os.listdir(GEN) if f.startswith("processed_image") and f.endswith(".png")]
    cands.sort(key=lambda f: os.path.getmtime(os.path.join(GEN, f)))
    src = os.path.join(GEN, cands[-1]) if cands else None
if not src or not os.path.exists(src):
    raise SystemExit("enhance 结果未找到")
print("增强图:", src)

base = Image.open(os.path.join(GEN, "v15_clean.png")).convert("RGB")
enh = Image.open(src).convert("RGB")
print("原图", base.size, "增强后", enh.size)


def sharpness(im):
    a = np.asarray(im.convert("L")).astype(np.float32)
    return float(np.abs(np.diff(a, axis=0)).mean() + np.abs(np.diff(a, axis=1)).mean())


s0 = sharpness(base)
s1 = sharpness(enh)

# 归档 enhance 版（1x）
p1x = os.path.join(HD, "INFJ_v15_hd_1x.png")
enh.save(p1x)

# 2x 放大 + 锐化
up = enh.resize((enh.width * 2, enh.height * 2), Image.LANCZOS)
up = up.filter(ImageFilter.UnsharpMask(radius=1.6, percent=62, threshold=3))
p2x = os.path.join(HD, "INFJ_v15_hd_2x.png")
up.save(p2x)
s2 = sharpness(up)

print(f"平均梯度  原始 {s0:.2f} -> enhance {s1:.2f} (+{(s1/s0-1)*100:.0f}%) -> 2x {s2:.2f}")
print("1x ->", p1x)
print("2x ->", p2x)

# 交付图 2048
up.save(os.path.join(OUT, "立绘概念稿_INFJ_v15_高清版_2048.png"))

# 对照图：左 1x 原尺寸，右 2x 裁同样区域
box = (170, 90, 600, 700)          # 头部到胸，1x 坐标
a = enh.crop(box)
b = up.crop(tuple(v * 2 for v in box))
H = 700
a = a.resize((int(a.width * H / a.height), H), Image.LANCZOS)
b = b.resize((int(b.width * H / b.height), H), Image.LANCZOS)
canvas = Image.new("RGB", (a.width + b.width + 30, H + 44), "white")
from PIL import ImageDraw, ImageFont
d = ImageDraw.Draw(canvas)
try:
    F = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 22)
except Exception:
    F = ImageFont.load_default()
d.text((6, 10), "enhance 1x  (1024x1536)", fill=(40, 40, 40), font=F)
d.text((a.width + 36, 10), "2x LANCZOS + UnsharpMask  (2048x3072)", fill=(40, 40, 40), font=F)
canvas.paste(a, (0, 40))
canvas.paste(b, (a.width + 30, 40))
canvas.save(os.path.join(OUT, "立绘概念稿_INFJ_v15_高清化对比.png"))
print("对比图已出")
