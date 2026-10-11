# -*- coding: utf-8 -*-
"""INFJ 定稿 v2：脸部白斑修复 + 温和提清（不做白场抬升）"""
import os
import sys
import numpy as np
import cv2
from PIL import Image, ImageFilter, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from face_patch_fix import FACE_POLY, build_mask, fill  # noqa

G15 = os.path.join(ROOT, "assets", "char", "_gen", "char_INFJ_v15")
G17 = os.path.join(ROOT, "assets", "char", "_gen", "char_INFJ_v17")
HD = os.path.join(ROOT, "assets", "char", "_hd")
OUT = os.path.join(ROOT, "_deliver")
os.makedirs(HD, exist_ok=True)


def grad(im):
    a = np.asarray(im.convert("L")).astype(np.float32)
    return round(float(abs(np.diff(a, axis=0)).mean() + abs(np.diff(a, axis=1)).mean()), 2)


def gentle(im):
    """不再做任何白场抬升（那正是白块的元凶），只留一层极轻的中间调对比"""
    a = np.asarray(im).astype(np.float32)
    a = 128.0 + (a - 128.0) * 1.04
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def repair(path, scale=1.0):
    im = Image.open(path).convert("RGB")
    arr = np.asarray(im)
    L = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    poly = (FACE_POLY.astype(np.float32) * scale).astype(np.int32)
    mask, info = build_mask(L, poly)
    print(f"  {os.path.basename(path)} 修复像素 {info['cand']}")
    return Image.fromarray(fill(arr, mask))


def count_patches(im, scale=1.0):
    """统计脸部残留的孤立白块"""
    arr = np.asarray(im.convert("RGB"))
    L = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    poly = (FACE_POLY.astype(np.float32) * scale).astype(np.int32)
    m, _ = build_mask(L, poly)
    return int(m.sum())


print("== v17 重出版（1536 原生）==")
base17 = repair(os.path.join(G17, "v17a.png"))
print("  修复后残留白块像素:", count_patches(base17))
base17.save(os.path.join(G17, "v17b_fixface.png"))

fin17 = gentle(base17).filter(ImageFilter.UnsharpMask(radius=1.0, percent=62, threshold=2))
p17_1536 = os.path.join(HD, "INFJ_v17_final_1536.png")
fin17.save(p17_1536)
print("  1536 最终 g =", grad(fin17))

big = fin17.resize((2048, 3072), Image.LANCZOS)
big = big.filter(ImageFilter.UnsharpMask(radius=1.0, percent=55, threshold=2))
p17_2048 = os.path.join(HD, "INFJ_v17_final_2048.png")
big.save(p17_2048)

print("== v15 原版（1024，保真备选）==")
base15 = repair(os.path.join(G15, "v15_clean.png"), scale=1024.0 / 1536.0)
print("  修复后残留白块像素:", count_patches(base15, 1024.0 / 1536.0))
base15.save(os.path.join(G15, "v15b_fixface.png"))
fin15 = gentle(base15).filter(ImageFilter.UnsharpMask(radius=1.0, percent=62, threshold=2))
fin15.save(os.path.join(HD, "INFJ_v15b_final_1024.png"))
big15 = fin15.resize((1536, 2304), Image.LANCZOS).filter(
    ImageFilter.UnsharpMask(radius=1.0, percent=55, threshold=2))
big15.save(os.path.join(HD, "INFJ_v15b_final_1536.png"))

# ---------- 交付 ----------
fin17.save(os.path.join(OUT, "立绘概念稿_INFJ_定稿_推荐1536原生.png"))
big.save(os.path.join(OUT, "立绘概念稿_INFJ_定稿_放大2048.png"))
big15.save(os.path.join(OUT, "立绘概念稿_INFJ_保真版_1536.png"))

# 修复对照：上排 1:1 脸部，下排全身
raw17 = Image.open(os.path.join(G17, "v17a.png")).convert("RGB")
FB = (690, 290, 990, 560)
a = raw17.crop(FB)
b = fin17.crop(FB)
try:
    F = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 22)
except Exception:
    F = ImageFont.load_default()
canvas = Image.new("RGB", (a.width * 2 + 40, a.height + 46), "white")
cd = ImageDraw.Draw(canvas)
cd.text((6, 10), "修复前：脸上有硬边白块", fill=(180, 30, 30), font=F)
cd.text((a.width + 34, 10), "修复后：肤色均匀，纹理保留", fill=(20, 120, 60), font=F)
canvas.paste(a, (0, 44))
canvas.paste(b, (a.width + 40, 44))
canvas.save(os.path.join(OUT, "立绘概念稿_INFJ_白斑修复对比.png"))
print("对照图 ->", canvas.size)
