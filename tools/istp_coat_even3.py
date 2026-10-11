# -*- coding: utf-8 -*-
"""ISTP 大衣浅色灰斑清除 v3。
思路：斑块 = 「比周边亮」且「比周边灰」的孤立中尺度区域，用 DoG（尺度差）直接定位，
不再依赖掩膜形状，因此不会误伤裤子；底色用归一化模糊，边界不失真。
用法: istp_coat_even3.py <src> <dst> [K] [dogL] [dogS]
"""
import os
import sys
import numpy as np
import cv2
from PIL import Image

OUT = "assets/char/_gen/char_ISTP_v2"

src, dst = sys.argv[1], sys.argv[2]
K = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8
TL = float(sys.argv[4]) if len(sys.argv) > 4 else 6.0
TS = float(sys.argv[5]) if len(sys.argv) > 5 else 0.030

sp = src if os.path.isabs(src) else os.path.join(OUT, src)
dp = dst if os.path.isabs(dst) else os.path.join(OUT, dst)
im = Image.open(sp).convert("RGB")
rgb = np.array(im)
H, W = rgb.shape[:2]
print("src =", sp, (W, H), "K=%.2f TL=%.1f TS=%.3f" % (K, TL, TS))

r = rgb[:, :, 0].astype(np.int16)
g = rgb[:, :, 1].astype(np.int16)
b = rgb[:, :, 2].astype(np.int16)
L = (0.299 * r + 0.587 * g + 0.114 * b).astype(np.float32)
S = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)[:, :, 1].astype(np.float32) / 255.0

# 大衣（绿色布料）判定：g 不低于 r/b，且不是纯白背景
green = (g >= r) & (g >= b) & (L < 236) & (L > 15)

# 尺度差：中尺度(8) 减 大尺度(30)
L1 = cv2.GaussianBlur(L, (0, 0), 8.0)
L2 = cv2.GaussianBlur(L, (0, 0), 30.0)
S1 = cv2.GaussianBlur(S, (0, 0), 8.0)
S2 = cv2.GaussianBlur(S, (0, 0), 30.0)
dogL = L1 - L2
dogS = S1 - S2

sel = green & (dogL > TL) & (dogS < -TS)
sel = (sel.astype(np.uint8)) * 255

n, cc, st, _ = cv2.connectedComponentsWithStats(sel, 8)
keep = np.zeros_like(sel)
cnt = 0
for i in range(1, n):
    if st[i, cv2.CC_STAT_AREA] >= 30:
        keep[cc == i] = 255
        cnt += 1
sel = keep
print("命中斑块数 = %d，像素占比 = %.2f%%（全图）" % (cnt, 100.0 * (sel > 0).mean()))

# 底色（归一化模糊，计算域 = 非背景）
allf = ((L < 238) & (L > 10)).astype(np.float32)
SIG = 26.0
ws = np.maximum(cv2.GaussianBlur(allf, (0, 0), SIG), 1e-6)
Lbase = cv2.GaussianBlur(L * allf, (0, 0), SIG) / ws
Sbase = cv2.GaussianBlur(S * allf, (0, 0), SIG) / ws
lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
A, B = lab[:, :, 1], lab[:, :, 2]
Abase = cv2.GaussianBlur(A * allf, (0, 0), SIG) / ws
Bbase = cv2.GaussianBlur(B * allf, (0, 0), SIG) / ws

self_m = cv2.GaussianBlur(sel.astype(np.float32) / 255.0, (0, 0), 3.0)
self_m = np.clip(self_m * 1.7, 0.0, 1.0)

Lnew = L - K * self_m * (L - Lbase)
Anew = A - K * self_m * (A - Abase)
Bnew = B - K * self_m * (B - Bbase)

lab3 = lab.copy()
lab3[:, :, 0] = np.clip(Lnew, 0, 255)
lab3[:, :, 1] = np.clip(Anew, 0, 255)
lab3[:, :, 2] = np.clip(Bnew, 0, 255)
out = cv2.cvtColor(lab3.astype(np.uint8), cv2.COLOR_LAB2RGB)

soft = np.clip(cv2.GaussianBlur(self_m, (0, 0), 1.0)[:, :, None], 0, 1)
res = out.astype(np.float32) * soft + rgb.astype(np.float32) * (1 - soft)
res = np.clip(res, 0, 255).astype(np.uint8)

d = np.abs(res.astype(np.int16) - rgb.astype(np.int16)).max(axis=2)
print("实际改动像素占比 = %.2f%%  最大通道差 = %d" % (100.0 * (d > 0).mean(), d.max()))
# 误选区检查：裤子（深灰、低饱和、g<b）是否被改
trousers = (b > g) & (L > 40) & (L < 150) & (np.abs(r - g) < 12)
hit_tr = int(((d > 0) & trousers).sum())
print("裤子区域被改像素 = %d (%.3f%%)" % (hit_tr, 100.0 * hit_tr / max(trousers.sum(), 1)))

Image.fromarray(res).save(dp)
# 命中可视化
vis = rgb.copy()
vis[sel > 0] = [255, 0, 0]
Image.fromarray(vis).resize((W // 2, H // 2)).save(os.path.join(OUT, "chk_sel3_%s.png" % dst.split(".")[0][-1]))
print("->", dp)
