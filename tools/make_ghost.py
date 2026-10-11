# -*- coding: utf-8 -*-
"""Mana 背景幽灵层：脸到胸口的特写，保留原色，仅椭圆羽化（不做灰度/双色调）。"""
from PIL import Image, ImageFilter
import numpy as np

SRC = 'assets/char/mana.png'
BOX = (170, 40, 880, 690)      # 脸 → 胸口
SCALE = 2
FEATHER_IN, FEATHER_OUT = 0.70, 1.06

src = Image.open(SRC).convert('RGBA')
out = src.crop(BOX)
out = out.resize((out.width * SCALE, out.height * SCALE), Image.LANCZOS)
W, H = out.size

yy, xx = np.mgrid[0:H, 0:W]
cx, cy = W / 2.0, H * 0.50
rx, ry = W * 0.60, H * 0.62
r = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
t = np.clip((r - FEATHER_IN) / (FEATHER_OUT - FEATHER_IN), 0, 1)
feather = 1 - (t * t * (3 - 2 * t))

arr = np.array(out).astype(np.float32)
arr[:, :, 3] *= feather
res = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGBA')
res = res.filter(ImageFilter.GaussianBlur(0.6))
res.save('assets/char/mana_ghost.png')
print('saved', res.size)
