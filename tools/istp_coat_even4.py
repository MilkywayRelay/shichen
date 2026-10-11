# -*- coding: utf-8 -*-
"""ISTP 大衣表面均匀化 v4 = even1 的验证效果 - 越界膨胀。
关键：掩膜不做膨胀、羽化半径收小，并把修正严格限制在原始大衣掩膜内，
彻底杜绝裤子被波及；改动同样只落在低频层。
用法: istp_coat_even4.py <src> <dst> [K] [thr]
"""
import os
import sys
import numpy as np
import cv2
from PIL import Image

OUT = "assets/char/_gen/char_ISTP_v2"
src, dst = sys.argv[1], sys.argv[2]
K = float(sys.argv[3]) if len(sys.argv) > 3 else 0.75
THR = float(sys.argv[4]) if len(sys.argv) > 4 else 7.0

sp = src if os.path.isabs(src) else os.path.join(OUT, src)
dp = dst if os.path.isabs(dst) else os.path.join(OUT, dst)
im = Image.open(sp).convert("RGB")
rgb = np.array(im)
H, W = rgb.shape[:2]
print("src =", sp, (W, H), "K=%.2f thr=%.1f" % (K, THR))

r = rgb[:, :, 0].astype(np.int16)
g = rgb[:, :, 1].astype(np.int16)
b = rgb[:, :, 2].astype(np.int16)
L = (0.299 * r + 0.587 * g + 0.114 * b).astype(np.float32)
S = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)[:, :, 1].astype(np.float32) / 255.0

# 应用域：绿色布料，仅做 3x3 闭运算填小洞，绝不膨胀
green = (g >= r) & (g >= b) & (L < 236) & (L > 15)
gm = (green.astype(np.uint8)) * 255
gm = cv2.morphologyEx(gm, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
keep0 = gm > 0
print("应用域(大衣) 占比 = %.2f%%" % (100.0 * keep0.mean()))

# 底色：计算域 = 非背景（稳健，不受掩膜稀疏影响）
allf = ((L < 238) & (L > 10)).astype(np.float32)
SIG = 26.0
ws = np.maximum(cv2.GaussianBlur(allf, (0, 0), SIG), 1e-6)
Lbase = cv2.GaussianBlur(L * allf, (0, 0), SIG) / ws
Sbase = cv2.GaussianBlur(S * allf, (0, 0), SIG) / ws
lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
A, B = lab[:, :, 1], lab[:, :, 2]
Abase = cv2.GaussianBlur(A * allf, (0, 0), SIG) / ws
Bbase = cv2.GaussianBlur(B * allf, (0, 0), SIG) / ws

dL = L - Lbase
# 斑块 = 大衣内亮度偏离底色，且同时偏灰（饱和度低于底色）
# 单向：只压「比底色亮」的浅斑；暗部(线稿/阴影)一律不动
sel = keep0 & (dL > THR) & ((Sbase - S) > 0.02)
sel = (sel.astype(np.uint8)) * 255

n, cc, st, _ = cv2.connectedComponentsWithStats(sel, 8)
keep = np.zeros_like(sel)
cnt = 0
for i in range(1, n):
    if st[i, cv2.CC_STAT_AREA] >= 60:
        keep[cc == i] = 255
        cnt += 1
sel = keep
print("命中斑块数 = %d，像素占比(大衣内) = %.2f%%" % (cnt, 100.0 * (sel > 0).sum() / max(keep0.sum(), 1)))

self_m = cv2.GaussianBlur(sel.astype(np.float32) / 255.0, (0, 0), 3.0)
self_m = np.clip(self_m * 1.7, 0.0, 1.0)
self_m[~keep0] = 0.0          # 严格锁在大衣内

Lnew = L - K * self_m * dL
Anew = A - K * self_m * (A - Abase)
Bnew = B - K * self_m * (B - Bbase)
lab3 = lab.copy()
lab3[:, :, 0] = np.clip(Lnew, 0, 255)
lab3[:, :, 1] = np.clip(Anew, 0, 255)
lab3[:, :, 2] = np.clip(Bnew, 0, 255)
out = cv2.cvtColor(lab3.astype(np.uint8), cv2.COLOR_LAB2RGB)

# 合成：羽化后再次强制锁在大衣内
soft = cv2.GaussianBlur(self_m, (0, 0), 1.2)
soft[~keep0] = 0.0
soft = np.clip(soft, 0, 1)[:, :, None]
res = out.astype(np.float32) * soft + rgb.astype(np.float32) * (1 - soft)
res = np.clip(res, 0, 255).astype(np.uint8)

d = np.abs(res.astype(np.int16) - rgb.astype(np.int16)).max(axis=2)
outside = int(((d > 0) & (~keep0)).sum())
print("实际改动像素占比 = %.2f%%  掩膜外改动像素 = %d  最大通道差 = %d" % (100.0 * (d > 0).mean(), outside, d.max()))

L2 = 0.299 * res[:, :, 0] + 0.587 * res[:, :, 1] + 0.114 * res[:, :, 2]
L2b = cv2.GaussianBlur(L2.astype(np.float32) * allf, (0, 0), SIG) / ws
bf = float(np.abs(dL[keep0]).mean())
af = float(np.abs(L2.astype(np.float32) - L2b)[keep0].mean())
print("大衣内平均 |亮度偏差| : %.3f -> %.3f (降 %.1f%%)" % (bf, af, 100 * (1 - af / bf)))

Image.fromarray(res).save(dp)
vis = rgb.copy(); vis[sel > 0] = [255, 0, 0]
Image.fromarray(vis).resize((W // 2, H // 2)).save(os.path.join(OUT, "sel4.png"))
print("->", dp)
