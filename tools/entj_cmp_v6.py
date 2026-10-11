# -*- coding: utf-8 -*-
"""ENTJ v6 对照：领口三版（金属领针/大蕾丝/小布花边）+ 全身（原版 vs 定稿）。"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = "C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen"
G = os.path.join(BASE, "assets/char/_gen/char_ENTJ_v2")
DEL = os.path.join(BASE, "_deliver")
FONT = "C:/Windows/Fonts/msyh.ttc"

OLD = os.path.join(BASE, "assets/char/entj.png")
V4 = os.path.join(G, "entj_v4_final.png")
V5 = os.path.join(G, "Keep_EVERYTHING_identical_to_t_2026-10-11T11-49-57.png")
V6 = os.path.join(G, "Keep_EVERYTHING_identical_to_t_2026-10-11T11-52-07.png")
FINAL = os.path.join(G, "entj_v6_final.png")


def build(items, out, panel_h, crop=None, font_size=30):
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
    f = ImageFont.truetype(FONT, font_size)
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
v6.save(FINAL, "PNG", optimize=True)
print("final ->", FINAL)

COLLAR = (0.30, 0.09, 0.80, 0.33)

build([(Image.open(V4).convert("RGB"), "① 金属小领针 · 太小"),
       (Image.open(V5).convert("RGB"), "② 大片蕾丝 · 太大太夸张"),
       (v6, "③ 小布花边 · 低调 ★")],
      os.path.join(DEL, "ENTJ_领口_三版对照.png"), 560, crop=COLLAR)

build([(old, "原版 · 长发 / 花纹衬衫"), (v6, "定稿 · 低髻碎发 / 白衬衫 + 小布花边")],
      os.path.join(DEL, "ENTJ_定稿_全身对照.png"), 980)
