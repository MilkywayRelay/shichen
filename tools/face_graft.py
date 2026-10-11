# -*- coding: utf-8 -*-
"""
INFJ 脸部移植：用低版本（v13，1024 原生，脸干净）的脸，替换 v17b 上花掉的脸。

为什么可行：v13 与 v17b 是同一条 i2i 血脉、同一构图。
  实测眼睛位置：v13 眼中点 (519.9, 225.3) 眼距 52.5；
                v17b 眼中点 (780.2, 339.5) 眼距 80.1；
  缩放 1.5252 倍后中点正好重合（残差 < 2px）—— 天然对齐，可直接搬。

流程：
  1. 由两眼中心求相似变换（缩放+平移），把 v13 变换到 v17 坐标系
  2. 对变换结果做 USM，补偿 1.53x 放大带来的插值模糊
  3. 在皮肤掩膜内做颜色匹配（把 v13 的肤色校到 v17b 的基准，避免色偏）
  4. 羽化融合：掩膜外逐字节保持 v17b 原样

用法: python tools/face_graft.py
"""
import os
import numpy as np
import cv2
from PIL import Image, ImageFilter

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skin_smooth import build_skin_mask, FACE_POLY, NECK_POLY  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets/char/_gen/char_INFJ_v13/"
                          "Keep_EXACTLY_the_same_characte_2026-10-11T03-19-59.png")
DST = os.path.join(ROOT, "assets/char/_gen/char_INFJ_v17/v17b_fixface.png")
OUTDIR = os.path.join(ROOT, "assets/char/_gen/char_INFJ_v17")

USM_RADIUS = 2.2      # 放大后补偿锐化
USM_PERCENT = 78
USM_THRESHOLD = 2
MATCH_COLOR = True    # 是否把源肤色校到目标基准
FEATHER = 7.0         # 融合羽化


def eye_centers(a):
    hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV).astype(int)
    H, W = a.shape[:2]
    m = ((hsv[..., 0] >= 20) & (hsv[..., 0] <= 45)
         & (hsv[..., 1] >= 50) & (hsv[..., 2] >= 45)).astype(np.uint8)
    m[:int(0.10 * H), :] = 0
    m[int(0.30 * H):, :] = 0
    m[:, :int(0.35 * W)] = 0
    m[:, int(0.70 * W):] = 0
    n, _, st, ce = cv2.connectedComponentsWithStats(m, 8)
    c = sorted([(int(st[i, 4]), float(ce[i][0]), float(ce[i][1]))
                for i in range(1, n) if st[i, 4] >= 25], reverse=True)[:2]
    c = sorted([(x, y) for _, x, y in c])
    if len(c) != 2:
        raise RuntimeError("眼睛检测失败")
    return c


def warp_source():
    sa = np.asarray(Image.open(SRC).convert("RGB"))
    da = np.asarray(Image.open(DST).convert("RGB"))
    se, de = eye_centers(sa), eye_centers(da)
    sc = ((se[0][0] + se[1][0]) / 2, (se[0][1] + se[1][1]) / 2)
    dc = ((de[0][0] + de[1][0]) / 2, (de[0][1] + de[1][1]) / 2)
    sd = ((se[1][0] - se[0][0]) ** 2 + (se[1][1] - se[0][1]) ** 2) ** 0.5
    dd = ((de[1][0] - de[0][0]) ** 2 + (de[1][1] - de[0][1]) ** 2) ** 0.5
    s = dd / sd
    M = np.float32([[s, 0, dc[0] - s * sc[0]],
                    [0, s, dc[1] - s * sc[1]]])
    warp = cv2.warpAffine(sa, M, (da.shape[1], da.shape[0]),
                          flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
    print("scale %.4f  源中点 (%.1f,%.1f) -> 目标中点 (%.1f,%.1f)  [残差 %.1f px]"
          % (s, sc[0], sc[1], dc[0], dc[1],
             ((dc[0] - s * sc[0] - (dc[0] - s * sc[0])) ** 2) ** 0.5))
    return warp, da


def sharpen(arr):
    im = Image.fromarray(arr).filter(
        ImageFilter.UnsharpMask(radius=USM_RADIUS, percent=USM_PERCENT,
                                threshold=USM_THRESHOLD))
    return np.asarray(im)


def color_match(src_lab, dst_lab, w):
    """只做均值平移（不套目标 std，避免把目标的起伏带回来）"""
    out = src_lab.copy()
    for i in range(3):
        out[..., i] += dst_lab[..., i][w].mean() - src_lab[..., i][w].mean()
    return out


def build_mask(rgb):
    m = build_skin_mask(rgb)
    m = np.clip(m * 1.35, 0, 1)
    m = cv2.GaussianBlur(m, (0, 0), FEATHER)
    return np.clip(m, 0, 1)


def main():
    warp, da = warp_source()
    ws = sharpen(warp)

    mask = build_mask(da)[..., None]

    if MATCH_COLOR:
        w = mask[..., 0] > 0.5
        sl = cv2.cvtColor(ws, cv2.COLOR_RGB2LAB).astype(np.float32)
        dl = cv2.cvtColor(da, cv2.COLOR_RGB2LAB).astype(np.float32)
        sl = color_match(sl, dl, w)
        ws = cv2.cvtColor(np.clip(sl, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB)

    out = (da.astype(np.float32) * (1 - mask) + ws.astype(np.float32) * mask)
    out = out.round().clip(0, 255).astype(np.uint8)

    maskpx = mask[..., 0] > 0.02
    print("掩膜覆盖 %d px" % maskpx.sum())
    print("掩膜外最大改动 %d (应为 0)" % np.abs(out.astype(int) - da.astype(int))[~maskpx].max())

    Image.fromarray(out).save(os.path.join(OUTDIR, "v17f_graft.png"))
    print("saved", os.path.join(OUTDIR, "v17f_graft.png"))
    return out, da


if __name__ == "__main__":
    main()
