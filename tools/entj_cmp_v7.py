# -*- coding: utf-8 -*-
"""ENTJ v7 对照：领花（平板 vs 褶皱）+ 全身（原版 vs 定稿）。"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = "C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen"
G = os.path.join(BASE, "assets/char/_gen/char_ENTJ_v2")
DEL = os.path.join(BASE, "_deliver")
FONT = "C:/Windows/Fonts/msyh.ttc"

OLD = os.path.join(BASE, "assets/char/entj.png")
V6 = os.path.join(G, "entj_v6_final.png")
V7 = os.path.join(G, "Keep_EVERYTHING_identical_to_t_2026-10-11T11-55-09.png")
FINAL = os.path.join(G, "entj_v7_final.png")


def build(items, out, panel_h, crop=None):
    rows = []
    for im, title in items:
        if crop:
            W, H = im.size
            im = im.crop((int(W * crop[0]), int(H * crop[1]), int(W * crop[2]), int(H * crop[3])))
        w = int(im.width * panel_h / im.height)
        rows.append((im.resize((w, panel_h), Image.LANCZOS), title))
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
v6 = Image.open(V6).convert("RGB")
v7 = Image.open(V7).convert("RGB")
v7.save(FINAL, "PNG", optimize=True)
print("final ->", FINAL)

COLLAR = (0.28, 0.08, 0.82, 0.34)

build([(v6, "上一版 · 平平板板的布片"), (v7, "本版 · 带褶皱的法式领花 ★")],
      os.path.join(DEL, "ENTJ_领花_褶皱对照.png"), 620, crop=COLLAR)

build([(old, "原版 · 长发 / 花纹衬衫"), (v7, "定稿 · 低髻碎发 / 白衬衫 + 法式褶领花")],
      os.path.join(DEL, "ENTJ_定稿_全身对照.png"), 980)
