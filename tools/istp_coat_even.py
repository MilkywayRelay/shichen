# -*- coding: utf-8 -*-
"""ISTP 大衣表面浅色斑驳的局部均匀化。
只在大衣（绿色布料）掩膜内、且相对局部底色明显偏亮/偏暗的像素上做修正，
改动全部落在低频层，褶皱明暗与线稿原样保留。
用法: istp_coat_even.py <src> <dst> [strength]
"""
import os
import sys
import numpy as np
import cv2
from PIL import Image

OUT = "assets/char/_gen/char_ISTP_v2"

src = sys.argv[1]
dst = sys.argv[2]
STRENGTH = float(sys.argv[3]) if len(sys.argv) > 3 else 0.75

sp = src if os.path.isabs(src) else os.path.join(OUT, src)
dp = dst if os.path.isabs(dst) else os.path.join(OUT, dst)

im = Image.open(sp).convert("RGB")
rgb = np.array(im)
H, W = rgb.shape[:2]
print("src =", sp, (W, H), "strength =", STRENGTH)

r = rgb[:, :, 0].astype(np.int16)
g = rgb[:, :, 1].astype(np.int16)
b = rgb[:, :, 2].astype(np.int16)
L = 0.299 * r + 0.587 * g + 0.114 * b

# ---- 大衣（绿布料）掩膜 ----
m = (g >= r) & (g >= b) & ((g - np.minimum(r, b)) > 8) & (L < 236) & (L > 20)
m = m.astype(np.uint8) * 255
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
m = cv2.dilate(m, np.ones((11, 11), np.uint8))
m[L > 238] = 0                      # 不吃纯白背景
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
mask = (m > 0)
print("coat mask 像素占比 = %.2f%%" % (100.0 * mask.mean()))

# ---- 局部底色（只统计掩膜内像素的归一化模糊）----
mf = mask.astype(np.float32)
SIG = 26.0
wsum = cv2.GaussianBlur(mf, (0, 0), SIG)
wsum = np.maximum(wsum, 1e-6)

Lf = L.astype(np.float32)
Lbase = cv2.GaussianBlur(Lf * mf, (0, 0), SIG) / wsum
diff = Lf - Lbase

lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
A = lab[:, :, 1]
B = lab[:, :, 2]
Abase = cv2.GaussianBlur(A * mf, (0, 0), SIG) / wsum
Bbase = cv2.GaussianBlur(B * mf, (0, 0), SIG) / wsum

# ---- 选出「异常像素」：相对底色偏亮或偏暗 ----
sel = (np.abs(diff) > 7) & mask
print("异常像素(大衣内) 占比 = %.2f%%" % (100.0 * sel.mean() / max(mask.mean(), 1e-6)))
sel = sel.astype(np.float32)
sel = cv2.GaussianBlur(sel, (0, 0), 2.5)
sel = np.clip(sel * 1.5, 0.0, 1.0)
sel[~mask] = 0

# ---- 修正：把异常像素拉回局部底色（低频层）----
Lnew = Lf - STRENGTH * sel * diff
Anew = A - STRENGTH * sel * (A - Abase)
Bnew = B - STRENGTH * sel * (B - Bbase)

lab2 = lab.copy()
lab2[:, :, 0] = np.clip(Lnew, 0, 255)
lab2[:, :, 1] = np.clip(Anew, 0, 255)
lab2[:, :, 2] = np.clip(Bnew, 0, 255)
out = cv2.cvtColor(lab2.astype(np.uint8), cv2.COLOR_LAB2RGB)

# ---- 掩膜外 0 改动 ----
soft = cv2.GaussianBlur(mf, (0, 0), 1.2)[:, :, None]
soft = np.clip(soft, 0, 1)
res = (out.astype(np.float32) * soft + rgb.astype(np.float32) * (1 - soft))
res = np.clip(res, 0, 255).astype(np.uint8)

changed = np.abs(res.astype(np.int16) - rgb.astype(np.int16)).max(axis=2)
print("实际改动像素占比 = %.2f%%  最大通道差 = %d" % (100.0 * (changed > 0).mean(), changed.max()))

# ---- 处理后残余异常量 ----
L2 = 0.299 * res[:, :, 0] + 0.587 * res[:, :, 1] + 0.114 * res[:, :, 2]
L2b = cv2.GaussianBlur(L2.astype(np.float32) * mf, (0, 0), SIG) / wsum
d2 = L2.astype(np.float32) - L2b
before = float(np.abs(diff[mask]).mean())
after = float(np.abs(d2[mask]).mean())
print("大衣内平均 |偏差| : %.3f -> %.3f  (降 %.1f%%)" % (before, after, 100 * (1 - after / before)))

Image.fromarray(res).save(dp)
print("->", dp)
