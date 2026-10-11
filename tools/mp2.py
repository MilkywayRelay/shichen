# -*- coding: utf-8 -*-
"""Mana 手部修复 v2：用"手部轮廓"掩膜把 E 的手贴合到 N 上（减少袖口色块移植）。"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASE = r"C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen"
E_PATH = os.path.join(BASE, "assets/char/mana_alt/E_handfix_raw.png")
N_PATH = os.path.join(BASE, "assets/char/mana_alt/N_nofeet.png")
OUT = os.path.join(BASE, "assets/char/_mana_handfix.png")
VIS = os.path.join(BASE, "_shots")

DX, DY = -15, -5
CX, CY, RX, RY, ROT = 340, 640, 108, 122, -18
DILATE, FEATHER = 9, 9
BOX = (215, 470, 500, 790)


def skinish(arr):
    R, G, B = arr[..., 0], arr[..., 1], arr[..., 2]
    m = (R > 168) & ((R - B) > 22) & ((R - G) > 5) & ((R - G) < 80)
    return m


def close_dilate(mask_bool, dilate, close=3):
    im = Image.fromarray((mask_bool * 255).astype(np.uint8))
    if close:
        im = im.filter(ImageFilter.MaxFilter(close + (1 - close % 2))).filter(ImageFilter.MinFilter(close + (1 - close % 2)))
    im = im.filter(ImageFilter.MaxFilter(dilate + (1 - dilate % 2)))
    return np.asarray(im) > 127


def ellipse(cx, cy, rx, ry, rot, feather, size):
    w, h = size
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    m = m.rotate(rot, center=(cx, cy), resample=Image.BICUBIC)
    if feather:
        m = m.filter(ImageFilter.GaussianBlur(feather / 2.0))
    return np.asarray(m).astype(np.float32) / 255.0


def main():
    aE = np.asarray(Image.open(E_PATH).convert("RGB")).astype(np.float32)
    aN = np.asarray(Image.open(N_PATH).convert("RGB")).astype(np.float32)
    h, w = aN.shape[:2]

    Es = np.roll(np.roll(aE, DY, axis=0), DX, axis=1)

    # 手部候选：E 与 N 的肤色 并集，限定在相机椭圆内
    ell = ellipse(CX, CY, RX, RY, ROT, 0, (w, h)) > 0.5
    m_skin = close_dilate(skinish(Es) | skinish(aN), DILATE)
    core = m_skin & ell
    # 粗填洞：对 core 做一次较大的闭运算
    core = close_dilate(core, 0, 13)
    core = core & ell
    mm = Image.fromarray((core * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(FEATHER / 2.0))
    m = (np.asarray(mm).astype(np.float32) / 255.0)[..., None]

    # 色彩匹配
    inner = (m[..., 0] > 0.85)
    for c in range(3):
        e_m, e_s = Es[..., c][inner].mean(), Es[..., c][inner].std() + 1e-3
        n_m, n_s = aN[..., c][inner].mean(), aN[..., c][inner].std() + 1e-3
        Es[..., c] = (Es[..., c] - e_m) / e_s * n_s * 0.96 + n_m

    out = np.clip(aN * (1 - m) + Es * m, 0, 255).astype(np.uint8)
    Image.fromarray(out).save(OUT)

    # 预览：掩膜 + 结果
    vis = out.copy()
    edge = (m[..., 0] > 0.5) & (m[..., 0] < 0.95)
    vis[edge] = [0, 160, 255]
    x0, y0, x1, y1 = BOX
    Image.fromarray(vis[y0:y1, x0:x1]).resize(((x1 - x0) * 3, (y1 - y0) * 3), Image.LANCZOS).save(
        os.path.join(VIS, "_handfix_v2_mask.png"))
    Image.fromarray(out[y0:y1, x0:x1]).resize(((x1 - x0) * 3, (y1 - y0) * 3), Image.LANCZOS).save(
        os.path.join(VIS, "_handfix_v2.png"))
    print("saved", OUT)


if __name__ == "__main__":
    main()
