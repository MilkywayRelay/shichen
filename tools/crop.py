# -*- coding: utf-8 -*-
"""按像素裁剪图片。用法: crop.py <src> <dst> <left> <top> <right> <bottom> [scale]"""
import sys
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
l, t, r, b = (int(x) for x in sys.argv[3:7])
sc = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0

im = Image.open(src).convert("RGB")
W, H = im.size
c = im.crop((max(0, l), max(0, t), min(W, r), min(H, b)))
if sc != 1.0:
    c = c.resize((int(c.width * sc), int(c.height * sc)), Image.LANCZOS)
c.save(dst)
print("src", (W, H), "-> crop", (l, t, r, b), "->", c.size, dst)
