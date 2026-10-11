# -*- coding: utf-8 -*-
"""在 E 手部区域内做颜色聚类，找出"皮肤"簇，输出干净的手部掩膜（供人工核对）。"""
import os
import numpy as np
from PIL import Image

BASE = r"C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen"
E = os.path.join(BASE, "assets/char/mana_alt/E_handfix_raw.png")
N = os.path.join(BASE, "assets/char/mana_alt/N_nofeet.png")
BOX = (250, 500, 470, 760)


def kmeans(X, k=6, iters=30, seed=0):
    rng = np.random.default_rng(seed)
    C = X[rng.choice(len(X), k, replace=False)]
    for _ in range(iters):
        d = ((X[:, None, :] - C[None, :, :]) ** 2).sum(-1)
        lab = d.argmin(1)
        for j in range(k):
            m = lab == j
            if m.any():
                C[j] = X[m].mean(0)
    return lab, C


def analyze(path, tag):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    x0, y0, x1, y1 = BOX
    sub = a[y0:y1, x0:x1].reshape(-1, 3)
    lab, C = kmeans(sub, k=7)
    # 按亮度/暖度给簇排序输出
    order = np.argsort(-(C[:, 0] - C[:, 2]))
    print("==", tag)
    for j in order:
        m = lab == j
        print("  cluster %d  n=%6d  meanRGB=%s  R-B=%.1f" % (
            j, int(m.sum()), np.round(C[j]).astype(int), C[j][0] - C[j][2]))
    return a, lab.reshape(y1 - y0, x1 - x0), C


def render(a, lab, C, path_out, choose):
    x0, y0, x1, y1 = BOX
    vis = a.astype(np.uint8).copy()
    m = np.isin(lab, choose)
    vis[y0:y1, x0:x1][m] = [255, 0, 255]
    Image.fromarray(vis[y0 - 10:y1 + 10, x0 - 10:x1 + 10]).save(path_out)
    print("saved", path_out)


if __name__ == "__main__":
    aE, labE, CE = analyze(E, "E")
    aN, labN, CN = analyze(N, "N")
