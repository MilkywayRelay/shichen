# -*- coding: utf-8 -*-
"""Mana 手部修复：把 E_handfix 的清晰手部对齐贴合到现行 N 主体上。

思路
1) 在 E / N 的手部区域各自分割出皮肤（手），形态学清理后取最大连通域
2) 用质心 + 主轴 + 面积比求出把 E 手映射到 N 手的相似变换
3) 按该变换 warp E 手（含羽化 alpha），只保留手部区域
4) 与 N 合成，并对皮肤区域做均值/方差色彩匹配，消除接缝
"""
import os
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from collections import deque

BASE = r"C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen"
E_SRC = os.path.join(BASE, "assets/char/mana_alt/E_handfix_raw.png")
N_SRC = os.path.join(BASE, "assets/char/mana_alt/N_nofeet.png")
OUT = os.path.join(BASE, "assets/char/_mana_handfix.png")
VISDIR = os.path.join(BASE, "_shots")

BOX = (215, 470, 480, 790)   # 手部搜索区

def skin_mask(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    m = (R > 165) & ((R - B) > 20) & ((R - G) > 5) & ((R - G) < 78) & ((G - B) > -6)
    x0, y0, x1, y1 = BOX
    mm = np.zeros_like(m)
    mm[y0:y1, x0:x1] = m[y0:y1, x0:x1]
    im = Image.fromarray((mm * 255).astype(np.uint8))
    im = im.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(5))  # 开运算去噪
    im = im.filter(ImageFilter.MaxFilter(3))
    mm = np.asarray(im) > 127
    # 最大连通域
    h, w = mm.shape
    seen = np.zeros_like(mm); best = None; bn = 0
    for sy in range(y0, y1):
        for sx in range(x0, x1):
            if mm[sy, sx] and not seen[sy, sx]:
                q = deque([(sy, sx)]); seen[sy, sx] = True; px = []
                while q:
                    y, x = q.popleft(); px.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if y0 <= ny < y1 and x0 <= nx < x1 and mm[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True; q.append((ny, nx))
                if len(px) > bn:
                    bn = len(px); best = px
    mask = np.zeros_like(mm)
    for y, x in best:
        mask[y, x] = True
    ys = np.array([p[0] for p in best], float); xs = np.array([p[1] for p in best], float)
    return a, mask, xs, ys

def moments(xs, ys):
    cx, cy = xs.mean(), ys.mean()
    X = xs - cx; Y = ys - cy
    cov = np.array([[np.mean(X * X), np.mean(X * Y)],
                    [np.mean(X * Y), np.mean(Y * Y)]])
    w, v = np.linalg.eigh(cov)
    major = v[:, int(np.argmax(w))]
    ang = np.arctan2(major[1], major[0])
    # 面积 -> 等效半径
    area = len(xs)
    return cx, cy, ang, area

def main():
    aE, mE, xsE, ysE = skin_mask(E_SRC)
    aN, mN, xsN, ysN = skin_mask(N_SRC)
    cxE, cyE, angE, areaE = moments(xsE, ysE)
    cxN, cyN, angN, areaN = moments(xsN, ysN)
    s = float(np.sqrt(areaN / areaE))
    dang = angN - angE
    print("E hand: c=(%.1f,%.1f) ang=%.1fdeg area=%d" % (cxE, cyE, np.degrees(angE), areaE))
    print("N hand: c=(%.1f,%.1f) ang=%.1fdeg area=%d" % (cxN, cyN, np.degrees(angN), areaN))
    print("scale=%.3f  rot=%.1fdeg" % (s, np.degrees(dang)))

    # 可视化两处掩膜
    for tag, a, m in (("E", aE, mE), ("N", aN, mN)):
        v = a.astype(np.uint8).copy()
        v[m] = [255, 0, 0]
        x0, y0, x1, y1 = BOX
        Image.fromarray(v[y0:y1, x0:x1]).resize(((x1 - x0) * 2, (y1 - y0) * 2), Image.NEAREST).save(
            os.path.join(VISDIR, "_mask_%s.png" % tag))

    # ---------- 构造把 E 手 -> N 手的相似变换 ----------
    # 目标：p_N = R(dang) * s * (p_E - c_E) + c_N
    ca, sa = np.cos(dang), np.sin(dang)
    A = s * np.array([[ca, -sa], [sa, ca]])          # 2x2
    t = np.array([cxN, cyN]) - A @ np.array([cxE, cyE])

    # PIL AFFINE: 输出(x,y) <- 输入 (a*x+b*y+c0, d*x+e*y+c1)  逆映射
    # 需要 inv(A): p_E = A^-1 (p_N - t)
    Ai = np.linalg.inv(A)
    ti = -Ai @ t
    # 输出图像尺寸 = 原图尺寸，变换写成 输出->输入
    coeffs = (Ai[0, 0], Ai[0, 1], ti[0], Ai[1, 0], Ai[1, 1], ti[1])

    # warp E 整图（RGB + 掩膜）
    eimg = Image.fromarray(aE.astype(np.uint8))
    wE = eimg.transform(eimg.size, Image.AFFINE, coeffs, resample=Image.BICUBIC, fillcolor=(255, 255, 255))
    wEa = np.asarray(wE).astype(np.float32)

    # warp 掩膜（用最近邻，再羽化）
    mimg = Image.fromarray((mE * 255).astype(np.uint8))
    wM = mimg.transform(mimg.size, Image.AFFINE, coeffs, resample=Image.BILINEAR, fillcolor=0)
    wM = wM.filter(ImageFilter.MaxFilter(9))     # 外扩 ~4px
    wM = wM.filter(ImageFilter.GaussianBlur(2.2))
    wMa = (np.asarray(wM).astype(np.float32) / 255.0)

    # ---------- 色彩匹配：以 N 手部皮肤为基准 ----------
    # 只在掩膜内部、且 N 也是皮肤处统计
    core = (wMa > 0.6)
    skinN = mN
    sel = core & skinN
    if sel.sum() > 200:
        for c in range(3):
            e_mean, e_std = wEa[..., c][sel].mean(), wEa[..., c][sel].std() + 1e-3
            n_mean, n_std = aN[..., c][sel].mean(), aN[..., c][sel].std() + 1e-3
            wEa[..., c] = (wEa[..., c] - e_mean) / e_std * n_std * 0.92 + n_mean
    wEa = np.clip(wEa, 0, 255)

    # ---------- 合成 ----------
    out = aN.copy()
    al = wMa[..., None]
    out = out * (1 - al) + wEa * al
    out = np.clip(out, 0, 255).astype(np.uint8)
    Image.fromarray(out).save(OUT)
    print("saved", OUT)

    x0, y0, x1, y1 = BOX
    Image.fromarray(out[y0:y1, x0:x1]).resize(((x1 - x0) * 2, (y1 - y0) * 2), Image.LANCZOS).save(
        os.path.join(VISDIR, "_handfix_result.png"))

if __name__ == "__main__":
    main()
