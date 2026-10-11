# -*- coding: utf-8 -*-
"""识尘 · 原画预处理
1) istp: 裁掉底部水印
2) mana: 黑底 -> 透明（从边框泛洪，避免抠穿角色内部的暗部）
其余三张原样拷贝。
"""
import os, shutil
from PIL import Image, ImageDraw, ImageFilter

SRC = r"E:/obsidian-vault/DarkBook/10-Projects/01-Current/识尘/角色形象/原画"
DST = r"C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen/assets/char"
os.makedirs(DST, exist_ok=True)

# ---------- 通用拷贝 ----------
for name in ["entj.png", "enfp.png", "isfj.png"]:
    s = os.path.join(SRC, name)
    if os.path.exists(s):
        shutil.copyfile(s, os.path.join(DST, name))
        print("copy  ", name, Image.open(s).size)

# ---------- istp: 裁掉底部水印 ----------
p = os.path.join(SRC, "istp.png")
if os.path.exists(p):
    im = Image.open(p).convert("RGB")
    w, h = im.size
    cut = int(h * 0.945)
    im.crop((0, 0, w, cut)).save(os.path.join(DST, "istp.png"), "PNG")
    print("istp   cropped bottom", h - cut, "px  -> ", im.crop((0, 0, w, cut)).size)

# ---------- mana: 黑底转透明 ----------
p = os.path.join(SRC, "mana.png")
if os.path.exists(p):
    im = Image.open(p).convert("RGB")
    w, h = im.size
    # 亮度掩码：接近纯黑 = 背景候选
    lum = im.convert("L")
    bg = lum.point(lambda v: 255 if v < 46 else 0)
    # 从四角与四边中点泛洪，只把"与边框连通的暗区"判为背景
    seeds = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
             (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]
    for s in seeds:
        try:
            ImageDraw.floodfill(bg, s, 128, thresh=0)
        except Exception as e:
            print("  seed skip", s, e)
    # 背景(128) -> 透明0，其余 -> 不透明255
    alpha = bg.point(lambda v: 0 if v == 128 else 255)
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.7))
    out = im.convert("RGBA")
    out.putalpha(alpha)
    out.save(os.path.join(DST, "mana.png"), "PNG")
    print("mana   matted ->", out.size, "RGBA")

print("\n-- result --")
for f in sorted(os.listdir(DST)):
    print("  ", f, round(os.path.getsize(os.path.join(DST, f)) / 1024, 1), "KB")
