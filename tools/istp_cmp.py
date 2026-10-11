# -*- coding: utf-8 -*-
"""ISTP 风衣修复：原版 / 结构修复 / 表面均匀化 三版对照（全身 + 肩部 + 下摆）。"""
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

G = "assets/char/_gen/char_ISTP_v2"
DEL = "_deliver"
os.makedirs(DEL, exist_ok=True)

items = [
    ("原版 1024", "assets/char/istp.png"),
    ("结构修复 1536", os.path.join(G, "istp_v1.png")),
    ("+ 表面均匀化 1536", os.path.join(G, "istp_v1_even5.png")),
]

def font(sz):
    for p in ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()

F_T = font(26)
F_S = font(20)

CELL_W, GAP, PAD = 470, 14, 18
BOX_FULL = (0.0, 0.0, 1.0, 1.0)
BOX_SH = (0.24, 0.12, 0.64, 0.37)     # 观者右肩：原撕裂破洞处
BOX_HEM = (0.46, 0.50, 0.92, 0.82)    # 观者右下摆：原磨白碎裂处

def load_full(p, w):
    im = Image.open(p).convert("RGB")
    h = int(w * im.height / im.width)
    return im.resize((w, h), Image.LANCZOS)

def load_crop(p, box, w, hh):
    im = Image.open(p).convert("RGB")
    W, H = im.size
    c = im.crop((int(box[0] * W), int(box[1] * H), int(box[2] * W), int(box[3] * H)))
    # 等比例缩放到指定高度
    h = hh
    ww = int(h * c.width / c.height)
    c = c.resize((ww, h), Image.LANCZOS)
    if ww > w:                      # 过宽则按宽裁剪居中
        left = (ww - w) // 2
        c = c.crop((left, 0, left + w, h))
    return c

full_h = int(CELL_W * 1536 / 1024)
sh_h = 300
hem_h = 330
HEAD_Y, HEAD_H = 10, 48

W_TOT = PAD * 2 + CELL_W * 3 + GAP * 2
H_TOT = HEAD_Y + HEAD_H + 44 + full_h + 40 + sh_h + 40 + hem_h + PAD

canvas = Image.new("RGB", (W_TOT, H_TOT), (250, 250, 252))
dr = ImageDraw.Draw(canvas)

def paste_row(y, h, box, tag, mode="crop"):
    x = PAD
    dr.text((PAD, y - 32), tag, font=F_S, fill=(96, 96, 108))
    for name, path in items:
        if mode == "full":
            img = load_full(path, CELL_W)
        else:
            img = load_crop(path, box, CELL_W, h)
        bx = x + (CELL_W - img.width) // 2
        canvas.paste(img, (bx, y))
        dr.rectangle([x - 1, y - 1, x + CELL_W, y + h], outline=(214, 214, 220))
        dr.text((x + 8, y + 8), name, font=F_T, fill=(30, 30, 40))
        x += CELL_W + GAP
    return y + h + 40

dr.text((PAD, HEAD_Y), "ISTP 猎手 · 风衣残破修复", font=font(30), fill=(20, 20, 30))
y = HEAD_Y + HEAD_H + 44
y = paste_row(y, full_h, BOX_FULL, "① 全身", mode="full")
y = paste_row(y, sh_h, BOX_SH, "② 肩部特写（原撕裂处）")
y = paste_row(y, hem_h, BOX_HEM, "③ 下摆特写（原磨白碎裂处）")

out = os.path.join(DEL, "ISTP_风衣修复_三版对照.png")
canvas.save(out)
print("->", out, canvas.size)

# 锐度对比
def grad(p, w=1024):
    """统一缩到同一宽度再测，避免跨分辨率误比。"""
    im = Image.open(p).convert("L")
    im = im.resize((w, int(w * im.height / im.width)), Image.LANCZOS)
    a = np.array(im, dtype=np.float32)
    gx = cv2.Sobel(a, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(a, cv2.CV_32F, 0, 1, ksize=3)
    return float(np.mean(np.sqrt(gx ** 2 + gy ** 2)))

print("— 统一归一化到 1024px 宽后测量 —")
for name, path in items:
    print("平均梯度 %-16s = %.3f" % (name, grad(path)))
