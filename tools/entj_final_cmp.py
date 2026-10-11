# -*- coding: utf-8 -*-
"""ENTJ 定稿对照：原版 vs 新版（全身 + 头部特写）。"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = "C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen"
G = os.path.join(BASE, "assets/char/_gen/char_ENTJ_v2")
DEL = os.path.join(BASE, "_deliver")
FONT = "C:/Windows/Fonts/msyh.ttc"

OLD = os.path.join(BASE, "assets/char/entj.png")
NEW = os.path.join(G, "Keep_EVERYTHING_identical_to_t_2026-10-11T11-47-56.png")
FINAL = os.path.join(G, "entj_v4_final.png")


def build(items, out, panel_h):
    rows = []
    for im, title in items:
        w = int(im.width * panel_h / im.height)
        rows.append((im.resize((w, panel_h), Image.LANCZOS), title))
    gap, pad, bar_h = 22, 22, 46
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
new = Image.open(NEW).convert("RGB")
new.save(FINAL, "PNG", optimize=True)
print("final ->", FINAL)

build([(old, "原版 · 长发披肩 / 花纹衬衫"), (new, "定稿 · 低髻碎发 / 白衬衫 + 领花")],
      os.path.join(DEL, "ENTJ_定稿_全身对照.png"), 960)


def headcrop(im):
    W, H = im.size
    return im.crop((int(W * 0.24), 0, int(W * 0.84), int(H * 0.30)))


build([(headcrop(old), "原版"), (headcrop(new), "定稿")],
      os.path.join(DEL, "ENTJ_定稿_头部特写.png"), 620)
