# -*- coding: utf-8 -*-
"""
INFJ 肤质修复 v2 —— 「同源干净皮肤」移植

结论先行（本轮的核心发现）：
  1. 低版本（v8/v13，1024）的脸确实明显干净 —— 用户判断正确。
     但 v13 放大 1.53 倍才够 v17 的尺寸，高频全糊，直接用会"脸软"。
     实测：v17b 与 v13 的差异 std 27.6，其中 96% 是细尺度——那部分是"分辨率差"，不是斑驳。
  2. 真正的解法是 v19：以 v17b 为底、prompt 强制"皮肤必须干净均匀"重出的一张
     原生 1536×2304 图。它与 v17b 的眼睛位置误差 <1px，构图完全对齐。
  3. 实测 v17b 脸上的"花" 96% 集中在细尺度（1~8px 的颗粒不均），
     所以低频压制/保边平滑都治不到根（这也是前几版"磨平"或"修不动"的原因）。
     正解：把皮肤整片换成 v19 的（同位置、原生清晰、细尺度均匀）。

本脚本：
  mask = 脸部多边形 ∩ (v17b 亮度 > 150)
         —— 亮度阈值天然把线稿（眉毛/眼线/唇线/发丝，L<150）排除在掩膜外，
            所以五官线条仍来自 v17b，设计不变；只有皮肤被换成干净的 v19。
  输出 = v17b·(1-mask) + v19·mask

用法: python tools/face_skin_graft.py
"""
import os
import sys
import numpy as np
import cv2
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skin_smooth import FACE_POLY, NECK_POLY, build_skin_mask, blotch_rms  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "assets/char/_gen/char_INFJ_v17/v17b_fixface.png")
SKIN = os.path.join(ROOT, "assets/char/_gen/char_INFJ_v19/v19a.png")   # 干净皮肤来源
OUTDIR = os.path.join(ROOT, "assets/char/_gen/char_INFJ_v19")

L_THR = 145        # 亮度阈值：>145 视为皮肤（线稿保留）
POLY_DILATE = 5    # 多边形外扩
FEATHER = 1.6      # 边缘羽化
EYE_BOX = (296, 392, 684, 880)   # 眼区 bbox (y0,y1,x0,x1)
EYE_DILATE = 7     # 虹膜保护膨胀（只保眼球本身，不连带眼周皮肤）


def _iris_mask(rgb, H, W):
    """按黄绿色虹膜检测出眼球，仅这些像素保持 v17b 原样（保住原眼型）"""
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(int)
    y0, y1, x0, x1 = EYE_BOX
    box = np.zeros((H, W), np.uint8)
    box[y0:y1, x0:x1] = 1
    m = ((hsv[..., 0] >= 20) & (hsv[..., 0] <= 45)
         & (hsv[..., 1] >= 50) & (hsv[..., 2] >= 45)).astype(np.uint8)
    m = (m & box).astype(np.uint8)
    return cv2.dilate(m, np.ones((EYE_DILATE, EYE_DILATE), np.uint8))


def main():
    dst = np.asarray(Image.open(DST).convert("RGB"))
    skin = np.asarray(Image.open(SKIN).convert("RGB"))
    H, W = dst.shape[:2]

    Ld = cv2.cvtColor(dst, cv2.COLOR_RGB2LAB).astype(np.float32)[..., 0]

    poly = np.zeros((H, W), np.uint8)
    cv2.fillPoly(poly, [FACE_POLY, NECK_POLY], 255)
    poly = cv2.dilate(poly, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                                      (POLY_DILATE * 2 + 1,) * 2))

    iris = _iris_mask(dst, H, W)
    m = ((poly > 0) & (Ld > L_THR) & (iris == 0)).astype(np.float32)
    m = np.clip(cv2.GaussianBlur(m, (0, 0), FEATHER), 0, 1)[..., None]

    out = (dst.astype(np.float32) * (1 - m) + skin.astype(np.float32) * m
           ).round().clip(0, 255).astype(np.uint8)

    ref = build_skin_mask(dst)
    print("斑驳度  v17b %.2f  ->  %.2f   (v19 基准 %.2f)"
          % (blotch_rms(dst, ref), blotch_rms(out, ref), blotch_rms(skin, ref)))
    print("掩膜覆盖 %d px   掩膜外最大改动 %d"
          % ((m[..., 0] > 0.05).sum(),
             np.abs(out.astype(int) - dst.astype(int))[m[..., 0] <= 0.001].max()))

    Image.fromarray(out).save(os.path.join(OUTDIR, "v19b_skin_graft.png"))
    print("saved", os.path.join(OUTDIR, "v19b_skin_graft.png"))
    return out


if __name__ == "__main__":
    main()
