# -*- coding: utf-8 -*-
"""识尘 · Mana 通透化处理（方案 A：以画师原画为底，不做造型改写）

流程
1) 黑底泛洪抠图 -> 透明（只清与边框连通的暗区，不抠穿角色内部）
2) 内缩 1px 去黑边 + 羽化，避免残留黑描边
3) 通透处理：
   - 裙摆/脚踝做柔和渐隐（"将离未离"，呼应欧律狄刻原型）
   - 提升暗部、略降饱和，让画面"发光"而不发闷
4) 裁到内容边界，输出 RGBA
5) 另出白底预览图与新旧对比图
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

BASE = r"C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen"
SRC = os.path.join(BASE, "assets/char/orig_backup/mana.png")
OUT = os.path.join(BASE, "assets/char/mana_ethereal.png")
PREV = os.path.join(BASE, "assets/char/_mana_A_preview.png")
CMP = os.path.join(BASE, "assets/char/_mana_cmp.png")

# ---------- 1. 抠图：亮度斜坡 + 反预乘（黑底） ----------
# 原画是"黑底不透明"，不是预乘 alpha；发丝之间的封闭黑腔泛洪清不掉，
# 所以直接对黑色做亮度斜坡，再把边缘朝黑的反混合还原回来。
im = Image.open(SRC).convert("RGB")
w, h = im.size
LO, HI = 10.0, 58.0
rgb0 = np.asarray(im).astype(np.float32)
lum = rgb0 @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
alpha = np.clip((lum - LO) / (HI - LO), 0.0, 1.0)

# 反预乘：pixel = a * true（对着黑底）=> true = pixel / a
safe = np.maximum(alpha, 1e-3)[..., None]
rgb = np.clip(rgb0 / safe, 0.0, 255.0)
print("transparent ratio: %.1f%%" % (100.0 * (alpha < 0.02).mean()))

# ---------- 2. 通透处理：底部渐隐 ----------
yy = np.arange(h, dtype=np.float32)[:, None] / float(h - 1)
START, END = 0.86, 1.0
fade = 1.0 - 0.90 * np.clip((yy - START) / (END - START), 0.0, 1.0)
# 顶部也极轻地收一点，让头顶不"顶格"
top = 0.93 + 0.07 * np.clip(yy / 0.06, 0.0, 1.0)
alpha = alpha * fade * top * 0.97

# ---------- 3. 调色：提暗部 + 略降饱和（更"发光"） ----------
rgb = 255.0 * np.power(rgb / 255.0, 0.93)                      # 抬暗部
img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
img = ImageEnhance.Color(img).enhance(0.90)                    # 降饱和
img = ImageEnhance.Contrast(img).enhance(0.97)

out = img.convert("RGBA")
out.putalpha(Image.fromarray((np.clip(alpha, 0, 1) * 255).astype(np.uint8)))

# ---------- 4. 裁到内容边界 ----------
bbox = out.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
print("bbox", bbox, "->", (bbox[2] - bbox[0], bbox[3] - bbox[1]))
out = out.crop(bbox)
out.save(OUT, "PNG")
print("saved", OUT, out.size, round(os.path.getsize(OUT) / 1024, 1), "KB")

# ---------- 5. 预览与对比 ----------
BW, BH = 420, 670
def on_white(im_rgba, bg=(250, 249, 246)):
    bgim = Image.new("RGB", im_rgba.size, bg)
    bgim.paste(im_rgba, (0, 0), im_rgba)
    return bgim

prev = on_white(out)
prev.thumbnail((BW, BH), Image.LANCZOS)
prev.save(PREV)
print("saved", PREV, prev.size)

cur = Image.open(os.path.join(BASE, "assets/char/mana.png")).convert("RGB")
cur.thumbnail((BW, BH), Image.LANCZOS)
prev2 = prev.copy()
W = BW * 2 + 30
H = max(cur.height, prev2.height) + 34
sheet = Image.new("RGB", (W, H), (250, 249, 246))
d = ImageDraw.Draw(sheet)
sheet.paste(cur, (10, 30))
sheet.paste(prev2, (BW + 20, 30))
d.text((10, 10), "BEFORE  (v1 AI)", fill=(40, 40, 40))
d.text((BW + 20, 10), "AFTER  (painter art + ethereal)", fill=(160, 120, 40))
sheet.save(CMP)
print("saved", CMP, sheet.size)
