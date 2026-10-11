# -*- coding: utf-8 -*-
"""脸部白斑（类白癜风硬边亮块）修复：连通域检测 + 归一化高斯填补 + 羽化"""
import os
import sys
import numpy as np
import cv2
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 脸部多边形（v17a 原生 1536x2304 坐标），覆盖额/颊/鼻/颌/颈
FACE_POLY = np.array([
    [700, 292], [760, 268], [836, 266], [892, 288],
    [916, 372], [908, 452], [872, 512], [846, 566],
    [790, 574], [740, 540], [706, 470], [694, 380],
], np.int32)

WHITE = 245          # 判定为"亮块"的阈值
SIGMA = 9.0          # 填补高斯半径
DILATE = 2


def build_mask(L, poly):
    """返回：(需要修复的掩膜, 诊断信息)"""
    h, w = L.shape
    white = (L >= WHITE).astype(np.uint8)

    # 1) 与画面边框连通的白色 = 背景，全部排除
    n, lab = cv2.connectedComponents(white, 8)
    border_labels = set(lab[0, :].tolist()) | set(lab[-1, :].tolist()) | \
                    set(lab[:, 0].tolist()) | set(lab[:, -1].tolist())
    border_labels.discard(0)
    bg = np.isin(lab, list(border_labels)).astype(np.uint8)

    inside = np.zeros((h, w), np.uint8)
    cv2.fillPoly(inside, [poly], 1)

    cand = (white & (1 - bg) & inside).astype(np.uint8)
    if DILATE:
        cand = cv2.dilate(cand, np.ones((DILATE * 2 + 1,) * 2, np.uint8), iterations=1)
    return cand, dict(white=int(white.sum()), bg=int(bg.sum()), cand=int(cand.sum()))


def fill(img, mask, sigma=SIGMA, texture_keep=True):
    """归一化高斯卷积填补 + 只回写低频差值（保住原有纸纹/笔触）"""
    m = mask.astype(np.float32)
    w = 1.0 - m
    out = img.astype(np.float32).copy()
    k = int(sigma * 4) | 1
    for ch in range(3):
        num = cv2.GaussianBlur(out[..., ch] * w, (k, k), sigma)
        den = cv2.GaussianBlur(w, (k, k), sigma)
        out[..., ch] = num / np.maximum(den, 1e-6)

    feather = cv2.GaussianBlur(m, (0, 0), 2.0)
    feather = np.clip(feather * 1.5, 0, 1)

    if texture_keep:
        diff = out - img.astype(np.float32)
        for ch in range(3):
            diff[..., ch] = cv2.GaussianBlur(diff[..., ch], (0, 0), 3.0)
        res = img.astype(np.float32) + diff * feather[..., None]
    else:
        res = img.astype(np.float32) * (1 - feather[..., None]) + out * feather[..., None]
    return np.clip(res, 0, 255).astype(np.uint8)


def main(src, dst, debug=None):
    im = Image.open(src).convert("RGB")
    arr = np.asarray(im)
    L = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    mask, info = build_mask(L, FACE_POLY)
    print("掩膜:", info)
    fixed = fill(arr, mask)
    Image.fromarray(fixed).save(dst)
    print("->", dst)
    if debug:
        ov = arr.copy()
        ov[mask > 0] = [255, 60, 60]
        Image.fromarray(ov).save(debug)
        print("->", debug)


if __name__ == "__main__":
    g17 = os.path.join(ROOT, "assets", "char", "_gen", "char_INFJ_v17")
    main(os.path.join(g17, "v17a.png"),
         os.path.join(g17, "v17b_fixface.png"),
         os.path.join(g17, "_mask_debug.png"))
