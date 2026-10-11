# -*- coding: utf-8 -*-
"""
INFJ 立绘「肤色均匀化」最终版 —— 频域分离(frequency separation)

诊断：脸上「青一块紫一块」的成分 = 皮肤上中尺度(约 10~110px)的明暗/色度起伏，
线稿(高频)与下颌等大光影(>110px)本身是好的。

做法（只在皮肤掩膜内生效，掩膜外一个像素都不动）：
 1) 掩膜 = 手绘「脸+颈+胸口」多边形 ∩ 暖色判定(LAB b 偏高) ，再剔除小连通域(虹膜)，
    不做孔洞填充，避免把压在脸上的银白发束一起抹平。
 2) 大尺度基线用**归一化卷积**（只统计皮肤像素），避免把背景灰白混进来导致肤色发灰。
 3) 亮度 L：软膝压制。偏差 |d| < knee0 的起伏视为斑驳 → 压掉；
    |d| > knee1 的视为真实光影 → 原样保留；中间平滑过渡。
 4) 色度 a/b：只轻压(κ)，保留整体冷暖倾向。

用法: python tools/skin_even.py
"""
import os
import numpy as np
import cv2
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets/char/_gen/char_INFJ_v17/v17b_fixface.png")
OUTDIR = os.path.join(ROOT, "assets/char/_gen/char_INFJ_v17")

# 多边形只做「大致范围」约束，真正的边界交给暖色判定，避免多边形切进脸颊造成台阶
FACE_POLY = np.array([
    (692, 286), (790, 266), (858, 284), (886, 338), (882, 398),
    (856, 436), (818, 462), (774, 470), (728, 450), (700, 404), (686, 340),
], np.int32)

NECK_POLY = np.array([
    (735, 444), (822, 450), (848, 500), (854, 556), (844, 596),
    (766, 600), (724, 556), (714, 500),
], np.int32)

WARM_B = 3.0           # LAB b 高于 128+该值 视为皮肤（用于把银白发丝排掉）
FEATHER = 6.0          # 掩膜羽化半径

SIGMA_BASE = 110.0     # 大尺度基线半径（归一化卷积）
SIGMA_DETAIL = 3.0     # 小于它的算细节，全保留

L_KNEE = (7.0, 20.0)   # 亮度软膝：<7 视为斑驳压掉，>20 视为光影保留
A_SOFT = (0.40, 0.5, 2.5)
B_SOFT = (0.40, 0.6, 3.0)
BLEND = 1.00           # 总体应用强度
MIN_BLOB = 900         # 小于该面积的连通域（虹膜等）剔除


def build_skin_mask(rgb):
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    L, B = lab[..., 0], lab[..., 2]

    region = np.zeros(rgb.shape[:2], np.uint8)
    cv2.fillPoly(region, [FACE_POLY, NECK_POLY], 255)

    warm = (((B - 128.0) > WARM_B) & (L > 160) & (L < 252)).astype(np.uint8) * 255
    m = cv2.bitwise_and(warm, region)

    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k, iterations=1)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k, iterations=1)

    n, lab_img, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    for i in range(1, n):
        if stats[i, 4] >= MIN_BLOB:
            keep[lab_img == i] = 255
    m = keep

    m = cv2.erode(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)), iterations=1)
    return np.clip(cv2.GaussianBlur(m.astype(np.float32) / 255.0, (0, 0), FEATHER), 0, 1)


def norm_blur(ch, mask, sigma):
    """只统计皮肤像素的归一化高斯：避免背景/头发把肤色拉灰"""
    m = mask.astype(np.float32)
    num = cv2.GaussianBlur(ch * m, (0, 0), sigma)
    den = cv2.GaussianBlur(m, (0, 0), sigma)
    return np.where(den > 0.02, num / np.maximum(den, 1e-6), cv2.GaussianBlur(ch, (0, 0), sigma))


def soft_knee(ch, base, kappa, k0, k1):
    d = ch - base
    t = np.clip((np.abs(d) - k0) / max(k1 - k0, 1e-6), 0, 1)
    t = t * t * (3 - 2 * t)
    return ch - d * kappa * (1 - t)


def even_skin(rgb, mask):
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    L, A, B = lab[..., 0], lab[..., 1], lab[..., 2]

    baseL = norm_blur(L, mask, SIGMA_BASE)
    baseA = norm_blur(A, mask, SIGMA_BASE)
    baseB = norm_blur(B, mask, SIGMA_BASE)

    # 亮度：软膝（kappa=1）
    Lc = soft_knee(L, baseL, 1.0, *L_KNEE)
    Ac = soft_knee(A, baseA, *A_SOFT)
    Bc = soft_knee(B, baseB, *B_SOFT)

    w = mask * BLEND
    out = np.stack([L * (1 - w) + Lc * w,
                    A * (1 - w) + Ac * w,
                    B * (1 - w) + Bc * w], -1)
    fixed = cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB)
    # 掩膜外用原始 RGB 合成，保证逐字节不变
    return (rgb.astype(np.float32) * (1 - w[..., None]) + fixed.astype(np.float32) * w[..., None]
            ).round().clip(0, 255).astype(np.uint8)


def blotch_metric(rgb, mask):
    """皮肤区内「斑驳度」：中尺度(σ3~σ60)亮度起伏的均方根，越小越均匀"""
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    L = lab[..., 0]
    d = cv2.GaussianBlur(L, (0, 0), SIGMA_DETAIL) - cv2.GaussianBlur(L, (0, 0), 60)
    w = mask > 0.9
    return float(np.sqrt((d[w] ** 2).mean()))


def sharpness(rgb):
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    return round(float(abs(np.diff(g, axis=0)).mean() + abs(np.diff(g, axis=1)).mean()), 2)


def main():
    rgb = np.asarray(Image.open(SRC).convert("RGB"))
    mask = build_skin_mask(rgb)
    print("皮肤掩膜 %d px" % (mask > 0.8).sum())
    print("处理前  斑驳度 %.2f   锐度 %.2f" % (blotch_metric(rgb, mask), sharpness(rgb)))

    out = even_skin(rgb, mask)
    print("处理后  斑驳度 %.2f   锐度 %.2f" % (blotch_metric(out, mask), sharpness(out)))

    outside = mask <= 0.0
    diff = np.abs(out.astype(int) - rgb.astype(int))
    print("掩膜外最大改动 %d (应为 0)" % diff[outside].max())

    Image.fromarray(out).save(os.path.join(OUTDIR, "v17d_skin_fixed.png"))

    dbg = rgb.copy()
    sel = mask > 0.5
    dbg[sel] = (dbg[sel] * 0.4 + np.array([255, 80, 80]) * 0.6).astype(np.uint8)
    Image.fromarray(dbg).crop((660, 250, 1000, 640)).save(os.path.join(OUTDIR, "_mask_skin_debug.png"))
    print("saved ->", OUTDIR)


if __name__ == "__main__":
    main()
