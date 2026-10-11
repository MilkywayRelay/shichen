# -*- coding: utf-8 -*-
"""
INFJ 立绘「肤质修复」—— 两层保边平滑（tone smoothing + detail preserving）

背景：这张脸上的「青一块紫一块 / 像白癜风」是**生成缺陷**——
站内在用的 Mana / ISFJ 立绘皮肤都是干净平滑的，说明这是画风里不该有的杂斑。

为什么不用纯频域压制：斑块幅度 10~27 灰阶，和鼻子/下颌的真实光影幅度重叠，
一刀切要么斑块留着，要么脸被抹成平面（实测两种都失败）。

最终做法（只在皮肤掩膜内生效）：
   把 L 拆成
     detail = L - blur(L, 2.0)      -> 线稿、睫毛、唇线、发丝，**原样保留**
     tone   = blur(L, 2.0)          -> 肤色明暗 + 斑块
   只对 tone 做**保边滤波(bilateral)**：同色邻近像素互相平均 →
   幅度小的斑驳被抹平，而单调渐变(鼻子/下颌阴影)因为是「局部相似」会被完整保留。
   最后 L' = bilateral(tone) + detail，线稿一根不少。
   色度 a/b 同样处理，并整体回补一点暖调，抵消平滑带来的轻微去饱和。

用法: python tools/skin_smooth.py
"""
import os
import numpy as np
import cv2
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets/char/_gen/char_INFJ_v17/v17b_fixface.png")
OUTDIR = os.path.join(ROOT, "assets/char/_gen/char_INFJ_v17")

# 多边形只约束大致范围，真实边界交给暖色判定（否则多边形会切进脸颊留下台阶）
FACE_POLY = np.array([
    (692, 286), (790, 266), (858, 284), (886, 338), (882, 398),
    (856, 436), (818, 462), (774, 470), (728, 450), (700, 404), (686, 340),
], np.int32)

NECK_POLY = np.array([
    (735, 444), (822, 450), (848, 500), (854, 556), (844, 596),
    (766, 600), (724, 556), (714, 500),
], np.int32)

WARM_B = 3.0          # LAB b 高于 128+该值 视为皮肤（排掉银白头发）
FEATHER = 6.0         # 掩膜羽化
MIN_BLOB = 900        # 小连通域（虹膜等）剔除

SIG_SPLIT = 2.0       # 细节层/色调层的分界
BF_D = 45             # 亮度层 bilateral 直径
BF_SC_L = 38          # 亮度层 bilateral 阈值
BF_SS = 36            # bilateral 空间半径
BF_PASSES = 3         # 亮度层重复次数

CHROMA_D = 27         # 色度层 bilateral 直径
CHROMA_SC = 5         # 色度层 bilateral 阈值
CHROMA_PASSES = 2     # 色度层重复次数

WARM_RESTORE = (0.60, 0.90)   # 平滑后回补的 a / b 温暖度（抵消平滑造成的去饱和）


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


def two_layer(ch, sc, passes=1, dia=BF_D, restore=0.0):
    tone = cv2.GaussianBlur(ch, (0, 0), SIG_SPLIT)
    detail = ch - tone
    t = tone.astype(np.uint8)
    for _ in range(passes):
        t = cv2.bilateralFilter(t, dia, sc, BF_SS)
    return t.astype(np.float32) + detail + restore


def fix_skin(rgb, mask):
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    L, A, B = lab[..., 0], lab[..., 1], lab[..., 2]

    Lc = two_layer(L, BF_SC_L, BF_PASSES)
    Ac = two_layer(A, CHROMA_SC, CHROMA_PASSES, CHROMA_D, WARM_RESTORE[0])
    Bc = two_layer(B, CHROMA_SC, CHROMA_PASSES, CHROMA_D, WARM_RESTORE[1])

    out = np.stack([L * (1 - mask) + Lc * mask,
                    A * (1 - mask) + Ac * mask,
                    B * (1 - mask) + Bc * mask], -1)
    fixed = cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB)
    # 掩膜外严格用原始 RGB 合成 -> 逐字节不变
    w = mask[..., None]
    return (rgb.astype(np.float32) * (1 - w) + fixed.astype(np.float32) * w
            ).round().clip(0, 255).astype(np.uint8)


def blotch_rms(rgb, mask):
    """皮肤区内中尺度(2~60px)亮度起伏 —— 斑驳度的量化指标"""
    L = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)[..., 0]
    d = cv2.GaussianBlur(L, (0, 0), 2) - cv2.GaussianBlur(L, (0, 0), 60)
    w = mask > 0.95
    return float(np.sqrt((d[w] ** 2).mean()))


def sharpness(rgb):
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    return round(float(abs(np.diff(g, axis=0)).mean() + abs(np.diff(g, axis=1)).mean()), 2)


def main():
    rgb = np.asarray(Image.open(SRC).convert("RGB"))
    mask = build_skin_mask(rgb)
    print("皮肤掩膜 %d px" % (mask > 0.8).sum())
    print("处理前  斑驳度 %.2f   锐度 %.2f" % (blotch_rms(rgb, mask), sharpness(rgb)))

    out = fix_skin(rgb, mask)
    print("处理后  斑驳度 %.2f   锐度 %.2f" % (blotch_rms(out, mask), sharpness(out)))

    a = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    b = cv2.cvtColor(out, cv2.COLOR_RGB2LAB).astype(np.float32)
    w = mask > 0.9
    print("肤色冷暖  b-128  %.2f -> %.2f   （回补后应与原图接近）"
          % (a[..., 2][w].mean() - 128, b[..., 2][w].mean() - 128))
    print("掩膜外最大改动 %d (应为 0)"
          % np.abs(out.astype(int) - rgb.astype(int))[mask <= 0.0].max())

    Image.fromarray(out).save(os.path.join(OUTDIR, "v17e_skin_smooth.png"))

    dbg = rgb.copy()
    sel = mask > 0.5
    dbg[sel] = (dbg[sel] * 0.4 + np.array([255, 80, 80]) * 0.6).astype(np.uint8)
    Image.fromarray(dbg).crop((660, 250, 1000, 640)).save(os.path.join(OUTDIR, "_mask_skin_debug.png"))
    print("saved ->", OUTDIR)


if __name__ == "__main__":
    main()
