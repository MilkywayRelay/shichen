# -*- coding: utf-8 -*-
"""ENTJ v8 最终对照：清晰度修复局部放大（v7 vs v8d）+ 全身（原版 vs v8d）。"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = "C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen"
G = os.path.join(BASE, "assets/char/_gen/char_ENTJ_v2")
DEL = os.path.join(BASE, "_deliver")
FONT = "C:/Windows/Fonts/msyh.ttc"

OLD = os.path.join(BASE, "assets/char/entj.png")
V7 = os.path.join(G, "entj_v7_final.png")
V8D = os.path.join(G, "entj_v8d_detail.png")
FINAL = os.path.join(G, "entj_v8_final.png")


def build(items, out, panel_h, crop=None, zoom=1.0):
    rows = []
    for im, title in items:
        if crop:
            W, H = im.size
            im = im.crop((int(W * crop[0]), int(H * crop[1]), int(W * crop[2]), int(H * crop[3])))
        if zoom != 1.0:
            im = im.resize((int(im.width * zoom), int(im.height * zoom)), Image.LANCZOS)
        rows.append((im, title))
    # 统一高
    h = panel_h
    rows = [(im.resize((int(im.width * h / im.height), h), Image.LANCZOS), t) for im, t in rows]
    gap, pad, bar_h = 20, 22, 46
    W = pad * 2 + sum(r[0].width for r in rows) + gap * (len(rows) - 1)
    H = pad * 2 + bar_h + panel_h + 8
    canvas = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT, 30)
    x = pad
    for im, title in rows:
        d.rectangle([x, pad, x + im.width, pad + bar_h], fill=(247, 247, 248))
        tw = d.textlength(title, font=f)
        d.text((x + (im.width - tw) / 2, pad + 7), title, font=f, fill=(38, 38, 42))
        canvas.paste(im, (x, pad + bar_h + 8))
        d.rectangle([x - 1, pad + bar_h + 7, x + im.width, pad + bar_h + 8 + panel_h],
                    outline=(226, 226, 230), width=1)
        x += im.width + gap
    canvas.save(out, "PNG", optimize=True)
    print("ok ->", out, canvas.size)


old = Image.open(OLD).convert("RGB")
v7 = Image.open(V7).convert("RGB")
v8d = Image.open(V8D).convert("RGB")
v8d.save(FINAL, "PNG", optimize=True)
print("final ->", FINAL)

# 脸部放大（眼睛/鼻/唇 —— 最容易看出糊的地方）
FACE = (0.34, 0.05, 0.66, 0.17)
build([(v7, "上一版 v7 · 迭代累积偏软"), (v8d, "本版 · 细节已回填")],
      os.path.join(DEL, "ENTJ_清晰度修复_脸部放大.png"), 620, crop=FACE, zoom=3.0)

build([(old, "原版 · 长发 / 花纹衬衫"), (v8d, "定稿 · 低髻碎发 / 白衬衫 + 法式褶领花")],
      os.path.join(DEL, "ENTJ_定稿_全身对照.png"), 980)
