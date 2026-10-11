# -*- coding: utf-8 -*-
"""把整页长图切段并拼成总览网格，便于一次性检查全站布局。"""
import os
from PIL import Image, ImageDraw

SRC = "_shots/site/full.png"
DST = "_shots/site/overview.png"

im = Image.open(SRC).convert("RGB")
W, H = im.size
print("full size =", W, "x", H)

SEG = 1750
n = (H + SEG - 1) // SEG
tiles = []
for i in range(n):
    t = im.crop((0, i * SEG, W, min(H, (i + 1) * SEG)))
    w = 430
    h = int(t.height * w / t.width)
    tiles.append(t.resize((w, h), Image.LANCZOS))

cols = 4
rows = (n + cols - 1) // cols
cw, gap, pad = 430, 8, 10
th = max(t.height for t in tiles)
canvas = Image.new("RGB", (pad * 2 + cols * cw + (cols - 1) * gap,
                           pad * 2 + rows * th + (rows - 1) * gap), (238, 238, 242))
dr = ImageDraw.Draw(canvas)
for i, t in enumerate(tiles):
    r, c = divmod(i, cols)
    x = pad + c * (cw + gap)
    y = pad + r * (th + gap)
    canvas.paste(t, (x, y))
    dr.rectangle([x - 1, y - 1, x + cw, y + th], outline=(206, 206, 212))
canvas.save(DST)
print("segments =", n, "->", DST, canvas.size)
