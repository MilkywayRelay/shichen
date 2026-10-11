# -*- coding: utf-8 -*-
"""识尘 · Mana 重绘稿(B)白底抠透 + 底部轻盈渐隐

白底抠图的坑与黑底相反：明亮的底色与白色衣袍同为高亮度，
所以不能全局阈值，只能从边框泛洪，只清"与画布边缘连通的亮区"。
边缘朝白混色 -> 用反预乘还原，去掉白描边。
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASE = r"C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen"
_name = sys.argv[1] if len(sys.argv) > 1 else "_mana_B_raw.png"
SRC = os.path.join(BASE, "assets/char", _name)
OUT = os.path.join(BASE, "assets/char/mana.png")
PREV = os.path.join(BASE, "assets/char/_mana_preview.png")

im = Image.open(SRC).convert("RGB")
w, h = im.size
rgb0 = np.asarray(im).astype(np.float32)
lum = Image.fromarray(rgb0.astype(np.uint8)).convert("L")

# ---- 1. 亮区候选（= 白底） ----
WHITE_T = 250
# 先在外围补 3px 白边再泛洪：保证种子点一定落在背景上，
# 否则 (w//2,0)/(0,h//2) 这类点可能正好压到人物身上，把人物当背景填掉。
PAD = 3
g = Image.new("L", (w + PAD * 2, h + PAD * 2), 255)
g.paste(lum.point(lambda v: 255 if v > WHITE_T else 0), (PAD, PAD))
ImageDraw.floodfill(g, (0, 0), 128, thresh=0)
gate = g.crop((PAD, PAD, PAD + w, PAD + h))

bg = gate.point(lambda v: 255 if v == 128 else 0)
# 稍微外扩 1px，避免留下白描边
bg = bg.filter(ImageFilter.MaxFilter(3))
alpha = (255 - np.asarray(bg).astype(np.float32)) / 255.0
alpha = np.clip(alpha * 1.06, 0.0, 1.0)          # 把半透的软边稍微推实
print("transparent ratio: %.1f%%" % (100.0 * (alpha < 0.02).mean()))

# ---- 2. 反预乘：pixel = a*true + (1-a)*255（对着白底） ----
a3 = np.maximum(alpha, 1e-3)[..., None]
rgb = np.clip((rgb0 - (1.0 - a3) * 255.0) / a3, 0.0, 255.0)

# ---- 3. 底部轻盈渐隐（裙摆融进空气） ----
yy = np.arange(h, dtype=np.float32)[:, None] / float(h - 1)
START, END = 0.90, 1.0
alpha = alpha * (1.0 - 0.75 * np.clip((yy - START) / (END - START), 0.0, 1.0)) * 0.985

out = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA")
out.putalpha(Image.fromarray((np.clip(alpha, 0, 1) * 255).astype(np.uint8)))

bbox = out.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
pad_x = int((bbox[2] - bbox[0]) * 0.035)
pad_y = int((bbox[3] - bbox[1]) * 0.018)
out = out.crop((
    max(0, bbox[0] - pad_x), max(0, bbox[1] - pad_y),
    min(w, bbox[2] + pad_x), min(h, bbox[3] + pad_y),
))
out.save(OUT, "PNG")
print("saved", OUT, out.size, round(os.path.getsize(OUT) / 1024, 1), "KB")

bgw = Image.new("RGB", out.size, (250, 249, 246))
bgw.paste(out, (0, 0), out)
p = bgw.copy(); p.thumbnail((420, 680), Image.LANCZOS)
p.save(PREV)
print("saved", PREV, p.size)
