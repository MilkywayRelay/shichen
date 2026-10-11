# -*- coding: utf-8 -*-
"""ENTJ 各版本锐度对比：脸部区域 Laplacian 方差 + 平均梯度。
注意：不同分辨率不能横比，故仅在 1536 原生版本之间比较；原图另列参考。"""
import os
import numpy as np
from PIL import Image

BASE = "C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen"
G = os.path.join(BASE, "assets/char/_gen/char_ENTJ_v2")

ITEMS = [
    ("原图 1024", os.path.join(BASE, "assets/char/entj.png")),
    ("v4a 1536", os.path.join(G, "Same_character__same_design__K_2026-10-11T11-46-14.png")),
    ("v4b 1536", os.path.join(G, "entj_v4_final.png")),
    ("v6  1536", os.path.join(G, "entj_v6_final.png")),
    ("v7  1536", os.path.join(G, "entj_v7_final.png")),
    ("v8  1536", os.path.join(G, "Keep_EVERYTHING_identical_to_t_2026-10-11T11-58-14.png")),
    ("v8d 回填", os.path.join(G, "entj_v8d_detail.png")),
]

# 脸部归一化区域（含眼睛、鼻、唇——细节最密集处）
FACE = (0.32, 0.05, 0.68, 0.20)


def metrics(im):
    W, H = im.size
    c = im.crop((int(W * FACE[0]), int(H * FACE[1]), int(W * FACE[2]), int(H * FACE[3])))
    # 统一缩放到 600 宽再做像素级度量，消除分辨率差异带来的尺度混入
    c = c.resize((600, int(600 * c.height / c.width)), Image.LANCZOS).convert("L")
    a = np.asarray(c, dtype=np.float32)
    lap = (-4 * a + np.roll(a, 1, 0) + np.roll(a, -1, 0)
           + np.roll(a, 1, 1) + np.roll(a, -1, 1))[1:-1, 1:-1]
    lv = lap.var()
    gx = np.abs(np.diff(a, axis=1)).mean()
    gy = np.abs(np.diff(a, axis=0)).mean()
    return lv, (gx + gy) / 2


print(f"{'版本':<10} {'Laplacian方差':>14} {'平均梯度':>10}")
for name, p in ITEMS:
    if not os.path.exists(p):
        print(f"{name:<10} {'(缺失)':>14}")
        continue
    im = Image.open(p).convert("RGB")
    lv, g = metrics(im)
    print(f"{name:<10} {lv:>14.1f} {g:>10.3f}")
