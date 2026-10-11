# -*- coding: utf-8 -*-
"""ISTP 大衣浅色灰斑的定向清除（v2）。
改进点：
  1) 掩膜只保留大衣主体的最大连通域，杜绝裤子/围巾被误伤；
  2) 斑块判定 = 「相对局部底色偏亮」且「相对局部底色偏灰」双条件，
     褶皱只是明暗变化（饱和度不变），因此不会被碰；
  3) 改动落在低频层，线稿与光影原样保留。
用法: istp_coat_even2.py <src> <dst> [strength]
"""
import os
import sys
import numpy as np
import cv2
from PIL import Image

OUT = "assets/char/_gen/char_ISTP_v2"

src = sys.argv[1]
dst = sys.argv[2]
K = float(sys.argv[3]) if len(sys.argv) > 3 else 0.85

sp = src if os.path.isabs(src) else os.path.join(OUT, src)
dp = dst if os.path.isabs(dst) else os.path.join(OUT, dst)

im = Image.open(sp).convert("RGB")
rgb = np.array(im)
H, W = rgb.shape[:2]
print("src =", sp, (W, H), "K =", K)

r = rgb[:, :, 0].astype(np.int16)
g = rgb[:, :, 1].astype(np.int16)
b = rgb[:, :, 2].astype(np.int16)
L = (0.299 * r + 0.587 * g + 0.114 * b).astype(np.float32)

hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
S = hsv[:, :, 1].astype(np.float32) / 255.0

# ---- 1) 大衣掩膜：绿色布料 + 只留最大连通域 ----
m = (g >= r) & (g >= b) & ((g - np.minimum(r, b)) > 8) & (L < 236) & (L > 20)
m = (m.astype(np.uint8)) * 255
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
n, lab_cc, stats, _ = cv2.connectedComponentsWithStats(m, 8)
if n > 1:
    areas = stats[1:, cv2.CC_STAT_AREA]
    keep = 1 + int(np.argmax(areas))
    m = np.where(lab_cc == keep, 255, 0).astype(np.uint8)
    print("连通域数 = %d，保留最大域面积 = %d px" % (n - 1, stats[keep, cv2.CC_STAT_AREA]))
mask = (m > 0)
print("大衣掩膜占比 = %.2f%%" % (100.0 * mask.mean()))

# ---- 2) 局部底色（只统计掩膜内像素）----
mf = mask.astype(np.float32)
SIG = 26.0
wsum = cv2.GaussianBlur(mf, (0, 0), SIG)
wsum = np.maximum(wsum, 1e-6)
Lbase = cv2.GaussianBlur(L * mf, (0, 0), SIG) / wsum
Sbase = cv2.GaussianBlur(S * mf, (0, 0), SIG) / wsum

lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
A, B = lab[:, :, 1], lab[:, :, 2]
Abase = cv2.GaussianBlur(A * mf, (0, 0), SIG) / wsum
Bbase = cv2.GaussianBlur(B * mf, (0, 0), SIG) / wsum

# ---- 3) 斑块判定：偏亮 + 偏灰（低饱和）----
brighter = (L - Lbase) > 6.0
greyer = (Sbase - S) > 0.045
sel = (mask & brighter & greyer).astype(np.uint8) * 255
print("亮灰斑像素占比(大衣内) = %.2f%%" % (100.0 * (sel > 0).sum() / max(mask.sum(), 1)))

# 去掉过小的碎点，只处理成规模的斑块
n2, lab2, st2, _ = cv2.connectedComponentsWithStats(sel, 8)
keep_mask = np.zeros_like(sel)
cnt = 0
for i in range(1, n2):
    if st2[i, cv2.CC_STAT_AREA] >= 40:
        keep_mask[lab2 == i] = 255
        cnt += 1
sel = keep_mask
print("保留斑块数 = %d，像素占比(大衣内) = %.2f%%" % (cnt, 100.0 * (sel > 0).sum() / max(mask.sum(), 1)))

self = cv2.GaussianBlur(sel.astype(np.float32) / 255.0, (0, 0), 3.0)
self = np.clip(self * 1.6, 0.0, 1.0)
self[~mask] = 0

# ---- 4) 修正（低频层）----
Lnew = L - K * self * (L - Lbase)
Anew = A - K * self * (A - Abase)
Bnew = B - K * self * (B - Bbase)

lab3 = lab.copy()
lab3[:, :, 0] = np.clip(Lnew, 0, 255)
lab3[:, :, 1] = np.clip(Anew, 0, 255)
lab3[:, :, 2] = np.clip(Bnew, 0, 255)
out = cv2.cvtColor(lab3.astype(np.uint8), cv2.COLOR_LAB2RGB)

soft = np.clip(cv2.GaussianBlur(self, (0, 0), 1.0)[:, :, None], 0, 1)
res = out.astype(np.float32) * soft + rgb.astype(np.float32) * (1 - soft)
res = np.clip(res, 0, 255).astype(np.uint8)

# ---- 5) 校验 ----
diffimg = np.abs(res.astype(np.int16) - rgb.astype(np.int16)).max(axis=2)
print("实际改动像素占比 = %.2f%%  最大通道差 = %d" % (100.0 * (diffimg > 0).mean(), diffimg.max()))
m2 = (res.astype(np.float32)[:, :, 1] >= res.astype(np.float32)[:, :, 0])  # 粗略：改动是否溢出大衣
outside = ((diffimg > 0) & (~mask)).sum()
print("掩膜外改动像素 = %d" % outside)

L2 = 0.299 * res[:, :, 0] + 0.587 * res[:, :, 1] + 0.114 * res[:, :, 2]
L2b = cv2.GaussianBlur(L2.astype(np.float32) * mf, (0, 0), SIG) / wsum
before = float(np.abs(L - Lbase)[mask].mean())
after = float(np.abs(L2.astype(np.float32) - L2b)[mask].mean())
print("大衣内平均 |亮度偏差| : %.3f -> %.3f (降 %.1f%%)" % (before, after, 100 * (1 - after / before)))

Image.fromarray(res).save(dp)
print("->", dp)
