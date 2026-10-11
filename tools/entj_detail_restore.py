# -*- coding: utf-8 -*-
"""细节回填：以 v8 为底，把 v4b 的细尺度线条（1~4px）叠回去，
领口改动区不回填，以保住新的褶领花设计。同时输出对齐检查图。"""
import os
import cv2
import numpy as np

BASE = "C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen"
G = os.path.join(BASE, "assets/char/_gen/char_ENTJ_v2")

V4B = os.path.join(G, "entj_v4_final.png")
V8 = os.path.join(G, "Keep_EVERYTHING_identical_to_t_2026-10-11T11-58-14.png")

WEIGHT = 0.88          # 细节回填强度
SIG_SPLIT = 1.6        # 细节层截止尺度
# 领口改动保护区（归一化），羽化过渡
KEEP = (0.28, 0.07, 0.82, 0.36)
FEATHER = 31


def main():
    base = cv2.imread(V8, cv2.IMREAD_COLOR)
    ref = cv2.imread(V4B, cv2.IMREAD_COLOR)
    print("v8:", base.shape, "v4b:", ref.shape)
    if base.shape != ref.shape:
        ref = cv2.resize(ref, (base.shape[1], base.shape[0]), interpolation=cv2.INTER_LANCZOS4)

    H, W = base.shape[:2]

    # ---- 对齐检查：红青叠加 ----
    g8 = cv2.cvtColor(base, cv2.COLOR_BGR2GRAY)
    g4 = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
    overlay = np.zeros((H, W, 3), np.uint8)
    overlay[:, :, 2] = g8          # 红 = v8
    overlay[:, :, 1] = g4          # 绿 = v4b
    overlay[:, :, 0] = g4          # 蓝 = v4b  → v4b 显示为青，v8 显示为红
    cv2.imwrite(os.path.join(G, "align_v8_v4b.png"), overlay)
    diff = cv2.absdiff(g8, g4)
    print("灰度绝对差: mean=%.2f  p95=%.1f" % (diff.mean(), np.percentile(diff, 95)))

    # ---- 细节回填 ----
    f = base.astype(np.float32)
    r = ref.astype(np.float32)
    low = cv2.GaussianBlur(r, (0, 0), SIG_SPLIT)
    detail = r - low                                  # v4b 的细尺度细节

    keep = np.zeros((H, W), np.float32)               # 1 = 不回填（保护领口）
    x0, y0, x1, y1 = int(KEEP[0] * W), int(KEEP[1] * H), int(KEEP[2] * W), int(KEEP[3] * H)
    keep[y0:y1, x0:x1] = 1.0
    keep = cv2.GaussianBlur(keep, (FEATHER, FEATHER), 0)
    keep = np.clip(keep, 0, 1)[..., None]

    out = f + detail * WEIGHT * (1 - keep)
    out = np.clip(out, 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(G, "entj_v8d_detail.png"), out)
    print("ok -> entj_v8d_detail.png")
    cv2.imwrite(os.path.join(G, "align_v8_v4b_head.png"),
                overlay[int(0.02 * H):int(0.32 * H), int(0.24 * W):int(0.84 * W)])


if __name__ == "__main__":
    main()
