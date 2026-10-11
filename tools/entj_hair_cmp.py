# -*- coding: utf-8 -*-
"""ENTJ 发型修正：改前 / 低髻 / 低髻+碎发 对照图。"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = "C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen"
G = os.path.join(BASE, "assets/char/_gen/char_ENTJ_v2")
DEL = os.path.join(BASE, "_deliver")
FONT = "C:/Windows/Fonts/msyh.ttc"


def headcrop(im, y0=0.0, y1=0.34):
    W, H = im.size
    return im.crop((int(W * 0.24), int(H * y0), int(W * 0.84), int(H * y1)))


def build(items, out, panel_h):
    """items: [(PIL图, 标题)]"""
    rows = []
    for im, title in items:
        w = int(im.width * panel_h / im.height)
        rows.append((im.resize((w, panel_h), Image.LANCZOS), title))
    gap, pad, bar_h = 20, 22, 44
    W = pad * 2 + sum(r[0].width for r in rows) + gap * (len(rows) - 1)
    H = pad * 2 + bar_h + panel_h + 8
    canvas = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT, 28)
    x = pad
    for im, title in rows:
        d.rectangle([x, pad, x + im.width, pad + bar_h], fill=(247, 247, 248))
        tw = d.textlength(title, font=f)
        d.text((x + (im.width - tw) / 2, pad + 6), title, font=f, fill=(38, 38, 42))
        canvas.paste(im, (x, pad + bar_h + 8))
        d.rectangle([x - 1, pad + bar_h + 7, x + im.width, pad + bar_h + 8 + panel_h],
                    outline=(226, 226, 230), width=1)
        x += im.width + gap
    canvas.save(out, "PNG", optimize=True)
    print("ok ->", out, canvas.size)


old = Image.open(os.path.join(BASE, "assets/char/entj.png")).convert("RGB")
v2 = Image.open(os.path.join(G, "entj_v2_hairfix.png")).convert("RGB")
v3 = Image.open(os.path.join(G, "entj_v3_bangs.png")).convert("RGB")

build([(headcrop(old), "1 原版 · 大量垂发"),
       (headcrop(v2), "2 低髻 · 发际线偏硬"),
       (headcrop(v3), "3 低髻 + 通透碎发 ★")],
      os.path.join(DEL, "ENTJ_发型修正_头部三版对比.png"), 520)

build([(old, "原版 · 长发披肩"), (v3, "新版 · 低髻 + 碎发刘海")],
      os.path.join(DEL, "ENTJ_发型修正_全身对比.png"), 900)
